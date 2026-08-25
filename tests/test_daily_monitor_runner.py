import json
import tempfile
import unittest
from dataclasses import replace
from datetime import date
from pathlib import Path

from tools.daily_monitoring.deepseek import DeepSeekAnalysis
from tools.daily_monitoring.documents import ExtractedDocument
from tools.daily_monitoring.models import Disclosure, FallbackClue, VerifiedFact
from tools.daily_monitoring.http import SourceError
from tools.daily_monitoring.runner import (
    MonitorOptions,
    MonitorServices,
    _watched,
    run_monitor,
)
from tools.daily_monitoring.state import empty_state


OFFICIAL_URL = (
    "https://www.sec.gov/Archives/edgar/data/1/000000000126000001/report.htm"
)


def write_triggers(root, *, with_zone=False):
    target = {
        "id": "样例公司",
        "name": "Example Co",
        "group": "重点",
        "codes": {"US": "usEXM"},
        "zones": [],
        "events": [],
        "disclosure_sources": {"sec": {"cik": "1"}},
    }
    if with_zone:
        target["zones"] = [
            {
                "label": "复核区",
                "dir": "below",
                "high": 100,
                "low": None,
                "market": "US",
            }
        ]
    path = root / "data" / "triggers.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"schema": 1, "targets": [target]}), encoding="utf-8")
    return path


def disclosure():
    return Disclosure(
        target_id="样例公司",
        source="sec",
        document_id="0000000001-26-000001",
        title="Quarterly results",
        published_at="2026-08-25T16:00:00-04:00",
        document_type="10-Q",
        official_url=OFFICIAL_URL,
        download_url=OFFICIAL_URL,
    )


class FakeAI:
    def __init__(self, result):
        self.result = result
        self.calls = 0

    def analyze(self, request):
        self.calls += 1
        return self.result


def ai_result(*, degraded=False):
    return DeepSeekAnalysis(
        status="DEGRADED" if degraded else "OK",
        priority="P0",
        why_now="新财报需要核验现金流假设。",
        verified_facts=() if degraded else (
            VerifiedFact("经营现金流发生变化。", OFFICIAL_URL, None, "high"),
        ),
        thesis_impacts=() if degraded else ("复核现金流假设。",),
        next_workflow=None if degraded else "/earnings-review",
        needs_human_review=degraded,
        limitations=("模型超时",) if degraded else (),
        needs_retry=degraded,
    )


def services(
    ai, *, collector=None, extraction_status="EXTRACTED", quote_price=90.0
):
    def default_collector(target_id, config, *, since, until, http):
        return [disclosure()]

    def extractor(document, target, http):
        return ExtractedDocument(
            status=extraction_status,
            sha256="a" * 64,
            pages_used=(),
            chunks=("UNTRUSTED DATA: cash flow changed.",) if extraction_status == "EXTRACTED" else (),
            limitation="需要 OCR" if extraction_status == "OCR_REQUIRED" else None,
        )

    return MonitorServices(
        quote_provider=lambda codes: {code: {"price": quote_price} for code in codes},
        collectors={"sec": collector or default_collector},
        http=object(),
        document_extractor=extractor,
        deepseek=ai,
    )


def options(root, triggers):
    return MonitorOptions(
        root=root,
        triggers_file=triggers,
        state_file=root / "runtime" / "state.json",
        report_dir=root / "runtime" / "reports",
        today=date(2026, 8, 25),
    )


class DailyMonitorRunnerTest(unittest.TestCase):
    def test_watch_matches_exact_identity_not_substring(self):
        target = {
            "id": "腾讯音乐",
            "name": "Tencent Music Entertainment",
            "codes": {"US": "usTME"},
        }

        self.assertFalse(_watched(target, ("腾讯",)))
        self.assertTrue(_watched(target, ("腾讯音乐",)))
        self.assertTrue(_watched(target, ("usTME",)))

    def test_watch_mode_excludes_unrelated_global_gaps(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            triggers = write_triggers(root)
            reports = root / "reports"
            reports.mkdir()
            (reports / "标的跟踪表.md").write_text(
                "| ID | 标的 | 复检日 | 状态 |\n"
                "| --- | --- | --- | --- |\n"
                "| unrelated | 无关公司 | 2026-01-01 | 待触发 |\n",
                encoding="utf-8",
            )
            run_options = replace(options(root, triggers), watch=("样例公司",))

            result = run_monitor(
                run_options,
                services(FakeAI(ai_result()), collector=lambda *args, **kwargs: []),
            )

            self.assertFalse(any(item.target_id == "unrelated" for item in result.items))

    def test_watch_mode_preserves_unrelated_gap_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            triggers = write_triggers(root)
            run_options = replace(options(root, triggers), watch=("样例公司",))
            state = empty_state()
            state["completeness"]["unrelated-gap"] = {
                "target_id": "unrelated",
                "name": "无关公司",
                "title": "旧缺口",
                "priority": "P0",
                "updated_at": "2026-08-24",
            }
            run_options.state_file.parent.mkdir(parents=True)
            run_options.state_file.write_text(
                json.dumps(state, ensure_ascii=False), encoding="utf-8"
            )

            result = run_monitor(
                run_options,
                services(FakeAI(ai_result()), collector=lambda *args, **kwargs: []),
            )

            self.assertIn("unrelated-gap", result.next_state["completeness"])
            self.assertFalse(any(item.target_id == "unrelated" for item in result.items))

    def test_ai_failure_writes_report_and_keeps_document_pending(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            triggers = write_triggers(root)
            ai = FakeAI(ai_result(degraded=True))

            result = run_monitor(options(root, triggers), services(ai))

            key = "sec:0000000001-26-000001"
            self.assertEqual(result.status, "DEGRADED")
            self.assertTrue(result.report_paths.latest.exists())
            self.assertEqual(result.next_state["documents"][key]["status"], "PENDING_AI")
            self.assertEqual(ai.calls, 1)

    def test_identical_second_run_does_not_call_ai_or_notify(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            triggers = write_triggers(root)
            first_ai = FakeAI(ai_result())
            first = run_monitor(options(root, triggers), services(first_ai))
            second_ai = FakeAI(ai_result())

            second = run_monitor(options(root, triggers), services(second_ai))

            self.assertEqual(first.next_state["documents"]["sec:0000000001-26-000001"]["status"], "DONE")
            self.assertEqual(second_ai.calls, 0)
            self.assertEqual(second.notification_items, ())

    def test_first_price_observation_uses_current_priority_without_notification(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            triggers = write_triggers(root, with_zone=True)

            result = run_monitor(options(root, triggers), services(FakeAI(ai_result())))

            price = next(row for row in result.items if row.section == "price")
            self.assertEqual(price.priority, "P0")
            self.assertFalse(price.notify)

    def test_price_within_five_percent_of_boundary_is_p1(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            triggers = write_triggers(root, with_zone=True)

            result = run_monitor(
                options(root, triggers),
                services(FakeAI(ai_result()), quote_price=104.0),
            )

            price = next(row for row in result.items if row.section == "price")
            self.assertEqual((price.priority, price.status), ("P1", "NEAR"))
            self.assertFalse(price.notify)

    def test_source_failure_does_not_advance_cursor_and_still_writes_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            triggers = write_triggers(root)

            def failing_collector(*args, **kwargs):
                raise RuntimeError("internal details")

            result = run_monitor(
                options(root, triggers),
                services(FakeAI(ai_result()), collector=failing_collector),
            )

            self.assertEqual(result.status, "DEGRADED")
            self.assertNotIn("cursor", result.next_state["sources"]["sec"])
            self.assertTrue(result.report_paths.latest.exists())
            self.assertTrue(any(row.source == "sec" and row.status == "FAILED" for row in result.source_health))

    def test_ocr_document_is_not_sent_to_ai(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            triggers = write_triggers(root)
            ai = FakeAI(ai_result())

            result = run_monitor(
                options(root, triggers), services(ai, extraction_status="OCR_REQUIRED")
            )

            record = result.next_state["documents"]["sec:0000000001-26-000001"]
            self.assertEqual(record["status"], "OCR_REQUIRED")
            self.assertEqual(ai.calls, 0)
            disclosure_item = next(row for row in result.items if row.section == "disclosures")
            self.assertTrue(disclosure_item.needs_human_review)

    def test_extraction_source_error_keeps_safe_failure_reason(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            triggers = write_triggers(root)
            runtime_services = services(FakeAI(ai_result()))

            def failing_extractor(*args, **kwargs):
                raise SourceError(
                    "sec", "连接中断或响应不完整", retryable=True
                )

            runtime_services.document_extractor = failing_extractor

            result = run_monitor(options(root, triggers), runtime_services)

            disclosure_item = next(
                row for row in result.items if row.section == "disclosures"
            )
            self.assertEqual(
                disclosure_item.limitations,
                ("正文提取失败（连接中断或响应不完整）",),
            )

    def test_cninfo_failure_uses_akshare_only_as_unverified_clue(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            triggers = root / "data" / "triggers.json"
            triggers.parent.mkdir(parents=True)
            triggers.write_text(
                json.dumps(
                    {
                        "schema": 1,
                        "targets": [
                            {
                                "id": "样例A股",
                                "name": "样例A股",
                                "group": "重点",
                                "codes": {"A": "sh600000"},
                                "zones": [],
                                "events": [],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            def failing_collector(*args, **kwargs):
                raise RuntimeError("cninfo unavailable")

            fallback_calls = []

            def fallback(target_id, config, *, since, until):
                fallback_calls.append(target_id)
                return [
                    FallbackClue(
                        target_id=target_id,
                        source="akshare",
                        title="疑似业绩公告",
                        published_at="2026-08-25",
                        url="https://example.com/unverified",
                        verified=False,
                        needs_human_review=True,
                    )
                ]

            runtime_services = MonitorServices(
                quote_provider=lambda codes: {},
                collectors={"cninfo": failing_collector},
                http=object(),
                document_extractor=lambda *args: None,
                deepseek=FakeAI(ai_result()),
                fallback_provider=fallback,
            )

            result = run_monitor(options(root, triggers), runtime_services)

            clue = next(row for row in result.items if row.metadata.get("fallback"))
            self.assertEqual(fallback_calls, ["样例A股"])
            self.assertEqual(clue.section, "disclosures")
            self.assertEqual(clue.verified_facts, ())
            self.assertEqual(clue.source_urls, ())
            self.assertTrue(clue.needs_human_review)


if __name__ == "__main__":
    unittest.main()

import json
import tempfile
import unittest
from dataclasses import replace
from datetime import date
from pathlib import Path

from tools.daily_monitoring.models import MonitorItem, RunResult, SourceHealth
from tools.daily_monitoring.report import render_markdown, report_payload, write_reports


def item(
    fingerprint,
    section,
    priority,
    *,
    target_id="腾讯",
    name="腾讯控股",
    title="监控事项",
    workflow=None,
    notify=False,
    resolved=False,
    status="NEW",
    metadata=None,
    verified_facts=(),
    source_urls=None,
    limitations=(),
    needs_human_review=False,
):
    return MonitorItem(
        fingerprint=fingerprint,
        section=section,
        priority=priority,
        target_id=target_id,
        name=name,
        title=title,
        why_now="出现了需要研究核验的增量，不构成买卖结论。",
        status=status,
        verified_facts=verified_facts,
        source_urls=source_urls if source_urls is not None else ((
            "https://www1.hkexnews.hk/listedco/listconews/sehk/2026/example.pdf",
        ) if section == "disclosures" else ()),
        next_workflow=workflow,
        limitations=limitations,
        needs_human_review=needs_human_review,
        notify=notify,
        resolved=resolved,
        metadata=metadata or {},
    )


def result(items):
    items = tuple(items)
    return RunResult(
        status="OK",
        items=items,
        notification_items=tuple(row for row in items if row.notify),
        source_health=(SourceHealth("quotes", "OK"),),
        next_state={"schema": 1},
        report_paths=None,
    )


class DailyMonitorReportTest(unittest.TestCase):
    def test_legacy_snapshot_excludes_retired_items_health_and_degradation(self):
        run = replace(
            result([
                item("price", "price", "P0", notify=True),
                item("disclosure", "disclosures", "P0", notify=True, title="旧公告"),
                item("event", "other", "P1", notify=True, title="旧事件"),
            ]),
            status="DEGRADED",
            source_health=(SourceHealth("quotes", "OK"), SourceHealth("sec", "FAILED")),
        )

        markdown = render_markdown(run, run_date=date(2026, 11, 19))
        payload = report_payload(run, run_date=date(2026, 11, 19))

        self.assertEqual([row for row in markdown.splitlines() if row.startswith("## ")], ["## 一、价格监控"])
        self.assertNotIn("旧公告", markdown)
        self.assertNotIn("旧事件", markdown)
        self.assertEqual(payload["status"], "OK")
        self.assertEqual(payload["notification_items"], ["price"])
        self.assertEqual([row["source"] for row in payload["source_health"]], ["quotes"])
        self.assertEqual([row["fingerprint"] for row in payload["items"]], ["price"])

    def test_price_section_renders_all_items_as_one_table(self):
        markdown = render_markdown(
            result(
                [
                    item(
                        "p0",
                        "price",
                        "P0",
                        title="加仓带：TRIGGERED",
                        status="TRIGGERED",
                        metadata={
                            "market": "H",
                            "zone_label": "加仓带",
                            "low": 400,
                            "high": 430,
                            "direction": "range",
                            "price": 410,
                        },
                    ),
                    item(
                        "p1",
                        "price",
                        "P1",
                        target_id="样例公司",
                        name="Example Co",
                        title="复核线：NEAR",
                        status="NEAR",
                        metadata={
                            "market": "US",
                            "zone_label": "复核线",
                            "low": None,
                            "high": 100,
                            "direction": "below",
                            "price": 104,
                        },
                    ),
                    item(
                        "p2",
                        "price",
                        "P2",
                        target_id="远端样例",
                        name="Far Away Co",
                        title="等待带：FAR",
                        status="FAR",
                        metadata={
                            "market": "US",
                            "zone_label": "等待带",
                            "low": 80,
                            "high": 100,
                            "direction": "range",
                            "price": 120,
                        },
                    ),
                ]
            ),
            run_date=date(2026, 8, 25),
        )

        self.assertIn(
            "| 优先级 | 标的 | 最新研究报告日期 | 市场 | 监控区间 | 条件 | 现价 | 距边界 | 状态 |",
            markdown,
        )
        self.assertIn(
            "P0=到达建仓或研究复核条件；P1=距对应边界≤5%；P2 与上涨警戒线事项不展示",
            markdown,
        )
        self.assertNotIn("above", markdown)
        self.assertIn(
            "| P0 | 腾讯控股 | - | H | 加仓带 | [400.00, 430.00] | 410.00 | 区间内 | TRIGGERED |",
            markdown,
        )
        self.assertIn(
            "| P1 | Example Co | - | US | 复核线 | ≤ 100.00 | 104.00 | 4.0% | NEAR |",
            markdown,
        )
        self.assertNotIn("### [P0] 腾讯控股", markdown)
        self.assertNotIn("Far Away Co", markdown)

    def test_price_section_shows_linked_report_date_and_missing_date(self):
        markdown = render_markdown(
            result(
                [
                    item(
                        "dated",
                        "price",
                        "P0",
                        metadata={
                            "research_link": "../公司/研究.md",
                            "research_date": "2026-08-31",
                        },
                    ),
                    item("undated", "price", "P1", target_id="其他", name="其他公司"),
                ]
            ),
            run_date=date(2026, 9, 1),
        )

        self.assertIn("| 优先级 | 标的 | 最新研究报告日期 | 市场 |", markdown)
        self.assertIn("| P0 | [腾讯控股](../公司/研究.md) | 2026-08-31 |", markdown)
        self.assertIn("| P1 | 其他公司 | - |", markdown)

    def test_above_warning_is_hidden_from_price_section_and_summary(self):
        markdown = render_markdown(
            result(
                [
                    item(
                        "warning",
                        "price",
                        "P0",
                        target_id="沃尔玛",
                        name="Walmart",
                        title="估值警戒线：WARN",
                        status="WARN",
                        notify=True,
                        metadata={
                            "market": "US",
                            "zone_label": "估值警戒线",
                            "low": 120,
                            "high": None,
                            "direction": "above",
                            "price": 122,
                        },
                    )
                ]
            ),
            run_date=date(2026, 8, 27),
        )

        self.assertNotIn("Walmart", markdown)
        self.assertNotIn("| WARN |", markdown)
        self.assertIn("P0 0 · P1 0 · 新增价格 0", markdown)
        self.assertIn("无 P0/P1 建仓或关注价格事项", markdown)

    def test_above_near_is_absent_from_markdown_summary_and_json(self):
        run = result(
            [
                item(
                    "warning-near",
                    "price",
                    "P1",
                    target_id="Credo",
                    name="Credo Technology",
                    title="估值警戒线：NEAR",
                    status="NEAR",
                    notify=True,
                    metadata={
                        "market": "US",
                        "zone_label": "估值警戒线",
                        "low": 220,
                        "direction": "above",
                        "price": 210.97,
                    },
                )
            ]
        )

        markdown = render_markdown(run, run_date=date(2026, 9, 28))
        payload = report_payload(run, run_date=date(2026, 9, 28))

        self.assertNotIn("Credo Technology", markdown)
        self.assertIn("P0 0 · P1 0 · 新增价格 0", markdown)
        self.assertEqual(payload["items"], [])
        self.assertEqual(payload["notification_items"], [])


    def test_writes_dated_latest_and_machine_json_atomically(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = write_reports(
                result([item("p", "price", "P0")]),
                Path(tmp),
                run_date=date(2026, 8, 25),
            )

            self.assertEqual(paths.dated.name, "daily-monitor-20260825.md")
            self.assertEqual(paths.dated.read_text(), paths.latest.read_text())
            payload = json.loads(paths.latest_json.read_text(encoding="utf-8"))
            self.assertEqual(payload["date"], "2026-08-25")
            self.assertEqual(payload["items"][0]["section"], "price")
            self.assertFalse(list(Path(tmp).glob("*.tmp")))


if __name__ == "__main__":
    unittest.main()

import json
import tempfile
import unittest
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from tools.daily_monitoring.config import load_targets
from tools.daily_monitoring.runner import MonitorOptions, MonitorServices, _watched, production_services, run_monitor
from tools.daily_monitoring.state import empty_state
from tools.daily_monitoring.transitions import price_state_key


REPO = Path(__file__).resolve().parents[1]
LIVE_TRIGGERS = REPO / "data" / "triggers.json"
BACKFILLED_LEDGER_TARGET_IDS = (
    "澜起科技",
    "云迹科技",
    "Adobe",
    "Booking",
    "MINIMAX",
    "Progressive",
    "Uber",
    "思格新能",
    "深科技",
    "群核科技",
)
BACKFILLED_LEDGER_CODES = {
    "sh688008",
    "hk06809",
    "hk02670",
    "usADBE",
    "usBKNG",
    "hk00100",
    "usPGR",
    "usUBER",
    "hk06656",
    "sz000021",
    "hk00068",
}


def write_triggers(root, *, with_zone=False, links=()):
    target = {
        "id": "样例公司",
        "name": "Example Co",
        "group": "重点",
        "codes": {"US": "usEXM"},
        "zones": [],
        "events": [{"label": "旧财报节点", "type": "财报", "date": "2026-08-25"}],
        "links": list(links),
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


def options(root, triggers):
    return MonitorOptions(
        root=root,
        triggers_file=triggers,
        state_file=root / "runtime" / "state.json",
        report_dir=root / "runtime" / "reports",
        today=date(2026, 8, 25),
    )


def services(*, quote_price=90.0):
    return MonitorServices(
        quote_provider=lambda codes: {code: {"price": quote_price} for code in codes}
    )


class DailyMonitorRunnerTest(unittest.TestCase):
    def test_target_without_price_zones_is_displayed_unrated_without_price_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = options(root, write_triggers(root))

            run = run_monitor(config, services(quote_price=123))

            price = next(row for row in run.items if row.section == "price")
            self.assertEqual((price.priority, price.status), ("-", "NO_ZONE"))
            self.assertEqual(price.metadata["price"], 123)
            self.assertEqual(run.next_state["price_states"], {})
            self.assertFalse(run.notification_items)
            self.assertIn("未登记价格区间", run.report_paths.latest.read_text())

    def test_all_registered_targets_appear_in_report_including_unrated_and_p2(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run = run_monitor(MonitorOptions(
                root=REPO, triggers_file=LIVE_TRIGGERS,
                state_file=root / "state.json", report_dir=root / "reports",
                today=date(2026, 11, 24),
            ), services(quote_price=100_000))
            payload = json.loads(run.report_paths.latest_json.read_text())

            self.assertEqual({row["target_id"] for row in payload["items"]},
                             {target["id"] for target in load_targets(LIVE_TRIGGERS)})
            self.assertIn("| P2 |", run.report_paths.latest.read_text())
            self.assertIn("| - |", run.report_paths.latest.read_text())

    def test_missing_quote_for_unrated_target_marks_source_degraded(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run = run_monitor(options(root, write_triggers(root)),
                              MonitorServices(quote_provider=lambda codes: {}))

            self.assertEqual(run.status, "DEGRADED")
            price = next(row for row in run.items if row.section == "price")
            self.assertEqual(price.status, "NO_ZONE")
            self.assertIsNone(price.metadata["price"])

    def test_production_curl_failure_marks_quotes_degraded(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = options(root, write_triggers(root, with_zone=True))
            failed_curl = SimpleNamespace(returncode=7, stdout=b"", stderr=b"connection failed")
            with patch("tools.trigger_scanner.subprocess.run", return_value=failed_curl):
                run = run_monitor(config, production_services())

            self.assertEqual(run.status, "DEGRADED")
            self.assertEqual(run.source_health[0].status, "FAILED")
            self.assertEqual(run.next_state["services"]["quotes"]["status"], "FAILED")
            payload = json.loads(run.report_paths.latest_json.read_text())
            self.assertEqual(payload["status"], "DEGRADED")

    def test_partial_quote_failure_keeps_valid_prices_and_recovers_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            triggers = write_triggers(root, with_zone=True)
            payload = json.loads(triggers.read_text())
            other = json.loads(json.dumps(payload["targets"][0]))
            other.update(id="另一公司", name="Other Co", codes={"US": "usOTHER"})
            payload["targets"].append(other)
            triggers.write_text(json.dumps(payload))
            config = options(root, triggers)
            partial = MonitorServices(quote_provider=lambda codes: {"usEXM": {"price": 90}})

            first = run_monitor(config, partial)
            repeated = run_monitor(config, partial)
            recovered = run_monitor(config, services())
            stable = run_monitor(config, services())

            self.assertEqual(first.status, "DEGRADED")
            prices = {item.target_id: item for item in first.items if item.section == "price"}
            self.assertEqual(prices["样例公司"].metadata["price"], 90)
            self.assertEqual(prices["样例公司"].status, "TRIGGERED")
            self.assertEqual(prices["另一公司"].status, "NO_DATA")
            self.assertFalse(repeated.notification_items)
            self.assertEqual(recovered.status, "OK")
            self.assertTrue(any(item.status == "RECOVERED" for item in recovered.notification_items))
            self.assertFalse(stable.notification_items)

    def test_invalid_quote_prices_are_no_data(self):
        for invalid in (None, float("nan"), float("inf"), -1, 0, True, "90"):
            with self.subTest(price=invalid), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                config = options(root, write_triggers(root, with_zone=True))
                run = run_monitor(config, services(quote_price=invalid))
                self.assertEqual(run.status, "DEGRADED")
                prices = [item for item in run.items if item.section == "price"]
                self.assertEqual(prices[0].status, "NO_DATA")
                self.assertIsNone(prices[0].metadata["price"])

    def test_script_refreshes_latest_prices_and_suppresses_unchanged_notifications(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = options(root, write_triggers(root, with_zone=True))
            run_monitor(config, services(quote_price=120))
            changed = run_monitor(config, services(quote_price=90))
            repeated = run_monitor(config, services(quote_price=90))

            self.assertEqual(len(changed.notification_items), 1)
            self.assertEqual(repeated.notification_items, ())
            payload = json.loads(repeated.report_paths.latest_json.read_text())
            self.assertEqual(payload["items"][0]["metadata"]["price"], 90)
            self.assertIn("90.00", repeated.report_paths.latest.read_text())

    def test_quote_failure_and_recovery_preserve_report_and_notify_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = options(root, write_triggers(root, with_zone=True))

            def fail_quotes(codes):
                raise RuntimeError("example credential must not appear in the report")

            failed = run_monitor(config, MonitorServices(quote_provider=fail_quotes))
            first_payload = json.loads(failed.report_paths.latest_json.read_text())
            repeated = run_monitor(config, MonitorServices(quote_provider=fail_quotes))
            recovered = run_monitor(config, services())

            self.assertEqual(first_payload["status"], "DEGRADED")
            self.assertNotIn("example credential", json.dumps(first_payload))
            self.assertTrue(failed.notification_items)
            self.assertFalse(repeated.notification_items)
            self.assertEqual(recovered.status, "OK")
            self.assertTrue(any(item.status == "RECOVERED" for item in recovered.notification_items))

    def test_price_refresh_preserves_research_state_and_skips_research_services(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = options(root, write_triggers(root, with_zone=True))
            state = empty_state()
            state['event_states'] = {'event': {'status': 'UPCOMING_7D'}}
            state['sources'] = {'sec': {'cursor': '2026-08-24'}}
            state['documents'] = {'pending': {'target_id': '样例公司', 'status': 'PENDING_AI'}}
            state['completeness'] = {'gap': {'target_id': '样例公司'}}
            state['services']['akshare_clues'] = {'old': {}}
            config.state_file.parent.mkdir(parents=True)
            config.state_file.write_text(json.dumps(state), encoding='utf-8')
            deps = services()
            with patch('urllib.request.urlopen', side_effect=AssertionError('不应访问公告或 AI')):
                run = run_monitor(config, deps)
            for key in ('event_states', 'sources', 'documents', 'completeness'):
                self.assertEqual(run.next_state[key], state[key])
            self.assertEqual(run.next_state['services']['akshare_clues'], {'old': {}})
            self.assertEqual({row.source for row in run.source_health}, {'quotes'})
            self.assertTrue(all((item.section == 'price' for item in run.items)))
            markdown = run.report_paths.latest.read_text()
            self.assertNotIn('财报与正式披露监控', markdown)
            self.assertNotIn('其他监控', markdown)

    def test_above_zone_is_excluded_from_daily_monitor_and_price_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            triggers = write_triggers(root, with_zone=True)
            config = json.loads(triggers.read_text(encoding="utf-8"))
            target = config["targets"][0]
            warning = {
                "label": "估值警戒线",
                "dir": "above",
                "low": 110,
                "market": "US",
            }
            target["zones"].append(warning)
            triggers.write_text(json.dumps(config, ensure_ascii=False), encoding="utf-8")

            result = run_monitor(
                options(root, triggers),
                services(
                    quote_price=105,
                ),
            )

            price_items = [item for item in result.items if item.section == "price"]
            self.assertEqual([item.metadata["direction"] for item in price_items], ["below"])
            self.assertNotIn(
                "估值警戒线", result.report_paths.latest.read_text(encoding="utf-8")
            )
            payload = json.loads(result.report_paths.latest_json.read_text(encoding="utf-8"))
            self.assertFalse(
                any(
                    item["section"] == "price"
                    and item["metadata"]["direction"] == "above"
                    for item in payload["items"]
                )
            )
            self.assertNotIn(price_state_key(target, warning), result.next_state["price_states"])

    def test_report_links_target_to_most_current_existing_research(self):
        """Selecting the first configured report instead of the newest is a bug."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            company_reports = root / "reports" / "样例公司"
            company_reports.mkdir(parents=True)
            (company_reports / "旧报告.md").write_text(
                "# 旧报告\n\n**数据截止日**：2026-07-31\n",
                encoding="utf-8",
            )
            (company_reports / "最新报告.md").write_text(
                "# 最新报告\n\n**研究日期 / 数据截止日**：2026-08-25 09:00 CST\n",
                encoding="utf-8",
            )
            (company_reports / "补充报告-20260820.md").write_text(
                "# 补充报告\n",
                encoding="utf-8",
            )
            triggers = write_triggers(
                root,
                with_zone=True,
                links=(
                    "reports/样例公司/旧报告.md",
                    "reports/样例公司/最新报告.md",
                    "reports/样例公司/补充报告-20260820.md",
                    "reports/样例公司/不存在.md",
                ),
            )

            result = run_monitor(
                options(root, triggers),
                services(
                ),
            )

            markdown = result.report_paths.latest.read_text(encoding="utf-8")
            self.assertIn(
                "[Example Co](../../reports/%E6%A0%B7%E4%BE%8B%E5%85%AC%E5%8F%B8/"
                "%E6%9C%80%E6%96%B0%E6%8A%A5%E5%91%8A.md)",
                markdown,
            )
            self.assertNotIn(
                "[Example Co](../../reports/%E6%A0%B7%E4%BE%8B%E5%85%AC%E5%8F%B8/"
                "%E6%97%A7%E6%8A%A5%E5%91%8A.md)",
                markdown,
            )
            self.assertIn(
                "%E6%9C%80%E6%96%B0%E6%8A%A5%E5%91%8A.md) | 2026-08-25 | US |",
                markdown,
            )
            payload = json.loads(result.report_paths.latest_json.read_text(encoding="utf-8"))
            price = next(row for row in payload["items"] if row["section"] == "price")
            self.assertEqual(price["metadata"]["research_date"], "2026-08-25")

    def test_watch_scans_every_backfilled_ledger_target_code(self):
        """Deleting a backfilled target must remove at least one watched quote."""
        captured_codes = []

        def quote_provider(codes):
            captured_codes.extend(codes)
            return {code: {"price": 1_000.0} for code in codes}

        services = MonitorServices(
            quote_provider=quote_provider,
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = run_monitor(
                MonitorOptions(
                    root=REPO,
                    triggers_file=LIVE_TRIGGERS,
                    state_file=root / "state.json",
                    report_dir=root / "reports",
                    today=date(2026, 8, 30),
                    watch=BACKFILLED_LEDGER_TARGET_IDS,
                ),
                services,
            )

        self.assertEqual(set(captured_codes), BACKFILLED_LEDGER_CODES)
        self.assertEqual(
            {target["id"] for target in load_targets(LIVE_TRIGGERS)}
            & set(BACKFILLED_LEDGER_TARGET_IDS),
            set(BACKFILLED_LEDGER_TARGET_IDS),
        )
        self.assertEqual(result.status, "OK")

    def test_watch_matches_exact_identity_not_substring(self):
        target = {
            "id": "腾讯音乐",
            "name": "Tencent Music Entertainment",
            "codes": {"US": "usTME"},
        }

        self.assertFalse(_watched(target, ("腾讯",)))
        self.assertTrue(_watched(target, ("腾讯音乐",)))
        self.assertTrue(_watched(target, ("usTME",)))

    def test_first_price_observation_uses_current_priority_without_notification(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            triggers = write_triggers(root, with_zone=True)

            result = run_monitor(options(root, triggers), services())

            price = next(row for row in result.items if row.section == "price")
            self.assertEqual(price.priority, "P0")
            self.assertFalse(price.notify)

    def test_price_within_five_percent_of_boundary_is_p1(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            triggers = write_triggers(root, with_zone=True)

            result = run_monitor(
                options(root, triggers),
                services(quote_price=104.0),
            )

            price = next(row for row in result.items if row.section == "price")
            self.assertEqual((price.priority, price.status), ("P1", "NEAR"))
            self.assertFalse(price.notify)


if __name__ == "__main__":
    unittest.main()

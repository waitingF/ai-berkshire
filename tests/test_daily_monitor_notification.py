import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

import yaml


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / ".github" / "scripts" / "notify_daily_monitor.py"


def load_module():
    spec = importlib.util.spec_from_file_location("notify_daily_monitor", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def monitor_payload():
    return {
        "date": "2026-08-25",
        "status": "OK",
        "items": [
            {
                "priority": "P0",
                "name": "腾讯控股",
                "title": "新财报",
                "why_now": "需要复核",
                "notify": True,
                "resolved": False,
                "status": "DONE",
            },
            {
                "priority": "P2",
                "name": "微软",
                "title": "持续状态",
                "why_now": "无变化",
                "notify": False,
                "resolved": False,
                "status": "TRIGGERED",
            },
            {
                "priority": "P2",
                "name": "美团",
                "title": "条件解除",
                "why_now": "已离开条件",
                "notify": True,
                "resolved": True,
                "status": "RESOLVED",
            },
        ],
    }


class NotificationContractTest(unittest.TestCase):
    def test_message_contains_only_notifiable_state_changes(self):
        module = load_module()

        title, message = module.build_message(monitor_payload())

        self.assertIn("新增 P0：1", message)
        self.assertIn("已解除：1", message)
        self.assertIn("腾讯控股", message)
        self.assertNotIn("持续状态", message)
        self.assertLessEqual(len(title), 32)

    def test_missing_sendkey_skips_without_failure(self):
        module = load_module()

        self.assertEqual(module.send_notification(monitor_payload(), sendkey=""), "SKIPPED")

    def test_no_changes_skips_even_with_key(self):
        module = load_module()
        payload = monitor_payload()
        for item in payload["items"]:
            item["notify"] = False

        self.assertEqual(module.send_notification(payload, sendkey="secret"), "SKIPPED")

    def test_message_aggregates_todays_changes_for_same_target_and_market(self):
        module = load_module()
        payload = {
            "date": "2026-08-26",
            "status": "OK",
            "items": [
                {
                    "target_id": "样例公司",
                    "name": "样例公司",
                    "priority": "P0",
                    "section": "disclosures",
                    "title": "INTERIM RESULTS FOR THE SIX MONTHS ENDED 30 JUNE 2026",
                    "why_now": "较早事项",
                    "notify": True,
                    "resolved": False,
                    "status": "DONE",
                    "source_urls": ["https://www1.hkexnews.hk/results.pdf"],
                    "metadata": {
                        "kind": "official_disclosure",
                        "market": "H",
                        "published_at": "2026-08-26T18:25:00+08:00",
                    },
                },
                {
                    "target_id": "样例公司",
                    "name": "样例公司",
                    "priority": "P1",
                    "section": "disclosures",
                    "title": "H SHARE FULL CIRCULATION BY THE COMPANY",
                    "why_now": "最新事项",
                    "notify": True,
                    "resolved": False,
                    "status": "DONE",
                    "source_urls": ["https://www1.hkexnews.hk/circulation.pdf"],
                    "metadata": {
                        "kind": "official_disclosure",
                        "market": "H",
                        "published_at": "2026-08-26T19:32:00+08:00",
                    },
                },
            ],
        }

        _, message = module.build_message(payload)

        self.assertIn("[2026年中期业绩](https://www1.hkexnews.hk/results.pdf)", message)
        self.assertIn("[H股全流通申请](https://www1.hkexnews.hk/circulation.pdf)", message)
        self.assertIn("| 样例公司 | H |", message)
        self.assertIn("| 2 | 19:32 | DONE |", message)
        self.assertIn("新增 P0：1｜新增 P1：0", message)

    def test_legacy_disclosures_ignore_placeholder_when_substantive_update_exists(self):
        module = load_module()
        payload = {
            "date": "2026-08-26",
            "status": "OK",
            "items": [
                {
                    "target_id": "样例公司",
                    "name": "样例公司",
                    "priority": "P0",
                    "section": "disclosures",
                    "title": "INTERIM RESULTS FOR THE SIX MONTHS ENDED 30 JUNE 2026",
                    "why_now": "较早事项",
                    "notify": True,
                    "resolved": False,
                    "source_urls": ["https://www1.hkexnews.hk/older.pdf"],
                    "metadata": {"published_at": "26/08/2026 18:25"},
                },
                {
                    "target_id": "样例公司",
                    "name": "样例公司",
                    "priority": "P1",
                    "section": "disclosures",
                    "title": (
                        "An announcement has just been published by the issuer in "
                        "the Chinese section of this website"
                    ),
                    "why_now": "最新事项",
                    "notify": True,
                    "resolved": False,
                    "source_urls": ["https://www1.hkexnews.hk/latest.pdf"],
                    "metadata": {"published_at": "26/08/2026 19:32"},
                },
            ],
        }

        _, message = module.build_message(payload)

        self.assertIn("[2026年中期业绩](https://www1.hkexnews.hk/older.pdf)", message)
        self.assertNotIn("An announcement has just been published", message)
        self.assertIn("| 1 | 18:25 | REVIEW |", message)

    def test_message_excludes_disclosures_not_published_today_in_shanghai(self):
        module = load_module()
        payload = {
            "date": "2026-08-26",
            "status": "OK",
            "items": [
                {
                    "target_id": "样例公司",
                    "name": "样例公司",
                    "section": "disclosures",
                    "priority": "P0",
                    "title": "Yesterday update",
                    "why_now": "旧公告",
                    "notify": True,
                    "resolved": False,
                    "status": "DONE",
                    "source_urls": ["https://www.sec.gov/yesterday.htm"],
                    "metadata": {
                        "kind": "official_disclosure",
                        "market": "US",
                        "published_at": "2026-08-25T23:59:00+08:00",
                    },
                },
                {
                    "target_id": "样例公司",
                    "name": "样例公司",
                    "section": "disclosures",
                    "priority": "P1",
                    "title": "Today update",
                    "why_now": "今日公告",
                    "notify": True,
                    "resolved": False,
                    "status": "DONE",
                    "source_urls": ["https://www.sec.gov/today.htm"],
                    "metadata": {
                        "kind": "official_disclosure",
                        "market": "US",
                        "published_at": "2026-08-25T12:01:00-04:00",
                    },
                },
            ],
        }

        _, message = module.build_message(payload)

        self.assertNotIn("Yesterday update", message)
        self.assertIn("[Today update](https://www.sec.gov/today.htm)", message)
        self.assertIn("| 1 | 00:01 | DONE |", message)

    def test_message_flattens_title_line_breaks_inside_table(self):
        module = load_module()
        payload = monitor_payload()
        payload["items"][0]["title"] = "中期业绩\n公告"

        _, message = module.build_message(payload)

        self.assertIn("中期业绩 公告", message)
        self.assertNotIn("中期业绩\n公告", message)


class WorkflowContractTest(unittest.TestCase):
    def test_weekday_schedule_and_safe_commit_order(self):
        workflow_path = REPO / ".github" / "workflows" / "daily-monitor.yml"
        workflow = yaml.load(workflow_path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)

        self.assertEqual(
            workflow["on"]["schedule"][0],
            {"cron": "30 17 * * 1-5", "timezone": "Asia/Shanghai"},
        )
        self.assertEqual(
            set(workflow["on"]["workflow_dispatch"]["inputs"]), {"commit", "notify"}
        )
        self.assertIn("concurrency", workflow)
        job = workflow["jobs"]["monitor"]
        self.assertGreater(int(job["timeout-minutes"]), 0)
        steps = job["steps"]
        commit = next(step for step in steps if step.get("id") == "commit_daily")
        self.assertIn(
            "git add reports/daily-monitor/ data/monitoring-state.json", commit["run"]
        )
        self.assertNotIn("data/triggers.json", commit["run"])
        pages_index = next(
            index for index, step in enumerate(steps) if step.get("id") == "rebuild_pages"
        )
        gate_index = next(
            index for index, step in enumerate(steps) if step.get("id") == "health_gate"
        )
        self.assertLess(pages_index, gate_index)


if __name__ == "__main__":
    unittest.main()

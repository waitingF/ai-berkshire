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
                "section": "disclosures",
                "name": "腾讯控股",
                "title": "新财报",
                "why_now": "需要复核",
                "notify": True,
                "resolved": False,
                "status": "DONE",
            },
            {
                "priority": "P2",
                "section": "price",
                "name": "微软",
                "title": "持续状态",
                "why_now": "无变化",
                "notify": False,
                "resolved": False,
                "status": "TRIGGERED",
            },
            {
                "priority": "P2",
                "section": "other",
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
    def test_retired_disclosures_and_events_are_not_rendered_or_sent(self):
        module = load_module()
        payload = monitor_payload()
        _, message = module.build_message(payload)

        self.assertIn("价格变化 0", message)
        self.assertNotIn("腾讯控股", message)
        self.assertNotIn("美团", message)
        self.assertNotIn("正式披露", message)
        self.assertNotIn("其他监控", message)
        self.assertEqual(module.send_notification(payload, sendkey="secret"), "SKIPPED")

    def test_quote_recovery_is_rendered_and_not_suppressed_as_resolved(self):
        module = load_module()
        payload = monitor_payload()
        payload["items"] = [{
            "section": "other", "name": "QUOTES", "title": "数据源已恢复",
            "why_now": "行情恢复", "status": "RECOVERED", "notify": True,
            "resolved": True, "metadata": {"service": "quotes"},
        }]
        _, message = module.build_message(payload)
        self.assertIn("数据源已恢复", message)
        self.assertEqual(module.send_notification(payload, sendkey="secret", post=lambda *args: '{"code":0}'), "SENT")


    def test_missing_sendkey_skips_without_failure(self):
        module = load_module()

        self.assertEqual(module.send_notification(monitor_payload(), sendkey=""), "SKIPPED")

    def test_no_changes_skips_even_with_key(self):
        module = load_module()
        payload = monitor_payload()
        for item in payload["items"]:
            item["notify"] = False

        self.assertEqual(module.send_notification(payload, sendkey="secret"), "SKIPPED")


    def test_above_warning_is_not_included_or_sent(self):
        module = load_module()
        payload = {
            "date": "2026-08-27",
            "status": "OK",
            "items": [
                {
                    "target_id": "沃尔玛",
                    "name": "Walmart",
                    "priority": "P0",
                    "section": "price",
                    "title": "估值警戒线：WARN",
                    "why_now": "现价越过估值警戒线。",
                    "notify": True,
                    "resolved": False,
                    "status": "WARN",
                    "metadata": {
                        "market": "US",
                        "zone_label": "估值警戒线",
                        "low": 120,
                        "high": None,
                        "direction": "above",
                        "price": 122,
                    },
                }
            ],
        }

        _, message = module.build_message(payload)

        self.assertNotIn("Walmart", message)
        self.assertIn("价格变化 0", message)
        self.assertIn("今日无新增进入或接近建仓/关注条件的标的", message)
        self.assertEqual(module.send_notification(payload, sendkey="secret"), "SKIPPED")

    def test_above_near_is_not_included_or_sent(self):
        module = load_module()
        payload = {
            "date": "2026-09-28",
            "status": "OK",
            "items": [
                {
                    "target_id": "Credo",
                    "name": "Credo Technology",
                    "priority": "P1",
                    "section": "price",
                    "title": "估值警戒线：NEAR",
                    "why_now": "距估值警戒线 4.1%",
                    "notify": True,
                    "resolved": False,
                    "status": "NEAR",
                    "metadata": {"direction": "above", "low": 220, "price": 210.97},
                }
            ],
        }

        _, message = module.build_message(payload)

        self.assertNotIn("Credo Technology", message)
        self.assertIn("价格变化 0", message)
        self.assertEqual(module.send_notification(payload, sendkey="secret"), "SKIPPED")


class WorkflowContractTest(unittest.TestCase):
    def test_weekday_schedule_and_safe_commit_order(self):
        workflow_path = REPO / ".github" / "workflows" / "daily-monitor.yml"
        workflow = yaml.load(workflow_path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)

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
        checkout = next(step for step in steps if step.get("uses") == "actions/checkout@v4")
        self.assertEqual(
            checkout["with"]["token"], "${{ secrets.DAILY_MONITOR_TOKEN }}"
        )
        self.assertFalse(
            any(step.get("id") == "rebuild_pages" for step in steps),
            "PAT 推送会自动触发 Pages，不应再次手动 dispatch",
        )
        self.assertFalse(
            any(step.get("id") == "health_gate" for step in steps),
            "降级状态只写入日报，不应再把 workflow 标记为失败",
        )


if __name__ == "__main__":
    unittest.main()

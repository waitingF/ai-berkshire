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

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
CLI = REPO / "tools" / "daily_monitor.py"
FIXTURES = REPO / "tests" / "fixtures" / "daily-monitor"


def run_cli(*args, env=None):
    command_env = {"PATH": os.environ.get("PATH", ""), "PYTHONPATH": str(REPO)}
    if env:
        command_env.update(env)
    return subprocess.run(
        [sys.executable, str(CLI), *map(str, args)],
        cwd=REPO,
        env=command_env,
        text=True,
        capture_output=True,
        timeout=30,
    )


class DailyMonitorCliTest(unittest.TestCase):
    def test_offline_run_writes_only_to_supplied_runtime_paths(self):
        initial_state = (REPO / "data" / "monitoring-state.json").read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "state.json"
            reports = Path(tmp) / "reports"

            completed = run_cli(
                "--offline-fixtures",
                FIXTURES,
                "--today",
                "2026-08-27",
                "--state-file",
                state,
                "--report-dir",
                reports,
                "--json",
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["status"], "OK")
            self.assertTrue((reports / "daily-monitor-latest.md").exists())
            report_payload = json.loads(
                (reports / "daily-monitor-latest.json").read_text(encoding="utf-8")
            )
            disclosure_summaries = [
                item
                for item in report_payload["items"]
                if item.get("metadata", {}).get("kind") == "disclosure_summary"
            ]
            self.assertEqual(disclosure_summaries, [])
            self.assertTrue(state.exists())
            state_payload = json.loads(state.read_text(encoding="utf-8"))
            self.assertGreaterEqual(len(state_payload["documents"]), 3)
            self.assertEqual(
                (REPO / "data" / "monitoring-state.json").read_text(encoding="utf-8"),
                initial_state,
            )

    def test_today_override_requires_offline_fixtures(self):
        completed = run_cli("--today", "2026-08-27", "--json")

        self.assertEqual(completed.returncode, 2)
        self.assertIn("--today 仅能与 --offline-fixtures 一起使用", completed.stderr)

    def test_check_ai_requires_key_without_printing_secret(self):
        completed = run_cli("--check-ai")

        self.assertEqual(completed.returncode, 1)
        self.assertIn("DEEPSEEK_API_KEY", completed.stderr)

    def test_check_is_read_only_and_validates_configuration(self):
        initial_state = (REPO / "data" / "monitoring-state.json").read_text(encoding="utf-8")

        completed = run_cli("--check")

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("配置校验通过", completed.stdout)
        self.assertEqual(
            (REPO / "data" / "monitoring-state.json").read_text(encoding="utf-8"),
            initial_state,
        )

    def test_help_exposes_isolated_and_watch_flags(self):
        completed = run_cli("--help")

        self.assertEqual(completed.returncode, 0)
        for flag in (
            "--check",
            "--check-ai",
            "--no-ai",
            "--offline-fixtures",
            "--today",
            "--watch",
            "--state-file",
            "--report-dir",
            "--json",
        ):
            self.assertIn(flag, completed.stdout)


if __name__ == "__main__":
    unittest.main()

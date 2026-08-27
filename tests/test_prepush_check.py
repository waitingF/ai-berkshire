from __future__ import annotations

import os
from pathlib import Path
import stat
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class PrepushCheckTest(unittest.TestCase):
    def test_fails_when_daily_monitor_config_check_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            fake_python = Path(tmp) / "python3"
            fake_python.write_text(
                """#!/bin/sh
if [ \"$1\" = \"tools/daily_monitor.py\" ]; then
  echo daily-monitor-config-error >&2
  exit 42
fi
if [ \"$1\" = \"tools/trigger_scanner.py\" ] && [ \"$2\" = \"--json\" ]; then
  echo '{"scanned_targets":0,"triggered":0,"near":0,"events_total":0,"report":"fixture","review_items":[]}'
  exit 0
fi
if [ \"$1\" = \"-\" ]; then
  cat >/dev/null
fi
exit 0
""",
                encoding="utf-8",
            )
            fake_python.chmod(fake_python.stat().st_mode | stat.S_IXUSR)
            env = os.environ.copy()
            env["PATH"] = f"{tmp}:{env['PATH']}"

            result = subprocess.run(
                ["bash", "scripts/prepush-check.sh"],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("daily-monitor-config-error", result.stderr)


if __name__ == "__main__":
    unittest.main()

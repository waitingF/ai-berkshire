#!/usr/bin/env python3
"""Refresh prices and stage only this run's machine outputs for the active commit."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    print("提交前刷新每日监控（腾讯 / Yahoo Finance 行情，不发送通知）……", flush=True)
    # A page refresh must not consume the scheduled monitor's notification baseline.
    with tempfile.TemporaryDirectory(prefix="daily-monitor-commit-") as runtime:
        state = Path(runtime) / "state.json"
        current_state = root / "data/monitoring-state.json"
        if current_state.exists():
            shutil.copyfile(current_state, state)
        completed = subprocess.run(
            [sys.executable, "tools/daily_monitor.py", "--state-file", str(state), "--json"],
            cwd=root, capture_output=True, text=True,
        )
    if completed.stderr:
        sys.stderr.write(completed.stderr)
    try:
        if completed.returncode not in (0, 2):
            raise ValueError(f"监控进程退出码 {completed.returncode}")
        summary = json.loads(completed.stdout)
        day = date.fromisoformat(summary["date"])
        if (completed.returncode, summary["status"]) not in {(0, "OK"), (2, "DEGRADED")}:
            raise ValueError("监控未正常生成报告")
        directory = "reports/daily-monitor"
        paths = [
            f"{directory}/daily-monitor-latest.md",
            f"{directory}/daily-monitor-latest.json",
            f"{directory}/daily-monitor-{day:%Y%m%d}.md",
        ]
        subprocess.run(["git", "add", "--", *paths], cwd=root, check=True)
    except (ValueError, KeyError, OSError, subprocess.CalledProcessError) as exc:
        print(f"提交已阻止：每日监控刷新或暂存失败（{exc}）。", file=sys.stderr)
        return 1
    print(f"每日监控已刷新并暂存：{day} · {summary['status']}。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

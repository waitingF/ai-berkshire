#!/usr/bin/env python3
"""Refresh the price monitor locally or from GitHub Actions."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.daily_monitoring.config import load_targets
from tools.daily_monitoring.runner import (
    MonitorOptions,
    MonitorServices,
    production_services,
    run_monitor,
)
from tools.daily_monitoring.state import load_state


DEFAULT_TRIGGERS = ROOT / "data" / "triggers.json"
DEFAULT_STATE = ROOT / "data" / "monitoring-state.json"
DEFAULT_REPORT_DIR = ROOT / "reports" / "daily-monitor"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="每日价格监控：读取已登记价格区间与腾讯 / Yahoo Finance 行情快照。"
    )
    parser.add_argument("--check", action="store_true", help="只读校验配置和状态")
    parser.add_argument(
        "--offline-fixtures",
        type=Path,
        metavar="PATH",
        help="使用离线夹具运行，禁止所有出站请求",
    )
    parser.add_argument(
        "--today",
        type=date.fromisoformat,
        metavar="YYYY-MM-DD",
        help="离线夹具回放日期（仅可与 --offline-fixtures 一起使用）",
    )
    parser.add_argument(
        "--watch",
        nargs="+",
        default=(),
        metavar="TARGET",
        help="仅扫描匹配的标的 ID、名称或代码",
    )
    parser.add_argument(
        "--state-file", type=Path, default=DEFAULT_STATE, help="机器状态文件路径"
    )
    parser.add_argument(
        "--report-dir", type=Path, default=DEFAULT_REPORT_DIR, help="报告输出目录"
    )
    parser.add_argument("--json", action="store_true", help="向标准输出写 JSON 摘要")
    return parser


def _offline_services(fixtures: Path) -> MonitorServices:
    fixture_file = fixtures / "quotes.json"
    payload = json.loads(fixture_file.read_text(encoding="utf-8"))

    def quote_provider(codes):
        return {code: payload.get(code, payload.get("default", {})) for code in codes}

    return MonitorServices(quote_provider=quote_provider)


def _check_configuration(state_file: Path) -> int:
    targets = load_targets(DEFAULT_TRIGGERS)
    state = load_state(state_file)
    print(
        f"配置校验通过：{len(targets)} 个标的；"
        f"monitoring-state schema={state['schema']}。"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    offline = args.offline_fixtures is not None
    if args.today is not None and not offline:
        parser.error("--today 仅能与 --offline-fixtures 一起使用")
    try:
        if args.check:
            return _check_configuration(args.state_file)
        default_state = args.state_file.expanduser().resolve() == DEFAULT_STATE.resolve()
        default_reports = (
            args.report_dir.expanduser().resolve() == DEFAULT_REPORT_DIR.resolve()
        )
        if args.watch and (default_state or default_reports):
            parser.error(
                "--watch 仅可配合自定义的 --state-file 和 --report-dir 使用，"
                "以免覆盖完整的每日监控报告"
            )
        if offline:
            services = _offline_services(args.offline_fixtures)
        else:
            services = production_services()
        today = args.today or datetime.now(ZoneInfo("Asia/Shanghai")).date()
        result = run_monitor(
            MonitorOptions(
                root=ROOT,
                triggers_file=DEFAULT_TRIGGERS,
                state_file=args.state_file.resolve(),
                report_dir=args.report_dir.resolve(),
                today=today,
                watch=tuple(args.watch),
            ),
            services,
        )
        payload = {
            "status": result.status,
            "date": today.isoformat(),
            "items": len(result.items),
            "notifications": len(result.notification_items),
            "report": str(result.report_paths.latest),
            "state_file": str(args.state_file.resolve()),
        }
        if args.json:
            print(json.dumps(payload, ensure_ascii=False))
        else:
            print(
                f"每日监控 {result.status}：{len(result.items)} 项，"
                f"{len(result.notification_items)} 项需通知。"
            )
            print(f"报告：{result.report_paths.latest}")
        return 2 if result.status == "DEGRADED" else 0
    except Exception as exc:
        print(f"每日监控启动失败：{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

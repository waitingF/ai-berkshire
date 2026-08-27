#!/usr/bin/env python3
"""Run the unified daily monitor locally or from GitHub Actions."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.daily_monitoring.config import load_targets
from tools.daily_monitoring.collectors import cninfo, hkex, sec
from tools.daily_monitoring.deepseek import DeepSeekClient
from tools.daily_monitoring.documents import ExtractedDocument
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
        description="每日监控：价格、正式披露和其他研究缺口的统一扫描。"
    )
    parser.add_argument("--check", action="store_true", help="只读校验配置和状态")
    parser.add_argument(
        "--check-ai",
        action="store_true",
        help="只用合成数据检查 DeepSeek API Key，不读取标的或写文件",
    )
    parser.add_argument("--no-ai", action="store_true", help="显式跳过 AI 增量判断")
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
    if not fixtures.is_dir():
        raise ValueError(f"离线夹具目录不存在: {fixtures}")
    required = (
        "cninfo-org-search.json",
        "cninfo-response.json",
        "hkex-active-stocks.json",
        "hkex-response.json",
        "sec-company-tickers.json",
        "sec-submissions.json",
        "deepseek-valid.json",
    )
    missing = [name for name in required if not (fixtures / name).is_file()]
    if missing:
        raise ValueError(f"离线夹具不完整: {', '.join(missing)}")
    for name in required:
        json.loads((fixtures / name).read_text(encoding="utf-8"))

    def quote_provider(codes):
        # Stable positive values establish a non-notifying baseline on an empty state.
        return {code: {"price": 1.0, "time": "OFFLINE"} for code in codes}

    fixtures_by_name = {
        name: json.loads((fixtures / name).read_text(encoding="utf-8"))
        for name in required
    }

    class FixtureHttp:
        def get_json(self, url, *, source, params=None, headers=None):
            if "activestock" in url:
                return fixtures_by_name["hkex-active-stocks.json"]
            if "titleSearchServlet" in url:
                return fixtures_by_name["hkex-response.json"]
            if "company_tickers" in url:
                return fixtures_by_name["sec-company-tickers.json"]
            if "submissions" in url:
                return fixtures_by_name["sec-submissions.json"]
            raise AssertionError(f"离线模式拒绝未登记请求: {source} {url}")

        def post_form_json(self, url, form, *, source, headers=None):
            if "topSearch" in url:
                return fixtures_by_name["cninfo-org-search.json"]
            if "hisAnnouncement" in url:
                return fixtures_by_name["cninfo-response.json"]
            raise AssertionError(f"离线模式拒绝未登记请求: {source} {url}")

        def get_bytes(self, *args, **kwargs):
            raise AssertionError("离线模式禁止下载公告正文")

    fixture_http = FixtureHttp()

    def cninfo_fixture(target_id, config, *, since, until, http):
        if config.get("stock_code") != "600519":
            return []
        return cninfo.collect(
            target_id, config, since=since, until=until, http=fixture_http
        )

    def hkex_fixture(target_id, config, *, since, until, http):
        if config.get("stock_code") != "00700":
            return []
        return hkex.collect(
            target_id, config, since=since, until=until, http=fixture_http
        )

    def sec_fixture(target_id, config, *, since, until, http):
        if config.get("ticker") != "PDD":
            return []
        return sec.collect(
            target_id, config, since=since, until=until, http=fixture_http
        )

    def fixture_extractor(disclosure, target, http):
        return ExtractedDocument(
            status="EXTRACTED",
            sha256=(disclosure.document_id.encode("utf-8").hex() + "0" * 64)[:64],
            pages_used=(1,),
            chunks=(f"[PAGE 1]\nOFFLINE FIXTURE: {disclosure.title}",),
            limitation="离线夹具仅含清洗后的最小样本文本",
        )

    return MonitorServices(
        quote_provider=quote_provider,
        collectors={
            "cninfo": cninfo_fixture,
            "hkex": hkex_fixture,
            "sec": sec_fixture,
        },
        http=fixture_http,
        document_extractor=fixture_extractor,
        deepseek=None,
    )


def _check_ai() -> int:
    api_key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if not api_key:
        print("错误：未配置 DEEPSEEK_API_KEY。", file=sys.stderr)
        return 1
    client = DeepSeekClient(
        api_key=api_key,
        model=os.environ.get("DEEPSEEK_MODEL"),
    )
    started = time.monotonic()
    result = client.check_api_key()
    latency = time.monotonic() - started
    if result.status != "OK":
        print(
            "DeepSeek JSON contract: FAILED；"
            + "；".join(result.limitations),
            file=sys.stderr,
        )
        return 1
    print(f"DeepSeek JSON contract: OK | model={client.model} | latency={latency:.2f}s")
    return 0


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
    if args.check_ai:
        return _check_ai()
    try:
        if args.check:
            return _check_configuration(args.state_file)
        if offline:
            services = _offline_services(args.offline_fixtures)
        else:
            services = production_services(
                edgar_identity=os.environ.get("EDGAR_IDENTITY"),
                deepseek_api_key=os.environ.get("DEEPSEEK_API_KEY"),
                deepseek_model=os.environ.get("DEEPSEEK_MODEL"),
                no_ai=args.no_ai,
            )
        today = args.today or datetime.now(ZoneInfo("Asia/Shanghai")).date()
        result = run_monitor(
            MonitorOptions(
                root=ROOT,
                triggers_file=DEFAULT_TRIGGERS,
                state_file=args.state_file.resolve(),
                report_dir=args.report_dir.resolve(),
                today=today,
                no_ai=args.no_ai or offline,
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

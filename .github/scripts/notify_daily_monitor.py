#!/usr/bin/env python3
"""Send ServerChan notifications for price-monitor state changes only."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable


def _item_market(item: dict[str, Any]) -> str:
    return str((item.get("metadata") or {}).get("market") or "")


def _changed_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        item for item in payload.get("items", [])
        if item.get("notify") is True
        and (
            item.get("section") == "price"
            or (item.get("metadata") or {}).get("service") == "quotes"
        )
        and (not item.get("resolved") or (item.get("metadata") or {}).get("service") == "quotes")
        and item.get("status") != "WARN"
        and (item.get("metadata") or {}).get("direction") != "above"
    ]


def _safe_cell(value: Any) -> str:
    return " ".join(str(value or "-").replace("|", "／").split())


def _number(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number == number else None


def _price_band(item: dict[str, Any]) -> str:
    metadata = item.get("metadata") or {}
    label = _safe_cell(metadata.get("zone_label") or item.get("title") or "价格条件")
    low = _number(metadata.get("low"))
    high = _number(metadata.get("high"))
    direction = metadata.get("direction", "range")
    if direction == "below" and high is not None:
        condition = f"≤{high:.2f}"
    elif low is not None and high is not None:
        condition = f"{low:.2f}–{high:.2f}"
    elif high is not None:
        condition = f"≤{high:.2f}"
    elif low is not None:
        condition = f"≥{low:.2f}"
    else:
        condition = "-"
    return f"{label} {condition}"


def _price_gap(item: dict[str, Any]) -> str:
    metadata = item.get("metadata") or {}
    price = _number(metadata.get("price"))
    low = _number(metadata.get("low"))
    high = _number(metadata.get("high"))
    status = item.get("status")
    if status == "NO_DATA" or price is None:
        return "无行情"
    if status == "RESOLVED":
        return "已离开"
    if status == "WARN":
        return "已越警戒线"
    if status == "TRIGGERED":
        if low is not None and low > 0 and price < low:
            return f"低于下界 {(low - price) / low:.1%}"
        return "区间内"
    boundary = high if high is not None else low
    if boundary is None or boundary <= 0:
        return "-"
    return f"{abs(price - boundary) / boundary:.1%}"


def build_message(payload: dict[str, Any]) -> tuple[str, str]:
    changed = _changed_items(payload)
    price_rows = [item for item in changed if item.get("section") == "price"]
    service_rows = [item for item in changed if (item.get("metadata") or {}).get("service") == "quotes"]
    title = f"价格监控 {payload.get('date', '')}"[:32]
    lines = [
        f"**运行状态**：{payload.get('status', 'UNKNOWN')}",
        f"**今日增量**：价格变化 {len(price_rows)}",
        "",
    ]
    if payload.get("status") == "DEGRADED":
        reasons = [
            str(row.get("safe_message") or "行情源请求失败")
            for row in payload.get("source_health", [])
            if row.get("source") == "quotes" and row.get("status") not in {"OK", "RECOVERED"}
        ]
        detail = "；".join(reasons) or "行情暂不可用"
        lines.extend([f"> **降级原因**：{detail}", ""])
    for item in service_rows:
        lines.extend([f"> **行情源**：{_safe_cell(item.get('title'))}；{_safe_cell(item.get('why_now'))}", ""])

    lines.extend(["## 一、价格监控", ""])
    if price_rows:
        lines.extend(
            [
                "| 优先级 | 标的 | 市场 | 监控区间 | 现价 | 距边界 | 状态 |",
                "|---|---|---|---|---:|---:|---|",
            ]
        )
        for item in price_rows:
            metadata = item.get("metadata") or {}
            price = _number(metadata.get("price"))
            lines.append(
                f"| {item.get('priority') or '-'} | {_safe_cell(item.get('name') or item.get('target_id'))} | "
                f"{_item_market(item) or '-'} | {_price_band(item)} | "
                f"{price:.2f} | {_price_gap(item)} | {item.get('status') or '-'} |"
                if price is not None
                else f"| {item.get('priority') or '-'} | {_safe_cell(item.get('name') or item.get('target_id'))} | "
                f"{_item_market(item) or '-'} | {_price_band(item)} | - | {_price_gap(item)} | {item.get('status') or '-'} |"
            )
        lines.extend(
            [
                "",
                "> 仅展示今日新进入、接近或离开监控条件的标的；完整价格状态见每日监控页面。",
            ]
        )
    else:
        lines.append("今日无新增进入或接近建仓/关注条件的标的。")


    lines.extend(["", "仅用于研究复核，不构成买卖或仓位建议。"])
    return title, "\n".join(lines)


def _post_serverchan(url: str, data: dict[str, str]) -> str:
    result = subprocess.run(
        [
            "/usr/bin/curl",
            "-s",
            "--noproxy",
            "*",
            "-X",
            "POST",
            "--data-urlencode",
            f"title={data['title']}",
            "--data-urlencode",
            f"desp={data['desp']}",
            url,
        ],
        capture_output=True,
        timeout=30,
    )
    if result.returncode:
        raise ConnectionError("ServerChan 请求失败")
    return result.stdout.decode("utf-8", errors="replace")


def send_notification(
    payload: dict[str, Any],
    *,
    sendkey: str,
    post: Callable[[str, dict[str, str]], str] | None = None,
) -> str:
    if not _changed_items(payload) or not sendkey.strip():
        return "SKIPPED"
    title, message = build_message(payload)
    response = (post or _post_serverchan)(
        f"https://sctapi.ftqq.com/{sendkey.strip()}.send",
        {"title": title, "desp": message},
    )
    try:
        body = json.loads(response)
    except json.JSONDecodeError as exc:
        raise RuntimeError("ServerChan 返回非 JSON") from exc
    if body.get("code") != 0:
        raise RuntimeError(f"ServerChan 返回错误 code={body.get('code')}")
    return "SENT"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="每日监控增量通知")
    parser.add_argument("report_json", type=Path)
    parser.add_argument("--preview", action="store_true")
    args = parser.parse_args(argv)
    payload = json.loads(args.report_json.read_text(encoding="utf-8"))
    if args.preview:
        title, message = build_message(payload)
        print(f"标题：{title}\n\n{message}")
        return 0
    status = send_notification(
        payload, sendkey=os.environ.get("SERVERCHAN_SENDKEY", "")
    )
    print("每日监控通知：" + status)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"每日监控通知失败：{type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(1)

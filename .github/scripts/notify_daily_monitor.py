#!/usr/bin/env python3
"""Send ServerChan notifications for daily-monitor state changes only."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable


def _changed_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    return [item for item in payload.get("items", []) if item.get("notify") is True]


def build_message(payload: dict[str, Any]) -> tuple[str, str]:
    changed = _changed_items(payload)
    active = [item for item in changed if not item.get("resolved")]
    resolved = [item for item in changed if item.get("resolved")]
    p0 = [item for item in active if item.get("priority") == "P0"]
    p1 = [item for item in active if item.get("priority") == "P1"]
    title = f"每日监控 {payload.get('date', '')}"[:32]
    lines = [
        f"**运行状态**：{payload.get('status', 'UNKNOWN')}",
        f"**新增 P0：{len(p0)}｜新增 P1：{len(p1)}｜已解除：{len(resolved)}**",
        "",
    ]
    for heading, rows in (("P0", p0), ("P1", p1), ("已解除", resolved)):
        if not rows:
            continue
        lines.extend([f"## {heading}", "", "| 标的 | 事项 | 原因 |", "|---|---|---|"])
        for item in rows:
            name = str(item.get("name") or item.get("target_id") or "-").replace("|", "／")
            item_title = str(item.get("title") or "-").replace("|", "／")
            reason = str(item.get("why_now") or "-").replace("|", "／").replace("\n", " ")
            lines.append(f"| {name} | {item_title} | {reason[:120]} |")
        lines.append("")
    lines.append("仅用于研究复核，不构成买卖或仓位建议。")
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

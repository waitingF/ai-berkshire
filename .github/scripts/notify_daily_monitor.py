#!/usr/bin/env python3
"""Send ServerChan notifications for daily-monitor state changes only."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any, Callable
from zoneinfo import ZoneInfo


PRIORITY_RANK = {"P2": 0, "P1": 1, "P0": 2}
OFFICIAL_HOSTS = ("hkexnews.hk", "sec.gov", "cninfo.com.cn")


def _item_market(item: dict[str, Any]) -> str:
    metadata = item.get("metadata") or {}
    if market := str(metadata.get("market") or "").strip():
        return market
    source = str(metadata.get("source") or "").strip()
    if source in {"cninfo", "akshare"}:
        return "A"
    if source == "hkex":
        return "H"
    if source == "sec":
        return "US"
    urls = " ".join(str(url).casefold() for url in item.get("source_urls") or [])
    if "hkexnews.hk" in urls:
        return "H"
    if "sec.gov" in urls:
        return "US"
    if "cninfo.com.cn" in urls:
        return "A"
    return ""


def _published_datetime(item: dict[str, Any]) -> datetime | None:
    metadata = item.get("metadata") or {}
    value = str(metadata.get("published_at") or "").strip()
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        parsed = None
        for pattern in (
            "%d/%m/%Y %H:%M",
            "%d/%m/%Y",
            "%Y/%m/%d %H:%M",
            "%Y/%m/%d",
        ):
            try:
                parsed = datetime.strptime(value, pattern)
                break
            except ValueError:
                continue
        if parsed is None:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=ZoneInfo("Asia/Shanghai"))
    return parsed.astimezone(ZoneInfo("Asia/Shanghai"))


def _is_official_disclosure(item: dict[str, Any]) -> bool:
    metadata = item.get("metadata") or {}
    kind = metadata.get("kind")
    if kind == "official_disclosure":
        return True
    if kind or metadata.get("fallback") or item.get("section") != "disclosures":
        return False
    urls = " ".join(str(url).casefold() for url in item.get("source_urls") or [])
    return any(host in urls for host in OFFICIAL_HOSTS)


def _is_placeholder_disclosure(item: dict[str, Any]) -> bool:
    title = " ".join(str(item.get("title") or "").casefold().split())
    return "an announcement has just been published by the issuer" in title


def _update_topic(item: dict[str, Any]) -> str:
    title = " ".join(str(item.get("title") or "").split())
    upper = title.upper()
    year_match = re.search(r"\b(20\d{2})\b", title)
    year = year_match.group(1) if year_match else ""
    if "INTERIM RESULTS" in upper:
        return f"{year + '年' if year else ''}中期业绩"
    if "H SHARE FULL CIRCULATION" in upper:
        return "H股全流通申请"
    if "NEXT DAY DISCLOSURE RETURN" in upper:
        return "翌日披露报表"
    if _is_placeholder_disclosure(item):
        return "新增公告，内容待确认"
    return title[:60] + ("…" if len(title) > 60 else "")


def _aggregate_changed_disclosures(
    changed: list[dict[str, Any]], *, today: date
) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
    result: list[dict[str, Any]] = []
    for item in changed:
        metadata = item.get("metadata") or {}
        if metadata.get("kind") == "disclosure_summary":
            result.append(item)
            continue
        if not _is_official_disclosure(item):
            result.append(item)
            continue
        published = _published_datetime(item)
        if published is None or published.date() != today:
            continue
        market = _item_market(item)
        target_id = str(item.get("target_id") or item.get("name") or "").strip()
        if not market or not target_id:
            result.append(item)
            continue
        groups.setdefault((target_id, market), []).append(item)

    for (target_id, market), rows in groups.items():
        substantive = [item for item in rows if not _is_placeholder_disclosure(item)]
        if substantive:
            rows = substantive
        rows.sort(key=_published_datetime)
        latest = _published_datetime(rows[-1])
        assert latest is not None
        updates = [
            {
                "summary": _update_topic(item),
                "source_urls": list(item.get("source_urls") or []),
            }
            for item in rows
        ]
        summary = dict(rows[0])
        summary["priority"] = max(
            rows, key=lambda item: PRIORITY_RANK.get(item.get("priority"), -1)
        ).get("priority")
        summary["title"] = f"{len(rows)} 项公告更新"
        summary["why_now"] = "；".join(update["summary"] for update in updates)
        completed = all(
            item.get("status") == "DONE" and not item.get("needs_human_review")
            for item in rows
        )
        summary["status"] = "DONE" if completed else "REVIEW"
        summary["needs_human_review"] = not completed
        summary["source_urls"] = list(
            dict.fromkeys(url for item in rows for url in item.get("source_urls") or [])
        )
        summary["metadata"] = {
            "kind": "disclosure_summary",
            "market": market,
            "date": today.isoformat(),
            "latest_time": latest.isoformat(),
            "announcement_count": len(rows),
            "updates": updates,
        }
        result.append(summary)
    return result


def _changed_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    changed = [
        item for item in payload.get("items", []) if item.get("notify") is True
    ]
    try:
        today = date.fromisoformat(str(payload.get("date") or ""))
    except ValueError:
        return changed
    return _aggregate_changed_disclosures(changed, today=today)


def _summary_updates(item: dict[str, Any]) -> str:
    updates = []
    for update in (item.get("metadata") or {}).get("updates") or []:
        summary = str(update.get("summary") or "新增公告")
        urls = update.get("source_urls") or []
        updates.append(f"[{summary}]({urls[0]})" if urls else summary)
    return "<br>".join(updates) or "-"


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
        lines.extend([f"## {heading}", ""])
        summaries = [
            item
            for item in rows
            if (item.get("metadata") or {}).get("kind") == "disclosure_summary"
        ]
        regular = [item for item in rows if item not in summaries]
        if summaries:
            lines.extend(
                [
                    "| 标的 | 市场 | 更新摘要 | 公告数 | 最新时间 | 状态 |",
                    "|---|---|---|---:|---|---|",
                ]
            )
        for item in summaries:
            metadata = item.get("metadata") or {}
            latest = str(metadata.get("latest_time") or "")
            try:
                latest = datetime.fromisoformat(latest).strftime("%H:%M")
            except ValueError:
                latest = latest or "-"
            name = str(item.get("name") or item.get("target_id") or "-").replace("|", "／")
            lines.append(
                f"| {name} | {_item_market(item) or '-'} | {_summary_updates(item)} | "
                f"{metadata.get('announcement_count') or 0} | {latest} | {item.get('status') or '-'} |"
            )
        if summaries:
            lines.append("")
        if regular:
            lines.extend(["| 标的 | 市场 | 事项 | 原因 |", "|---|---|---|---|"])
        for item in regular:
            name = str(item.get("name") or item.get("target_id") or "-").replace("|", "／")
            market = _item_market(item) or "-"
            item_title = (
                str(item.get("title") or "-")
                .replace("|", "／")
                .replace("\n", " ")
            )
            reason = str(item.get("why_now") or "-").replace("|", "／").replace("\n", " ")
            lines.append(f"| {name} | {market} | {item_title} | {reason[:120]} |")
        if regular:
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

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
        item
        for item in payload.get("items", [])
        if item.get("notify") is True
        and not item.get("resolved")
        and not (item.get("section") == "price" and item.get("status") == "WARN")
    ]
    try:
        today = date.fromisoformat(str(payload.get("date") or ""))
    except ValueError:
        return changed
    return _aggregate_changed_disclosures(changed, today=today)


def _summary_updates(item: dict[str, Any]) -> str:
    metadata_updates = (item.get("metadata") or {}).get("updates") or []
    updates = []
    for update in metadata_updates[:3]:
        summary = _safe_cell(update.get("summary") or "新增公告")
        urls = update.get("source_urls") or []
        updates.append(f"[{summary}]({urls[0]})" if urls else summary)
    remaining = len(metadata_updates) - len(updates)
    if remaining > 0:
        updates.append(f"另 {remaining} 项（完整清单见每日监控页面）")
    return "<br>".join(updates) or "-"


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


def _degradation_reasons(payload: dict[str, Any]) -> list[str]:
    reasons: list[str] = []

    def add(name: str, limitations: Any) -> None:
        for limitation in limitations or []:
            reason = f"{name}：{_safe_cell(limitation)}"
            if reason not in reasons:
                reasons.append(reason)

    for health in payload.get("source_health") or []:
        if health.get("status") not in {"OK", "RECOVERED"}:
            add(str(health.get("source") or "数据源"), [health.get("safe_message")])
    for item in payload.get("items") or []:
        name = _safe_cell(item.get("name") or item.get("target_id") or "监控项")
        if item.get("status") in {"PENDING_AI", "PENDING_EXTRACTION", "OCR_REQUIRED"}:
            add(name, item.get("limitations"))
        for update in (item.get("metadata") or {}).get("updates") or []:
            if update.get("status") in {"PENDING_AI", "PENDING_EXTRACTION", "OCR_REQUIRED"}:
                add(name, update.get("limitations"))
    return reasons


def build_message(payload: dict[str, Any]) -> tuple[str, str]:
    changed = _changed_items(payload)
    price_rows = [item for item in changed if item.get("section") == "price"]
    disclosure_rows = [item for item in changed if item.get("section") == "disclosures"]
    disclosure_summaries = [
        item
        for item in disclosure_rows
        if (item.get("metadata") or {}).get("kind") == "disclosure_summary"
    ]
    event_rows = [item for item in disclosure_rows if item not in disclosure_summaries]
    other_rows = [
        item for item in changed if item.get("section") not in {"price", "disclosures"}
    ]
    title = f"每日监控 {payload.get('date', '')}"[:32]
    lines = [
        f"**运行状态**：{payload.get('status', 'UNKNOWN')}",
        f"**今日增量**：价格变化 {len(price_rows)}｜正式披露 {len(disclosure_summaries)} 组｜"
        f"财报节点 {len(event_rows)}｜其他 {len(other_rows)}",
        "",
    ]
    if payload.get("status") == "DEGRADED":
        reasons = _degradation_reasons(payload)
        detail = "；".join(reasons[:3]) or "存在待重试的数据源、正文提取或 AI 分诊事项"
        lines.extend([f"> **降级原因**：{detail}", ""])

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

    lines.extend(["", "## 二、财报与正式披露监控", "", "### 正式披露", ""])
    if disclosure_summaries:
        lines.extend(
            [
                "| 优先级 | 标的 | 市场 | 更新摘要 | 公告数 | 最新时间 | 状态 |",
                "|---|---|---|---|---:|---|---|",
            ]
        )
        for item in disclosure_summaries:
            metadata = item.get("metadata") or {}
            latest = str(metadata.get("latest_time") or "")
            try:
                latest = datetime.fromisoformat(latest).strftime("%H:%M")
            except ValueError:
                latest = latest or "-"
            lines.append(
                f"| {item.get('priority') or '-'} | {_safe_cell(item.get('name') or item.get('target_id'))} | "
                f"{_item_market(item) or '-'} | {_summary_updates(item)} | "
                f"{metadata.get('announcement_count') or 0} | {latest} | {item.get('status') or '-'} |"
            )
    else:
        lines.append("今日无新增正式披露。")

    lines.extend(["", "### 财报与复检节点", ""])
    if event_rows:
        lines.extend(
            [
                "| 优先级 | 标的 | 节点 | 到期状态 | 需要核验 |",
                "|---|---|---|---|---|",
            ]
        )
        for item in event_rows:
            metadata = item.get("metadata") or {}
            note = metadata.get("note") or item.get("why_now") or "-"
            lines.append(
                f"| {item.get('priority') or '-'} | {_safe_cell(item.get('name') or item.get('target_id'))} | "
                f"{_safe_cell(item.get('title'))} | {item.get('status') or '-'} | {_safe_cell(note)[:120]} |"
            )
    else:
        lines.append("今日无新增财报或复检节点变化。")

    lines.extend(["", "## 三、其他监控", ""])
    if other_rows:
        lines.extend(
            [
                "| 优先级 | 标的/数据源 | 事项 | 状态 | 原因 |",
                "|---|---|---|---|---|",
            ]
        )
        for item in other_rows:
            lines.append(
                f"| {item.get('priority') or '-'} | {_safe_cell(item.get('name') or item.get('target_id'))} | "
                f"{_safe_cell(item.get('title'))} | {item.get('status') or '-'} | "
                f"{_safe_cell(item.get('why_now'))[:120]} |"
            )
    else:
        lines.append("今日无新增研究缺口。")

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

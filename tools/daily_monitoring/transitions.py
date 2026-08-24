"""Deterministic price/event transitions and program priority floors."""

from __future__ import annotations

import hashlib
import json
from datetime import date, datetime
from typing import Any

from .models import MonitorItem


PRIORITY_RANK = {"P2": 0, "P1": 1, "P0": 2}
FINANCIAL_EVENT_TYPES = frozenset(
    {
        "财报",
        "年报",
        "中报",
        "季报",
        "业绩预告",
        "业绩快报",
        "盈利预警",
        "公告",
    }
)
ACTIVE_PRICE_STATES = frozenset({"TRIGGERED", "WARN", "NEAR"})
ACTIVE_EVENT_STATES = frozenset({"OVERDUE", "TODAY", "UPCOMING_7D", "UPCOMING_14D", "OPEN"})


def _fingerprint(*parts: Any) -> str:
    encoded = json.dumps(parts, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def apply_priority_floor(ai_priority: str, program_floor: str) -> str:
    """Return the more urgent priority, rejecting unknown model values."""
    for priority in (ai_priority, program_floor):
        if priority not in PRIORITY_RANK:
            raise ValueError(f"非法优先级: {priority}")
    if PRIORITY_RANK[ai_priority] >= PRIORITY_RANK[program_floor]:
        return ai_priority
    return program_floor


def price_state_key(target: dict[str, Any], zone: dict[str, Any]) -> str:
    return _fingerprint(
        "price",
        target.get("id"),
        zone.get("market"),
        zone.get("label"),
        zone.get("dir", "range"),
        zone.get("low"),
        zone.get("high"),
    )


def price_item(
    target: dict[str, Any],
    zone: dict[str, Any],
    *,
    previous: str | None,
    current: str,
    price: float | None,
    message: str | None = None,
) -> MonitorItem | None:
    """Create a report item only for visible current states or state changes."""
    target_id = str(target.get("id", ""))
    name = str(target.get("name") or target_id)
    label = str(zone.get("label") or "价格条件")
    fingerprint = price_state_key(target, zone)
    metadata = {
        "previous_status": previous,
        "current_status": current,
        "price": price,
        "market": zone.get("market"),
        "zone_label": label,
        "low": zone.get("low"),
        "high": zone.get("high"),
        "direction": zone.get("dir", "range"),
        "note": zone.get("note", ""),
    }

    if previous is None:
        if current == "FAR":
            return None
        if current == "NO_DATA":
            return MonitorItem(
                fingerprint=fingerprint,
                section="price",
                priority="P1",
                target_id=target_id,
                name=name,
                title=f"{label}：行情不可用",
                why_now="首次建立监控基线时未取得有效行情，需要确认代码或行情源。",
                status=current,
                needs_human_review=True,
                notify=True,
                metadata=metadata,
            )
        return MonitorItem(
            fingerprint=fingerprint,
            section="price",
            priority="P2",
            target_id=target_id,
            name=name,
            title=f"{label}：初始基线",
            why_now="当前价格状态已记录为初始基线，不能据此声称刚刚进入价格条件。",
            status=current,
            notify=False,
            metadata=metadata,
        )

    if current == "NO_DATA":
        return MonitorItem(
            fingerprint=fingerprint,
            section="price",
            priority="P1" if previous != "NO_DATA" else "P2",
            target_id=target_id,
            name=name,
            title=f"{label}：行情不可用",
            why_now="有效行情本次缺失，需要确认代码、交易状态或行情源。",
            status=current,
            needs_human_review=True,
            notify=previous != "NO_DATA",
            metadata=metadata,
        )

    if previous == "NO_DATA":
        if current == "FAR":
            return MonitorItem(
                fingerprint=fingerprint,
                section="price",
                priority="P2",
                target_id=target_id,
                name=name,
                title=f"{label}：行情恢复",
                why_now="行情已恢复，当前价格条件未达到。",
                status=current,
                notify=True,
                resolved=True,
                metadata=metadata,
            )

    if current == "FAR":
        if previous in ACTIVE_PRICE_STATES:
            return MonitorItem(
                fingerprint=fingerprint,
                section="price",
                priority="P2",
                target_id=target_id,
                name=name,
                title=f"{label}：条件已解除",
                why_now="价格已离开此前监控条件，本次记录解除状态。",
                status=current,
                notify=True,
                resolved=True,
                metadata=metadata,
            )
        return None

    changed = previous != current
    if current == "TRIGGERED":
        priority = "P0" if changed else "P2"
        why_now = (
            "价格条件本次达到；仍需核验经营条件与 thesis 红线，不构成买卖结论。"
            if changed
            else "价格条件持续满足；经营条件与 thesis 红线仍需独立核验。"
        )
    elif current in {"WARN", "NEAR"}:
        priority = "P1" if changed else "P2"
        condition = "警示线" if current == "WARN" else "边界"
        why_now = (
            f"价格本次进入{condition}监控状态；仍需独立核验经营事实。"
            if changed
            else f"价格持续处于{condition}监控状态，无需重复通知。"
        )
    else:
        priority = "P2"
        why_now = message or "价格状态已记录。"

    return MonitorItem(
        fingerprint=fingerprint,
        section="price",
        priority=priority,
        target_id=target_id,
        name=name,
        title=f"{label}：{current}",
        why_now=message or why_now,
        status=current,
        notify=changed,
        metadata=metadata,
    )


def classify_event(event: dict[str, Any], today: date) -> tuple[str, int | None]:
    if event.get("done"):
        return "DONE", None
    raw_date = str(event.get("date") or "").strip()
    if not raw_date:
        return "OPEN", None
    try:
        event_date = datetime.strptime(raw_date, "%Y-%m-%d").date()
    except ValueError:
        return "OPEN", None
    days = (event_date - today).days
    if days < 0:
        return "OVERDUE", days
    if days == 0:
        return "TODAY", days
    if days <= 7:
        return "UPCOMING_7D", days
    if days <= 14:
        return "UPCOMING_14D", days
    return "FUTURE", days


def event_state_key(target: dict[str, Any], event: dict[str, Any]) -> str:
    return _fingerprint(
        "event",
        target.get("id"),
        event.get("date"),
        event.get("type"),
        event.get("label"),
    )


def event_item(
    target: dict[str, Any],
    event: dict[str, Any],
    *,
    previous: str | None,
    current: str,
    days: int | None,
) -> MonitorItem | None:
    if current == "DONE":
        return None

    target_id = str(target.get("id", ""))
    name = str(target.get("name") or target_id)
    event_type = str(event.get("type") or "复检")
    label = str(event.get("label") or event_type)
    section = "disclosures" if event_type in FINANCIAL_EVENT_TYPES else "other"
    fingerprint = event_state_key(target, event)
    metadata = {
        "previous_status": previous,
        "current_status": current,
        "date": event.get("date"),
        "days": days,
        "event_type": event_type,
        "note": event.get("note", ""),
    }

    if current == "FUTURE":
        if previous in ACTIVE_EVENT_STATES:
            return MonitorItem(
                fingerprint=fingerprint,
                section=section,
                priority="P2",
                target_id=target_id,
                name=name,
                title=f"{label}：提醒已解除",
                why_now="事件已不在当前提醒窗口，本次记录解除状态。",
                status=current,
                notify=True,
                resolved=True,
                metadata=metadata,
            )
        return None

    changed = previous != current
    if current in {"OVERDUE", "TODAY"}:
        priority = "P0"
        timing = "已逾期" if current == "OVERDUE" else "今天到期"
    elif current in {"UPCOMING_7D", "UPCOMING_14D"}:
        priority = "P1" if changed else "P2"
        timing = f"{days} 天后到期"
    else:
        priority = "P1" if changed else "P2"
        timing = "日期缺失或格式异常"

    needs_human_review = current == "OPEN"
    return MonitorItem(
        fingerprint=fingerprint,
        section=section,
        priority=priority,
        target_id=target_id,
        name=name,
        title=f"{label}：{timing}",
        why_now=f"登记事件状态为{timing}，需按备注核验；监控本身不作投资决定。",
        status=current,
        needs_human_review=needs_human_review,
        notify=changed,
        metadata=metadata,
    )

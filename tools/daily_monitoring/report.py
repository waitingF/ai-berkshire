"""Render and atomically persist the price monitor."""

from __future__ import annotations

import json
import math
import os
from dataclasses import asdict, replace
from datetime import date
from pathlib import Path
from typing import Any, Iterable

from .models import MonitorItem, ReportPaths, RunResult
from .transitions import PRIORITY_RANK


def price_result(result: RunResult) -> RunResult:
    """Exclude retired monitoring data, including when rendering old snapshots."""
    def included(item: MonitorItem) -> bool:
        return item.section == "price" or item.metadata.get("service") == "quotes"

    health = tuple(row for row in result.source_health if row.source == "quotes")
    return replace(
        result,
        status="DEGRADED" if any(row.status not in {"OK", "RECOVERED"} for row in health) else "OK",
        items=tuple(item for item in result.items if included(item)),
        notification_items=tuple(item for item in result.notification_items if included(item)),
        source_health=health,
    )


def _is_above_price(item: MonitorItem) -> bool:
    return item.section == "price" and item.metadata.get("direction") == "above"


def _sorted_items(items: Iterable[MonitorItem]) -> list[MonitorItem]:
    def sort_key(item: MonitorItem) -> tuple:
        gap = _price_gap_ratio(item)
        return (
            -PRIORITY_RANK.get(item.priority, -1),
            -(gap if gap is not None else -1),
            item.name.casefold(),
            item.title.casefold(),
            item.fingerprint,
        )

    return sorted(items, key=sort_key)


def _summary(result: RunResult) -> str:
    changed = [
        item
        for item in result.items
        if item.notify
        and not item.resolved
        and not _is_above_price(item)
        and not (item.section == "price" and item.status == "WARN")
    ]
    p0 = sum(item.priority == "P0" for item in changed)
    p1 = sum(item.priority == "P1" for item in changed)
    prices = sum(item.section == "price" for item in changed)
    errors = sum(health.status not in {"OK", "RECOVERED"} for health in result.source_health)
    return f"P0 {p0} · P1 {p1} · 新增价格 {prices} · 异常 {errors}"


def _as_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _format_price(value: Any) -> str:
    number = _as_number(value)
    return f"{number:.2f}" if number is not None else "-"


def _price_condition(metadata: dict[str, Any]) -> str:
    low = _as_number(metadata.get("low"))
    high = _as_number(metadata.get("high"))
    direction = metadata.get("direction", "range")
    if direction == "below" and high is not None:
        return f"≤ {high:.2f}"
    if direction == "above" and low is not None:
        return f"≥ {low:.2f}"
    if low is not None and high is not None:
        return f"[{low:.2f}, {high:.2f}]"
    if low is not None:
        return f"≥ {low:.2f}"
    if high is not None:
        return f"≤ {high:.2f}"
    return "-"


def _price_gap_ratio(item: MonitorItem) -> float | None:
    """Use the trigger boundary for both display and sorting, including P0 rows."""
    price = _as_number(item.metadata.get("price"))
    low = _as_number(item.metadata.get("low"))
    high = _as_number(item.metadata.get("high"))
    direction = item.metadata.get("direction", "range")
    boundary = None
    if direction == "below":
        boundary = high
    elif direction == "above":
        boundary = low
    else:
        boundary = high if high is not None else low
    if price is None or price <= 0 or boundary is None or boundary <= 0:
        return None
    return abs(price - boundary) / boundary


def _price_gap(item: MonitorItem) -> str:
    gap = _price_gap_ratio(item)
    return f"{gap:.1%}" if gap is not None else "-"


def _markdown_cell(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", "<br>")


def _target_name(item: MonitorItem) -> str:
    link = str(item.metadata.get("research_link") or "").strip()
    if not link:
        return item.name
    label = (
        item.name.replace("\\", "\\\\").replace("[", "\\[").replace("]", "\\]")
    )
    return f"[{label}]({link})"


def _render_price_table(items: Iterable[MonitorItem]) -> list[str]:
    visible = [
        item
        for item in items
        if item.status != "WARN" and not _is_above_price(item)
    ]
    lines = [
        "> 价格优先级：P0=达到研究复核条件；P1=距对应边界≤5%或行情待核验；P2=尚未接近或条件已解除；-=未登记价格区间，不评级。展示全部已登记标的，上涨警戒线不参与。",
        "> 排序：P0 → P1 → P2 → 未评级，同级按距边界百分比从大到小；距离=|现价−触发边界|÷触发边界，区间条件取上界。缺失距离排同级末尾，同一标的多个价格区间分别展示。优先级只表示复核紧迫度，不代表交易信号。",
        "> 最新研究报告日期仅比较标的已登记的本地报告；优先取报告中的日期标注，其次取文件名，无法判定显示 -。",
        "",
    ]
    if not visible:
        lines.extend(["无已登记标的的价格监控记录。", ""])
        return lines
    lines.extend(
        [
            "| 优先级 | 标的 | 最新研究报告日期 | 市场 | 监控区间 | 条件 | 现价 | 距边界 | 状态 |",
            "|---|---|---|---|---|---:|---:|---:|---|",
        ]
    )
    for item in visible:
        metadata = item.metadata
        status = "未登记价格区间" if item.status == "NO_ZONE" else item.status
        if item.resolved:
            status += "（已解除）"
        elif item.needs_human_review:
            status += "（待人工确认）"
        cells = (
            item.priority,
            _target_name(item),
            metadata.get("research_date") or "-",
            metadata.get("market") or "-",
            metadata.get("zone_label") or item.title,
            _price_condition(metadata),
            _format_price(metadata.get("price")),
            _price_gap(item),
            status,
        )
        lines.append("| " + " | ".join(_markdown_cell(cell) for cell in cells) + " |")
    lines.append("")
    return lines


def render_markdown(result: RunResult, *, run_date: date | None = None) -> str:
    result = price_result(result)
    day = run_date or date.today()
    health = "、".join(
        f"{row.source}={row.status}" + (f"（{row.safe_message}）" if row.safe_message else "")
        for row in result.source_health
    ) or "无外部数据源"
    lines = [
        "# 每日监控 · 价格监控",
        "",
        f"**数据截止日**：{day.isoformat()}（Asia/Shanghai）",
        f"**运行状态**：{result.status}",
        f"**摘要**：{_summary(result)}",
        f"**数据源状态**：{health}",
        "",
        "> 根据已登记价格区间与腾讯行情快照更新；优先级表示研究复核紧迫度，不代表交易信号。",
        "",
    ]
    lines.extend(["## 一、价格监控", ""])
    rows = _sorted_items(item for item in result.items if item.section == "price")
    lines.extend(_render_price_table(rows))
    lines.extend(
        [
            "---",
            "",
            "价格达到条件只触发研究复核。",
            "本报告用于学习和研究，不构成投资建议，也不会自动作出买卖或仓位结论。",
            "",
        ]
    )
    return "\n".join(lines)


def _json_value(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, tuple):
        return [_json_value(item) for item in value]
    if isinstance(value, list):
        return [_json_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _json_value(item) for key, item in value.items()}
    return value


def report_payload(result: RunResult, *, run_date: date) -> dict[str, Any]:
    result = price_result(result)
    return {
        "schema": 1,
        "date": run_date.isoformat(),
        "timezone": "Asia/Shanghai",
        "status": result.status,
        "summary": _summary(result),
        "items": [
            _json_value(asdict(item))
            for item in _sorted_items(result.items)
            if not _is_above_price(item)
        ],
        "notification_items": [
            item.fingerprint
            for item in result.notification_items
            if not _is_above_price(item)
        ],
        "source_health": [_json_value(asdict(row)) for row in result.source_health],
    }


def _write_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    try:
        with temporary.open("w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(path)
    finally:
        if temporary.exists():
            temporary.unlink()


def write_reports(
    result: RunResult, report_dir: str | Path, *, run_date: date | None = None
) -> ReportPaths:
    day = run_date or date.today()
    directory = Path(report_dir)
    paths = ReportPaths(
        dated=directory / f"daily-monitor-{day:%Y%m%d}.md",
        latest=directory / "daily-monitor-latest.md",
        latest_json=directory / "daily-monitor-latest.json",
    )
    markdown = render_markdown(result, run_date=day)
    payload = json.dumps(
        report_payload(result, run_date=day), ensure_ascii=False, indent=2
    ) + "\n"
    _write_atomic(paths.dated, markdown)
    _write_atomic(paths.latest, markdown)
    _write_atomic(paths.latest_json, payload)
    return paths

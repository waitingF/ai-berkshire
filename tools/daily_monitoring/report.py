"""Render and atomically persist the unified three-section daily monitor."""

from __future__ import annotations

import json
import os
from dataclasses import asdict
from datetime import date
from pathlib import Path
from typing import Any, Iterable

from .models import MonitorItem, ReportPaths, RunResult
from .transitions import PRIORITY_RANK


SECTION_HEADINGS = (
    ("price", "## 一、价格监控"),
    ("disclosures", "## 二、财报与正式披露监控"),
    ("other", "## 三、其他监控"),
)
SECTION_ORDER = {name: index for index, (name, _) in enumerate(SECTION_HEADINGS)}


def _sorted_items(items: Iterable[MonitorItem]) -> list[MonitorItem]:
    return sorted(
        items,
        key=lambda item: (
            -PRIORITY_RANK.get(item.priority, -1),
            item.name.casefold(),
            item.title.casefold(),
            item.fingerprint,
        ),
    )


def _workflow_owners(items: Iterable[MonitorItem]) -> set[str]:
    owners: set[str] = set()
    selected: dict[str, MonitorItem] = {}
    for item in items:
        if not item.next_workflow:
            continue
        current = selected.get(item.target_id)
        candidate_key = (
            PRIORITY_RANK.get(item.priority, -1),
            -SECTION_ORDER.get(item.section, 99),
        )
        current_key = (
            PRIORITY_RANK.get(current.priority, -1),
            -SECTION_ORDER.get(current.section, 99),
        ) if current else (-1, -99)
        if current is None or candidate_key > current_key:
            selected[item.target_id] = item
    owners.update(item.fingerprint for item in selected.values())
    return owners


def _summary(result: RunResult) -> str:
    changed = [item for item in result.items if item.notify and not item.resolved]
    p0 = sum(item.priority == "P0" for item in changed)
    p1 = sum(item.priority == "P1" for item in changed)
    prices = sum(item.section == "price" for item in changed)
    disclosures = sum(item.section == "disclosures" for item in changed)
    errors = sum(health.status not in {"OK", "RECOVERED"} for health in result.source_health)
    return f"P0 {p0} · P1 {p1} · 新增价格 {prices} · 新增披露 {disclosures} · 异常 {errors}"


def _as_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number == number else None


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


def _price_gap(item: MonitorItem) -> str:
    if item.status in {"TRIGGERED", "WARN"}:
        price = _as_number(item.metadata.get("price"))
        low = _as_number(item.metadata.get("low"))
        direction = item.metadata.get("direction", "range")
        if (
            direction == "range"
            and price is not None
            and low is not None
            and low > 0
            and price < low
        ):
            return f"低于下界 {(low - price) / low:.1%}"
        return "区间内"
    price = _as_number(item.metadata.get("price"))
    low = _as_number(item.metadata.get("low"))
    high = _as_number(item.metadata.get("high"))
    direction = item.metadata.get("direction", "range")
    boundary = None
    if direction == "below":
        boundary = high
    elif direction == "above":
        boundary = low
    elif price is not None:
        if low is not None and price < low:
            boundary = low
        elif high is not None and price > high:
            boundary = high
        else:
            boundary = low if high is None else high
    if price is None or boundary is None or boundary <= 0:
        return "-"
    return f"{abs(price - boundary) / boundary:.1%}"


def _markdown_cell(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", "<br>")


def _render_price_table(items: Iterable[MonitorItem]) -> list[str]:
    visible = [item for item in items if item.priority != "P2"]
    lines = [
        "> 价格优先级：P0=区间内或低于区间；P1=高于区间上界且距上界≤5%；P2 不展示。`above` 风险警戒线保留原方向语义。优先级只表示价格距离，不代表交易信号。",
        "",
    ]
    if not visible:
        lines.extend(["无 P0/P1 价格事项（P2 已隐藏）。", ""])
        return lines
    lines.extend(
        [
            "| 优先级 | 标的 | 市场 | 监控区间 | 条件 | 现价 | 距边界 | 状态 |",
            "|---|---|---|---|---:|---:|---:|---|",
        ]
    )
    for item in visible:
        metadata = item.metadata
        status = item.status
        if item.resolved:
            status += "（已解除）"
        elif item.needs_human_review:
            status += "（待人工确认）"
        cells = (
            item.priority,
            item.name,
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


def _item_date(item: MonitorItem) -> str:
    return str(item.metadata.get("published_at") or item.metadata.get("date") or "-")


def _item_evidence(item: MonitorItem) -> str:
    if item.verified_facts:
        rows = []
        for fact in item.verified_facts:
            page = f"，第 {fact.page} 页" if fact.page else ""
            rows.append(
                f"{fact.fact}（{fact.confidence}{page}；[正式来源]({fact.official_url})）"
            )
        return "<br>".join(rows)
    if item.source_urls:
        return "<br>".join(
            f"[正式来源{index if len(item.source_urls) > 1 else ''}]({url})"
            for index, url in enumerate(item.source_urls, start=1)
        )
    return "-"


def _item_workflow(item: MonitorItem, *, show_workflow: bool) -> str:
    if not show_workflow or not item.next_workflow:
        return "-"
    return f"`{item.next_workflow} {item.target_id}`"


def _item_notes(item: MonitorItem) -> str:
    notes = []
    metadata_note = str(item.metadata.get("note") or "").strip()
    if metadata_note:
        notes.append(metadata_note)
    notes.extend(item.limitations)
    if item.resolved:
        notes.append("已解除")
    if item.needs_human_review:
        notes.append("待人工确认")
    return "<br>".join(notes) or "-"


def _render_disclosure_table(
    items: Iterable[MonitorItem], *, workflow_owners: set[str]
) -> list[str]:
    lines = [
        "| 优先级 | 标的 | 披露/事项 | 日期 | 状态 | 为什么现在 | 核验事实/正式来源 | 下一流程 | 备注 |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for item in items:
        cells = (
            item.priority,
            item.name,
            item.title,
            _item_date(item),
            item.status,
            item.why_now,
            _item_evidence(item),
            _item_workflow(item, show_workflow=item.fingerprint in workflow_owners),
            _item_notes(item),
        )
        lines.append("| " + " | ".join(_markdown_cell(cell) for cell in cells) + " |")
    lines.append("")
    return lines


def _render_other_table(
    items: Iterable[MonitorItem], *, workflow_owners: set[str]
) -> list[str]:
    lines = [
        "| 优先级 | 标的/数据源 | 事项 | 日期 | 状态 | 为什么现在 | 下一流程 | 备注 |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for item in items:
        cells = (
            item.priority,
            item.name,
            item.title,
            _item_date(item),
            item.status,
            item.why_now,
            _item_workflow(item, show_workflow=item.fingerprint in workflow_owners),
            _item_notes(item),
        )
        lines.append("| " + " | ".join(_markdown_cell(cell) for cell in cells) + " |")
    lines.append("")
    return lines


def render_markdown(result: RunResult, *, run_date: date | None = None) -> str:
    day = run_date or date.today()
    workflow_owners = _workflow_owners(result.items)
    health = "、".join(
        f"{row.source}={row.status}" + (f"（{row.safe_message}）" if row.safe_message else "")
        for row in result.source_health
    ) or "无外部数据源"
    lines = [
        "# 每日监控",
        "",
        f"**数据截止日**：{day.isoformat()}（Asia/Shanghai）",
        f"**运行状态**：{result.status}",
        f"**摘要**：{_summary(result)}",
        f"**数据源状态**：{health}",
        "",
        "> 价格条件、正式披露与其他研究缺口在同一份报告中展示；优先级表示研究处理顺序，不代表交易信号。",
        "",
    ]
    for section, heading in SECTION_HEADINGS:
        lines.extend([heading, ""])
        rows = _sorted_items(item for item in result.items if item.section == section)
        if not rows:
            lines.extend(["无新增或持续事项。", ""])
            continue
        if section == "price":
            lines.extend(_render_price_table(rows))
            continue
        if section == "disclosures":
            lines.extend(_render_disclosure_table(rows, workflow_owners=workflow_owners))
            continue
        lines.extend(_render_other_table(rows, workflow_owners=workflow_owners))
    lines.extend(
        [
            "---",
            "",
            "价格达到条件只触发研究复核；正式披露的模型判断也只用于研究分流。",
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
    return {
        "schema": 1,
        "date": run_date.isoformat(),
        "timezone": "Asia/Shanghai",
        "status": result.status,
        "summary": _summary(result),
        "items": [_json_value(asdict(item)) for item in _sorted_items(result.items)],
        "notification_items": [item.fingerprint for item in result.notification_items],
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

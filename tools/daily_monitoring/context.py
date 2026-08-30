"""Build minimal target context and detect local research completeness gaps."""

from __future__ import annotations

import hashlib
import os
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import quote

from .models import MonitorItem


RELEVANT_TERMS = (
    "红线",
    "假设",
    "健康度",
    "下次",
    "关注",
    "复检",
    "现金流",
    "估值",
)
PRICE_PATTERN = re.compile(
    r"(?:"
    r"(?:价格|价位|港元|美元|元|HK\$|US\$|\$)[^\n]{0,40}"
    r"\d+(?:\.\d+)?\s*(?:--|[-–—~至])\s*\d+(?:\.\d+)?"
    r"|"
    r"\d+(?:\.\d+)?\s*(?:--|[-–—~至])\s*\d+(?:\.\d+)?\s*"
    r"(?:港元|美元|元|HK\$|US\$|\$)"
    r")",
    re.IGNORECASE,
)
DATE_PATTERN = re.compile(r"\b(20\d{2}-\d{2}-\d{2})\b")
REPORT_DATE_LABEL_PATTERN = re.compile(
    r"数据截止(?:日|日期)?|研究日期|报告日期|更新日期|最后更新|财报发布日期|发布日期"
)
SEPARATED_DATE_PATTERN = re.compile(
    r"(?<!\d)(20\d{2})(?:-|/|\.|年)(\d{1,2})(?:-|/|\.|月)(\d{1,2})日?(?!\d)"
)
COMPACT_DATE_PATTERN = re.compile(r"(?<!\d)(20\d{2})(\d{2})(\d{2})(?!\d)")
NEXT_CHECK_PATTERN = re.compile(r"下次(?:正式)?(?:检查|复检|动作)|复检(?:日|时间|节点)")
CLOSED_LEDGER_STATES = ("已关闭", "已完成", "命中", "未命中", "已复盘")


@dataclass(frozen=True)
class ResearchContext:
    target_id: str
    text: str
    source_paths: tuple[str, ...]
    limitations: tuple[str, ...] = ()


def _safe_local_path(root: Path, relative: str) -> tuple[Path | None, str | None]:
    root_resolved = root.resolve()
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root_resolved)
    except ValueError:
        return None, f"本地链接越界，已拒绝读取: {relative}"
    return candidate, None


def _target_aliases(target: dict[str, Any]) -> tuple[str, ...]:
    aliases = {
        str(target.get("id") or "").strip(),
        str(target.get("name") or "").strip(),
    }
    for code in (target.get("codes") or {}).values():
        value = str(code)
        aliases.add(value)
        aliases.add(value[2:])
    return tuple(sorted((alias for alias in aliases if alias), key=len, reverse=True))


def _matching_rows(text: str, aliases: Iterable[str]) -> str:
    matched = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("|"):
            cells = [cell.strip() for cell in stripped.strip("|").split("|")]
            identity_cells = cells[:2]
            is_match = any(
                alias in cell for alias in aliases for cell in identity_cells
            )
        else:
            is_match = any(stripped.startswith(alias) for alias in aliases)
        if is_match:
            matched.append(line.strip())
    return "\n".join(matched)


def _select_relevant_text(text: str, aliases: Iterable[str]) -> str:
    aliases_tuple = tuple(aliases)
    blocks = re.split(r"\n\s*\n", text)
    selected: list[str] = []
    for block in blocks:
        stripped = block.strip()
        if not stripped:
            continue
        if stripped.startswith("# ") or any(
            term in stripped for term in (*RELEVANT_TERMS, *aliases_tuple)
        ):
            selected.append(stripped)
    return "\n\n".join(selected)


def _candidate_target_files(root: Path, target: dict[str, Any]) -> list[Path]:
    files: list[Path] = []
    for relative in target.get("links") or []:
        candidate, _ = _safe_local_path(root, str(relative))
        if candidate and candidate.is_file() and candidate.suffix.lower() == ".md":
            files.append(candidate)
    reports = root / "reports"
    for directory_name in (str(target.get("id") or ""), str(target.get("name") or "")):
        directory = reports / directory_name
        if directory.is_dir():
            files.extend(directory.rglob("*-thesis*.md"))
    return list(dict.fromkeys(path.resolve() for path in files))


def _dates_in(value: str) -> list[date]:
    dates: list[date] = []
    for pattern in (SEPARATED_DATE_PATTERN, COMPACT_DATE_PATTERN):
        for match in pattern.finditer(value):
            try:
                dates.append(date(*(int(part) for part in match.groups())))
            except ValueError:
                continue
    return dates


def _report_recency(path: Path) -> date:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        text = ""
    labeled_dates = [
        parsed
        for line in text.splitlines()
        if REPORT_DATE_LABEL_PATTERN.search(line)
        for parsed in _dates_in(line)
    ]
    if labeled_dates:
        return max(labeled_dates)
    filename_dates = _dates_in(path.stem)
    return max(filename_dates, default=date.min)


def primary_research_link(
    root: str | Path,
    report_dir: str | Path,
    target: dict[str, Any],
) -> str | None:
    """Return a report-relative link to the most current configured report."""
    root_path = Path(root).resolve()
    best_path: Path | None = None
    best_recency = date.min
    for relative_value in target.get("links") or []:
        candidate, error = _safe_local_path(root_path, str(relative_value))
        if error or candidate is None or not candidate.is_file():
            continue
        if candidate.suffix.lower() != ".md":
            continue
        recency = _report_recency(candidate)
        if best_path is None or recency > best_recency:
            best_path = candidate
            best_recency = recency
    if best_path is None:
        return None
    relative = os.path.relpath(best_path, start=Path(report_dir).resolve())
    return quote(Path(relative).as_posix(), safe="/-._~")


def build_context(
    root: str | Path, target: dict[str, Any], *, max_chars: int = 16_000
) -> ResearchContext:
    root_path = Path(root).resolve()
    aliases = _target_aliases(target)
    sections: list[str] = []
    source_paths: list[str] = []
    limitations: list[str] = []

    for filename, label in (
        ("reports/重点标的看板.md", "重点标的看板"),
        ("reports/标的跟踪表.md", "标的跟踪表"),
    ):
        path = root_path / filename
        if not path.is_file():
            limitations.append(f"缺少 {filename}")
            continue
        matched = _matching_rows(path.read_text(encoding="utf-8"), aliases)
        if matched:
            sections.append(f"## {label}\n{matched}")
            source_paths.append(filename)

    for relative in target.get("links") or []:
        candidate, error = _safe_local_path(root_path, str(relative))
        if error:
            limitations.append(error)
        elif candidate is not None and not candidate.is_file():
            limitations.append(f"本地链接不存在: {relative}")

    for path in _candidate_target_files(root_path, target):
        relative = path.relative_to(root_path).as_posix()
        selected = _select_relevant_text(path.read_text(encoding="utf-8"), aliases)
        if selected:
            sections.append(f"## {relative}\n{selected}")
            source_paths.append(relative)

    text = "\n\n".join(sections)
    if len(text) > max_chars:
        text = text[:max_chars]
        limitations.append(f"研究上下文截断为 {max_chars} 字符")
    return ResearchContext(
        target_id=str(target.get("id") or ""),
        text=text,
        source_paths=tuple(dict.fromkeys(source_paths)),
        limitations=tuple(limitations),
    )


def _gap_fingerprint(gap_type: str, target_id: str, evidence: str) -> str:
    normalized = re.sub(r"\s+", " ", evidence).strip()
    payload = f"{gap_type}\0{target_id}\0{normalized}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _gap_item(
    gap_type: str,
    target_id: str,
    name: str,
    title: str,
    why_now: str,
    evidence_path: str,
    *,
    priority: str = "P1",
) -> MonitorItem:
    return MonitorItem(
        fingerprint=_gap_fingerprint(gap_type, target_id, evidence_path),
        section="other",
        priority=priority,
        target_id=target_id,
        name=name,
        title=title,
        why_now=why_now,
        status="GAP",
        needs_human_review=True,
        notify=True,
        metadata={"gap_type": gap_type, "evidence_path": evidence_path},
    )


def _parse_markdown_tables(text: str) -> list[dict[str, str]]:
    lines = text.splitlines()
    rows: list[dict[str, str]] = []
    index = 0
    while index + 1 < len(lines):
        header_line = lines[index].strip()
        separator_line = lines[index + 1].strip()
        if not (header_line.startswith("|") and separator_line.startswith("|")):
            index += 1
            continue
        separator_cells = [cell.strip() for cell in separator_line.strip("|").split("|")]
        if not separator_cells or not all(re.fullmatch(r":?-{3,}:?", cell) for cell in separator_cells):
            index += 1
            continue
        headers = [cell.strip() for cell in header_line.strip("|").split("|")]
        index += 2
        while index < len(lines) and lines[index].strip().startswith("|"):
            values = [cell.strip() for cell in lines[index].strip().strip("|").split("|")]
            if len(values) == len(headers):
                rows.append(dict(zip(headers, values)))
            index += 1
    return rows


def find_completeness_gaps(
    root: str | Path,
    targets: Iterable[dict[str, Any]],
    *,
    today: date,
) -> list[MonitorItem]:
    root_path = Path(root).resolve()
    reports_path = root_path / "reports"
    board_path = reports_path / "重点标的看板.md"
    ledger_path = reports_path / "标的跟踪表.md"
    board_text = board_path.read_text(encoding="utf-8") if board_path.is_file() else ""
    ledger_text = ledger_path.read_text(encoding="utf-8") if ledger_path.is_file() else ""
    gaps: list[MonitorItem] = []

    targets_list = list(targets)
    for target in targets_list:
        target_id = str(target.get("id") or "")
        name = str(target.get("name") or target_id)
        for relative_value in target.get("links") or []:
            relative = str(relative_value)
            candidate, error = _safe_local_path(root_path, relative)
            if error or candidate is None or not candidate.is_file():
                gaps.append(
                    _gap_item(
                        "broken_link",
                        target_id,
                        name,
                        "本地研究链接失效",
                        error or f"配置链接不存在：{relative}",
                        relative,
                    )
                )
                continue
            if candidate.suffix.lower() != ".md":
                continue
            text = candidate.read_text(encoding="utf-8")
            if not target.get("zones") and PRICE_PATTERN.search(text):
                gaps.append(
                    _gap_item(
                        "unregistered_price",
                        target_id,
                        name,
                        "报告含明确价格区间但未登记监控",
                        "需要人工确认并按触发规则登记，未登记即不会自动监控。",
                        relative,
                    )
                )
            if "thesis" in candidate.name.casefold() and not NEXT_CHECK_PATTERN.search(text):
                gaps.append(
                    _gap_item(
                        "missing_next_check",
                        target_id,
                        name,
                        "thesis 缺少下次检查节点",
                        "论文没有可识别的下次检查或复检字段。",
                        relative,
                    )
                )
            if not target.get("events") and NEXT_CHECK_PATTERN.search(text) and DATE_PATTERN.search(text):
                gaps.append(
                    _gap_item(
                        "unregistered_event",
                        target_id,
                        name,
                        "报告含日期化复检节点但未登记事件",
                        "需要人工确认并登记事件，否则不会自动提醒。",
                        relative,
                    )
                )

    if reports_path.is_dir():
        for thesis in reports_path.rglob("*-thesis*.md"):
            company = thesis.parent.name
            relative = thesis.relative_to(root_path).as_posix()
            if company and company not in board_text and thesis.stem not in board_text:
                gaps.append(
                    _gap_item(
                        "board_coverage",
                        company,
                        company,
                        "thesis 未被重点标的看板覆盖",
                        "发现 thesis 文件，但重点标的看板中没有对应公司。",
                        relative,
                    )
                )

    for row in _parse_markdown_tables(ledger_text):
        review_value = row.get("复检日", "")
        match = DATE_PATTERN.search(review_value)
        if not match:
            continue
        try:
            review_date = date.fromisoformat(match.group(1))
        except ValueError:
            continue
        status = row.get("状态", "")
        if review_date >= today or any(token in status for token in CLOSED_LEDGER_STATES):
            continue
        target_id = row.get("ID") or row.get("标的") or "ledger"
        name = re.sub(r"\[([^]]+)]\([^)]*\)", r"\1", row.get("标的", target_id))
        gaps.append(
            _gap_item(
                "overdue_ledger",
                target_id,
                name,
                "台账复检日已过但状态未关闭",
                f"复检日 {review_date.isoformat()}，当前状态：{status or '空'}。",
                f"reports/标的跟踪表.md#{target_id}",
                priority="P0",
            )
        )

    unique: dict[str, MonitorItem] = {}
    for gap in gaps:
        unique.setdefault(gap.fingerprint, gap)
    return sorted(
        unique.values(),
        key=lambda item: ({"P0": 0, "P1": 1, "P2": 2}[item.priority], item.name, item.title),
    )

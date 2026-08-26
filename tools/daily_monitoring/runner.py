"""End-to-end orchestration for deterministic and incremental daily monitoring."""

from __future__ import annotations

import copy
import hashlib
import json
import re
from dataclasses import dataclass, replace
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Mapping
from zoneinfo import ZoneInfo

from .collectors import akshare, cninfo, hkex, sec
from .config import infer_sources, load_targets
from .context import build_context, find_completeness_gaps
from .deepseek import AnalysisRequest, DeepSeekClient
from .disclosures import deduplicate
from .documents import ExtractedDocument, extract_document, prepare_prompt_chunks, temporary_document
from .http import HttpClient, SourceError
from .models import Disclosure, FallbackClue, MonitorItem, RunResult, SourceHealth
from .report import write_reports
from .state import load_state, save_state_atomic
from .transitions import (
    PRIORITY_RANK,
    classify_event,
    event_item,
    event_state_key,
    price_item,
    price_state_key,
)


Collector = Callable[..., list[Disclosure]]
DocumentExtractor = Callable[[Disclosure, dict[str, Any], Any], ExtractedDocument]


@dataclass(frozen=True)
class MonitorOptions:
    root: Path
    triggers_file: Path
    state_file: Path
    report_dir: Path
    today: date
    no_ai: bool = False
    watch: tuple[str, ...] = ()


@dataclass
class MonitorServices:
    quote_provider: Callable[[list[str]], dict[str, dict[str, Any]]]
    collectors: Mapping[str, Collector]
    http: Any
    document_extractor: DocumentExtractor
    deepseek: Any | None
    fallback_provider: Callable[..., list[FallbackClue]] | None = None


FINANCIAL_DISCLOSURE_TYPES = frozenset(
    {"财报", "业绩预告", "10-K", "10-Q", "20-F", "40-F"}
)
DISCLOSURE_MARKETS = {"cninfo": "A", "hkex": "H", "sec": "US", "akshare": "A"}


def _production_quotes(codes: list[str]) -> dict[str, dict[str, Any]]:
    from tools.trigger_scanner import _curl_qq

    result: dict[str, dict[str, Any]] = {}
    for start in range(0, len(codes), 30):
        result.update(_curl_qq(codes[start : start + 30]))
    return result


def _production_extractor(
    disclosure: Disclosure, target: dict[str, Any], http: Any
) -> ExtractedDocument:
    keywords = [
        str(target.get("id") or ""),
        str(target.get("name") or ""),
        "业绩",
        "收入",
        "利润",
        "现金流",
        "风险",
    ]
    with temporary_document(disclosure, http) as path:
        return extract_document(path, keywords)


def production_services(
    *,
    edgar_identity: str | None,
    deepseek_api_key: str | None,
    deepseek_model: str | None = None,
    no_ai: bool = False,
) -> MonitorServices:
    http = HttpClient(edgar_identity=edgar_identity)
    return MonitorServices(
        quote_provider=_production_quotes,
        collectors={"cninfo": cninfo.collect, "hkex": hkex.collect, "sec": sec.collect},
        http=http,
        document_extractor=_production_extractor,
        deepseek=None if no_ai else DeepSeekClient(api_key=deepseek_api_key, model=deepseek_model),
        fallback_provider=akshare.collect_fallback,
    )


def _watched(target: dict[str, Any], patterns: tuple[str, ...]) -> bool:
    if not patterns:
        return True
    identities = {
        value.strip().casefold()
        for value in (
            [str(target.get("id") or ""), str(target.get("name") or "")]
            + [str(code) for code in (target.get("codes") or {}).values()]
        )
        if value.strip()
    }
    return any(pattern.strip().casefold() in identities for pattern in patterns)


def _safe_failure(source: str, exc: Exception) -> str:
    if isinstance(exc, SourceError):
        return exc.safe_message
    return f"{source} 运行失败（{type(exc).__name__}）"


def _failure_fingerprint(source: str, state: str) -> str:
    return hashlib.sha256(f"service\0{source}\0{state}".encode()).hexdigest()


def _service_item(
    source: str, *, recovered: bool, notify: bool, message: str
) -> MonitorItem:
    return MonitorItem(
        fingerprint=_failure_fingerprint(source, "RECOVERED" if recovered else "FAILED"),
        section="other",
        priority="P2" if recovered else "P1",
        target_id=source,
        name=source.upper(),
        title="数据源已恢复" if recovered else "数据源异常",
        why_now=message,
        status="RECOVERED" if recovered else "FAILED",
        needs_human_review=not recovered,
        notify=notify,
        resolved=recovered,
        metadata={"service": source},
    )


def _document_key(disclosure: Disclosure) -> str:
    return f"{disclosure.source}:{disclosure.document_id}"


def _fallback_fingerprint(clue: FallbackClue) -> str:
    payload = f"fallback\0{clue.target_id}\0{clue.title}\0{clue.published_at}"
    return hashlib.sha256(payload.encode()).hexdigest()


def _fallback_item(clue: FallbackClue, *, notify: bool) -> MonitorItem:
    return MonitorItem(
        fingerprint=_fallback_fingerprint(clue),
        section="disclosures",
        priority="P1",
        target_id=clue.target_id,
        name=clue.target_id,
        title=f"备用源线索：{clue.title}",
        why_now=(
            "正式披露源本次失败，AKShare 仅提供待回到正式来源核验的线索；"
            "不得据此形成已验证事实或投资结论。"
        ),
        status="FALLBACK_CLUE",
        source_urls=(clue.url,) if clue.verified and clue.url else (),
        needs_human_review=True,
        limitations=("AKShare 不是一期正式披露依据",),
        notify=notify,
        metadata={
            "kind": "fallback_clue",
            "fallback": True,
            "source": clue.source,
            "market": DISCLOSURE_MARKETS.get(clue.source),
            "published_at": clue.published_at,
        },
    )


def _document_record(disclosure: Disclosure) -> dict[str, Any]:
    return {
        "status": "PENDING_EXTRACTION",
        "target_id": disclosure.target_id,
        "source": disclosure.source,
        "document_id": disclosure.document_id,
        "title": disclosure.title,
        "published_at": disclosure.published_at,
        "document_type": disclosure.document_type,
        "official_url": disclosure.official_url,
        "download_url": disclosure.download_url,
        "source_urls": list(disclosure.source_urls),
        "reported": False,
    }


def _record_disclosure(record: dict[str, Any]) -> Disclosure:
    return Disclosure(
        target_id=str(record["target_id"]),
        source=str(record["source"]),
        document_id=str(record["document_id"]),
        title=str(record["title"]),
        published_at=str(record["published_at"]),
        document_type=str(record["document_type"]),
        official_url=str(record["official_url"]),
        download_url=record.get("download_url"),
        source_urls=tuple(record.get("source_urls") or ()),
    )


def _disclosure_floor(disclosure: Disclosure) -> str:
    return "P0" if disclosure.document_type in FINANCIAL_DISCLOSURE_TYPES else "P1"


def _disclosure_fingerprint(disclosure: Disclosure) -> str:
    payload = f"disclosure\0{disclosure.source}\0{disclosure.document_id}"
    return hashlib.sha256(payload.encode()).hexdigest()


def _disclosure_item(
    disclosure: Disclosure,
    *,
    priority: str,
    why_now: str,
    status: str,
    notify: bool,
    needs_human_review: bool,
    verified_facts=(),
    next_workflow: str | None = None,
    limitations=(),
    thesis_impacts=(),
) -> MonitorItem:
    return MonitorItem(
        fingerprint=_disclosure_fingerprint(disclosure),
        section="disclosures",
        priority=priority,
        target_id=disclosure.target_id,
        name=disclosure.target_id,
        title=disclosure.title,
        why_now=why_now,
        status=status,
        verified_facts=tuple(verified_facts),
        source_urls=disclosure.source_urls,
        next_workflow=next_workflow,
        needs_human_review=needs_human_review,
        limitations=tuple(limitations),
        notify=notify,
        metadata={
            "kind": "official_disclosure",
            "document_type": disclosure.document_type,
            "source": disclosure.source,
            "market": DISCLOSURE_MARKETS.get(disclosure.source),
            "published_at": disclosure.published_at,
            "thesis_impacts": list(thesis_impacts),
        },
    )


def _published_datetime(item: MonitorItem) -> datetime | None:
    value = str(item.metadata.get("published_at") or "").strip()
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        parsed = None
        for pattern in ("%d/%m/%Y %H:%M", "%d/%m/%Y", "%Y/%m/%d %H:%M", "%Y/%m/%d"):
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


def _disclosure_update_topic(item: MonitorItem) -> str:
    title = " ".join(item.title.split())
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


def _is_placeholder_disclosure(item: MonitorItem) -> bool:
    title = " ".join(item.title.casefold().split())
    return "an announcement has just been published by the issuer" in title


def _aggregate_todays_disclosures(
    items: list[MonitorItem], *, today: date
) -> list[MonitorItem]:
    groups: dict[tuple[str, str], list[MonitorItem]] = {}
    untouched: list[MonitorItem] = []
    for item in items:
        if item.metadata.get("kind") != "official_disclosure":
            untouched.append(item)
            continue
        published = _published_datetime(item)
        if published is None or published.date() != today:
            continue
        market = str(item.metadata.get("market") or "").strip()
        if not market:
            untouched.append(item)
            continue
        groups.setdefault((item.target_id, market), []).append(item)

    summaries: list[MonitorItem] = []
    for (target_id, market), rows in groups.items():
        substantive = [item for item in rows if not _is_placeholder_disclosure(item)]
        if substantive:
            rows = substantive
        rows.sort(key=lambda item: (_published_datetime(item), item.fingerprint))
        latest = _published_datetime(rows[-1])
        assert latest is not None
        priority = max(rows, key=lambda item: PRIORITY_RANK[item.priority]).priority
        completed = all(
            item.status == "DONE" and not item.needs_human_review for item in rows
        )
        updates = [
            {
                "summary": _disclosure_update_topic(item),
                "title": item.title,
                "published_at": item.metadata.get("published_at"),
                "priority": item.priority,
                "status": item.status,
                "why_now": item.why_now,
                "source_urls": list(item.source_urls),
                "verified_facts": [
                    {
                        "fact": fact.fact,
                        "official_url": fact.official_url,
                        "page": fact.page,
                        "confidence": fact.confidence,
                    }
                    for fact in item.verified_facts
                ],
                "next_workflow": item.next_workflow,
                "needs_human_review": item.needs_human_review,
                "limitations": list(item.limitations),
                "document_type": item.metadata.get("document_type"),
                "source": item.metadata.get("source"),
                "thesis_impacts": list(item.metadata.get("thesis_impacts") or []),
            }
            for item in rows
        ]
        fingerprint = hashlib.sha256(
            "\0".join(
                ("disclosure-summary", today.isoformat(), target_id, market)
                + tuple(item.fingerprint for item in rows)
            ).encode()
        ).hexdigest()
        summaries.append(
            MonitorItem(
                fingerprint=fingerprint,
                section="disclosures",
                priority=priority,
                target_id=target_id,
                name=rows[0].name,
                title=f"{len(rows)} 项公告更新",
                why_now="；".join(update["summary"] for update in updates),
                status="DONE" if completed else "REVIEW",
                source_urls=tuple(
                    dict.fromkeys(url for item in rows for url in item.source_urls)
                ),
                needs_human_review=not completed,
                notify=any(item.notify for item in rows),
                metadata={
                    "kind": "disclosure_summary",
                    "market": market,
                    "date": today.isoformat(),
                    "published_at": rows[-1].metadata.get("published_at"),
                    "latest_time": latest.isoformat(),
                    "announcement_count": len(rows),
                    "updates": updates,
                },
            )
        )
    return [*untouched, *summaries]


def _cursor_start(source_state: dict[str, Any], today: date) -> date:
    raw = source_state.get("cursor")
    if isinstance(raw, str):
        try:
            return date.fromisoformat(raw)
        except ValueError:
            pass
    return today - timedelta(days=3)


def _find_target(targets: list[dict[str, Any]], target_id: str) -> dict[str, Any] | None:
    return next((target for target in targets if target.get("id") == target_id), None)


def run_monitor(options: MonitorOptions, services: MonitorServices) -> RunResult:
    targets = [
        target
        for target in load_targets(options.triggers_file)
        if _watched(target, options.watch)
    ]
    state = copy.deepcopy(load_state(options.state_file))
    state["updated_at"] = options.today.isoformat()
    items: list[MonitorItem] = []
    source_health: list[SourceHealth] = []
    degraded = False

    codes = sorted(
        {
            str(code)
            for target in targets
            for code in (target.get("codes") or {}).values()
        }
    )
    try:
        quotes = services.quote_provider(codes)
        previous_quote_health = (state["services"].get("quotes") or {}).get("status")
        source_health.append(SourceHealth("quotes", "OK"))
        state["services"]["quotes"] = {"status": "OK", "updated_at": options.today.isoformat()}
        if previous_quote_health == "FAILED":
            items.append(
                _service_item(
                    "quotes",
                    recovered=True,
                    notify=True,
                    message="行情源本次恢复，可继续执行价格条件核验。",
                )
            )
    except Exception as exc:
        quotes = {}
        degraded = True
        message = _safe_failure("quotes", exc)
        previous_quote_health = (state["services"].get("quotes") or {}).get("status")
        source_health.append(SourceHealth("quotes", "FAILED", message))
        state["services"]["quotes"] = {
            "status": "FAILED",
            "updated_at": options.today.isoformat(),
            "safe_message": message,
        }
        items.append(
            _service_item(
                "quotes",
                recovered=False,
                notify=previous_quote_health != "FAILED",
                message=message,
            )
        )

    for target in targets:
        for zone in target.get("zones") or []:
            code = (target.get("codes") or {}).get(zone.get("market"))
            quote = quotes.get(str(code), {})
            price = quote.get("price")
            from tools.trigger_scanner import judge_zone

            current, message = judge_zone(price, zone, near_ratio=0.05)
            key = price_state_key(target, zone)
            previous = (state["price_states"].get(key) or {}).get("status")
            monitor_item = price_item(
                target,
                zone,
                previous=previous,
                current=current,
                price=price,
                message=message,
            )
            if monitor_item:
                items.append(monitor_item)
            state["price_states"][key] = {
                "status": current,
                "updated_at": options.today.isoformat(),
                "price": price,
            }

        for event in target.get("events") or []:
            key = event_state_key(target, event)
            previous = (state["event_states"].get(key) or {}).get("status")
            current, days = classify_event(event, options.today)
            monitor_item = event_item(
                target, event, previous=previous, current=current, days=days
            )
            if monitor_item:
                items.append(monitor_item)
            state["event_states"][key] = {
                "status": current,
                "updated_at": options.today.isoformat(),
            }

    source_targets: dict[str, list[tuple[dict[str, Any], dict[str, Any]]]] = {}
    for target in targets:
        for source, config in infer_sources(target).items():
            if source in services.collectors:
                source_targets.setdefault(source, []).append((target, config))

    all_collected: list[Disclosure] = []
    fallback_state = state["services"].setdefault("akshare_clues", {})
    for source, configured_targets in sorted(source_targets.items()):
        source_state = state["sources"].setdefault(source, {})
        since = _cursor_start(source_state, options.today)
        collected: list[Disclosure] = []
        source_failed = False
        safe_message = None
        failed_targets: list[tuple[dict[str, Any], dict[str, Any]]] = []
        for target, source_config in configured_targets:
            try:
                collected.extend(
                    services.collectors[source](
                        str(target["id"]),
                        source_config,
                        since=since,
                        until=options.today,
                        http=services.http,
                    )
                )
            except Exception as exc:
                source_failed = True
                safe_message = _safe_failure(source, exc)
                failed_targets.append((target, source_config))
        previous_status = source_state.get("status")
        if source_failed:
            degraded = True
            source_health.append(SourceHealth(source, "FAILED", safe_message))
            source_state.update(
                {
                    "status": "FAILED",
                    "updated_at": options.today.isoformat(),
                    "safe_message": safe_message,
                }
            )
            items.append(
                _service_item(
                    source,
                    recovered=False,
                    notify=previous_status != "FAILED",
                    message=safe_message or f"{source} 披露采集失败",
                )
            )
            if source == "cninfo" and services.fallback_provider is not None:
                for target, source_config in failed_targets:
                    try:
                        clues = services.fallback_provider(
                            str(target["id"]),
                            source_config,
                            since=since,
                            until=options.today,
                        )
                    except Exception:
                        clues = []
                    for clue in clues:
                        fingerprint = _fallback_fingerprint(clue)
                        items.append(
                            _fallback_item(clue, notify=fingerprint not in fallback_state)
                        )
                        fallback_state[fingerprint] = {
                            "target_id": clue.target_id,
                            "title": clue.title,
                            "published_at": clue.published_at,
                            "updated_at": options.today.isoformat(),
                        }
        else:
            status = "RECOVERED" if previous_status == "FAILED" else "OK"
            source_health.append(SourceHealth(source, status))
            source_state.update(
                {
                    "status": "OK",
                    "updated_at": options.today.isoformat(),
                    "cursor": options.today.isoformat(),
                }
            )
            source_state.pop("safe_message", None)
            if previous_status == "FAILED":
                items.append(
                    _service_item(
                        source,
                        recovered=True,
                        notify=True,
                        message=f"{source} 正式披露采集本次恢复。",
                    )
                )
        all_collected.extend(collected)

    for document in deduplicate(all_collected):
        state["documents"].setdefault(_document_key(document), _document_record(document))

    target_ids = {str(target["id"]) for target in targets}
    for key in sorted(state["documents"]):
        record = state["documents"][key]
        if record.get("target_id") not in target_ids:
            continue
        if record.get("status") in {"DONE", "OCR_REQUIRED"}:
            continue
        disclosure = _record_disclosure(record)
        target = _find_target(targets, disclosure.target_id)
        if target is None:
            continue
        was_reported = bool(record.get("reported"))
        floor = _disclosure_floor(disclosure)
        try:
            extracted = services.document_extractor(disclosure, target, services.http)
        except Exception as exc:
            failure = (
                exc.safe_message if isinstance(exc, SourceError) else type(exc).__name__
            )
            extracted = ExtractedDocument(
                status="EXTRACTION_FAILED",
                sha256="",
                pages_used=(),
                chunks=(),
                limitation=f"正文提取失败（{failure}）",
            )

        record["sha256"] = extracted.sha256 or None
        record["pages_used"] = list(extracted.pages_used)
        record["last_attempt"] = options.today.isoformat()
        if extracted.status == "OCR_REQUIRED":
            record["status"] = "OCR_REQUIRED"
            record["reported"] = True
            degraded = True
            items.append(
                _disclosure_item(
                    disclosure,
                    priority=floor,
                    why_now="正式披露未提取到可用文本，一期不执行 OCR，需要人工核验。",
                    status="OCR_REQUIRED",
                    notify=not was_reported,
                    needs_human_review=True,
                    limitations=(extracted.limitation or "需要 OCR",),
                )
            )
            continue
        if extracted.status != "EXTRACTED":
            record["status"] = "PENDING_EXTRACTION"
            record["reported"] = True
            degraded = True
            items.append(
                _disclosure_item(
                    disclosure,
                    priority=floor,
                    why_now="正式披露正文暂未成功提取，保留待重试状态。",
                    status="PENDING_EXTRACTION",
                    notify=not was_reported,
                    needs_human_review=True,
                    limitations=(extracted.limitation or "正文提取失败",),
                )
            )
            continue

        if options.no_ai or services.deepseek is None:
            record["status"] = "PENDING_AI"
            record["reported"] = True
            if not options.no_ai:
                degraded = True
            items.append(
                _disclosure_item(
                    disclosure,
                    priority=floor,
                    why_now="已取得正式披露并完成正文提取；AI 增量判断尚未执行。",
                    status="PENDING_AI",
                    notify=not was_reported,
                    needs_human_review=True,
                    limitations=("AI 已显式关闭" if options.no_ai else "未配置 DeepSeek",),
                )
            )
            continue

        context = build_context(options.root, target)
        analysis = services.deepseek.analyze(
            AnalysisRequest(
                target_id=disclosure.target_id,
                name=str(target.get("name") or disclosure.target_id),
                priority_floor=floor,
                increment_title=disclosure.title,
                increment_type=disclosure.document_type,
                official_urls=disclosure.source_urls,
                prompt_chunks=prepare_prompt_chunks(extracted.chunks),
                context=context,
            )
        )
        record["reported"] = True
        if analysis.status != "OK":
            record["status"] = "PENDING_AI"
            degraded = True
        else:
            record["status"] = "DONE"
            record["completed_at"] = options.today.isoformat()
        items.append(
            _disclosure_item(
                disclosure,
                priority=analysis.priority,
                why_now=analysis.why_now,
                status=record["status"],
                notify=not was_reported,
                needs_human_review=analysis.needs_human_review,
                verified_facts=analysis.verified_facts,
                next_workflow=analysis.next_workflow,
                limitations=(*analysis.limitations, *context.limitations),
                thesis_impacts=analysis.thesis_impacts,
            )
        )

    previous_gaps = state["completeness"]
    if options.watch:
        scoped_previous_gaps = {
            fingerprint: gap
            for fingerprint, gap in previous_gaps.items()
            if str(gap.get("target_id") or "") in target_ids
        }
        preserved_gaps = {
            fingerprint: gap
            for fingerprint, gap in previous_gaps.items()
            if fingerprint not in scoped_previous_gaps
        }
    else:
        scoped_previous_gaps = previous_gaps
        preserved_gaps = {}
    current_gaps: dict[str, dict[str, Any]] = {}
    detected_gaps = find_completeness_gaps(options.root, targets, today=options.today)
    if options.watch:
        detected_gaps = [gap for gap in detected_gaps if gap.target_id in target_ids]
    for gap in detected_gaps:
        is_new = gap.fingerprint not in scoped_previous_gaps
        items.append(replace(gap, notify=is_new))
        current_gaps[gap.fingerprint] = {
            "target_id": gap.target_id,
            "name": gap.name,
            "title": gap.title,
            "priority": gap.priority,
            "updated_at": options.today.isoformat(),
        }
    for fingerprint, old_gap in scoped_previous_gaps.items():
        if fingerprint in current_gaps:
            continue
        items.append(
            MonitorItem(
                fingerprint=fingerprint,
                section="other",
                priority="P2",
                target_id=str(old_gap.get("target_id") or "research-gap"),
                name=str(old_gap.get("name") or old_gap.get("target_id") or "研究覆盖"),
                title=f"{old_gap.get('title') or '研究缺口'}：已解除",
                why_now="此前研究覆盖缺口本次未再出现，记录为已解除。",
                status="RESOLVED",
                notify=True,
                resolved=True,
            )
        )
    state["completeness"] = {**preserved_gaps, **current_gaps}

    items = _aggregate_todays_disclosures(items, today=options.today)
    notifications = tuple(item for item in items if item.notify)
    provisional = RunResult(
        status="DEGRADED" if degraded else "OK",
        items=tuple(items),
        notification_items=notifications,
        source_health=tuple(source_health),
        next_state=state,
        report_paths=None,
    )
    paths = write_reports(provisional, options.report_dir, run_date=options.today)
    final = replace(provisional, report_paths=paths)
    save_state_atomic(options.state_file, state)
    return final

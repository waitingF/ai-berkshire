"""Run price monitoring without disclosure, AI, event or research-gap scans."""

from __future__ import annotations

import copy
import hashlib
import math
from dataclasses import dataclass, replace
from datetime import date
from pathlib import Path
from typing import Any, Callable

from .config import load_targets
from .context import primary_research_report
from .models import MonitorItem, RunResult, SourceHealth
from .report import write_reports
from .state import load_state, save_state_atomic
from .transitions import price_item, price_state_key


@dataclass(frozen=True)
class MonitorOptions:
    root: Path
    triggers_file: Path
    state_file: Path
    report_dir: Path
    today: date
    watch: tuple[str, ...] = ()


@dataclass
class MonitorServices:
    quote_provider: Callable[[list[str]], dict[str, dict[str, Any]]]


def _production_quotes(codes: list[str]) -> dict[str, dict[str, Any]]:
    from tools.trigger_scanner import _curl_qq

    result: dict[str, dict[str, Any]] = {}
    for start in range(0, len(codes), 30):
        result.update(_curl_qq(codes[start : start + 30]))
    return result


def production_services() -> MonitorServices:
    return MonitorServices(quote_provider=_production_quotes)


def _quote_price(quote: Any) -> float | None:
    price = quote.get("price") if isinstance(quote, dict) else None
    if isinstance(price, bool) or not isinstance(price, (int, float)):
        return None
    return price if math.isfinite(price) and price > 0 else None


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


def run_monitor(options: MonitorOptions, services: MonitorServices) -> RunResult:
    targets = [
        target
        for target in load_targets(options.triggers_file)
        if _watched(target, options.watch)
    ]
    zones_by_target = {
        target["id"]: [zone for zone in target.get("zones") or []
                       if zone.get("dir", "range") != "above"]
        for target in targets
    }
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
        required_codes = {
            str((target.get("codes") or {}).get(zone.get("market")))
            for target in targets
            for zone in zones_by_target[target["id"]]
        } | {
            str(code)
            for target in targets if not zones_by_target[target["id"]]
            for code in (target.get("codes") or {}).values()
        }
        missing = sum(_quote_price(quotes.get(code)) is None for code in required_codes)
        if missing:
            degraded = True
            message = f"{missing}/{len(required_codes)} 个监控代码缺少有效行情；其余有效行情保留。"
    except Exception as exc:
        quotes = {}
        degraded = True
        message = _safe_failure("quotes", exc)

    previous_quote_health = (state["services"].get("quotes") or {}).get("status")
    if degraded:
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
    else:
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

    for target in targets:
        zones = zones_by_target[target["id"]]
        if not zones:
            quote_gap = target.get("quote_unavailable_reason") if not target.get("codes") else None
            label = quote_gap or "未登记价格区间"
            for market, code in (target.get("codes") or {"-": None}).items():
                items.append(MonitorItem(
                    fingerprint=hashlib.sha256(
                        f"no-zone\0{target['id']}\0{market}".encode()
                    ).hexdigest(),
                    section="price", priority="-", target_id=target["id"],
                    name=str(target.get("name") or target["id"]),
                    title=label, status="NO_QUOTE" if quote_gap else "NO_ZONE",
                    why_now=quote_gap or "仅展示行情；未登记有效价格区间，无法判断价格优先级。",
                    metadata={"market": market, "price": _quote_price(quotes.get(str(code))),
                              "zone_label": label},
                ))
        for zone in zones:
            code = (target.get("codes") or {}).get(zone.get("market"))
            price = _quote_price(quotes.get(str(code)))
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

    research_reports = {
        str(target.get("id") or ""): {
            "research_link": selected[0],
            "research_date": selected[1].isoformat() if selected[1] else None,
        }
        for target in targets
        if (
            selected := primary_research_report(
                options.root,
                options.report_dir,
                target,
            )
        )
    }
    items = [
        replace(
            item,
            metadata={**item.metadata, **research_reports[item.target_id]},
        )
        if item.target_id in research_reports
        else item
        for item in items
    ]
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

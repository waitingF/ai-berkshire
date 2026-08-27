"""Load and validate daily-monitor configuration from human-authored triggers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


SUPPORTED_DISCLOSURE_SOURCES = frozenset({"cninfo", "hkex", "sec"})
SUPPORTED_ZONE_DIRECTIONS = frozenset({"below", "range", "above"})


class ConfigError(ValueError):
    """Raised when human-authored monitoring configuration is invalid."""


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def validate_price_zones(target: dict[str, Any]) -> list[str]:
    """Return all price-zone contract violations for one target."""
    target_id = str(target.get("id") or "<unknown>")
    codes = target.get("codes") or {}
    errors: list[str] = []
    by_market: dict[str, list[dict[str, Any]]] = {}

    for zone in target.get("zones") or []:
        if not isinstance(zone, dict):
            errors.append(f"{target_id} 的 zones 中存在非对象条目")
            continue
        label = str(zone.get("label") or "未命名区间")
        market = str(zone.get("market") or "").strip()
        direction = str(zone.get("dir", "range"))
        low = zone.get("low")
        high = zone.get("high")

        if market not in codes:
            errors.append(
                f"{target_id}：zone「{label}」引用市场 {market or '<空>'} 不存在于 codes"
            )
        if direction not in SUPPORTED_ZONE_DIRECTIONS:
            errors.append(f"{target_id}：zone「{label}」dir 非法（{direction}）")
            continue
        if low is not None and not _is_number(low):
            errors.append(f"{target_id}：zone「{label}」low 必须是数字")
        if high is not None and not _is_number(high):
            errors.append(f"{target_id}：zone「{label}」high 必须是数字")
        if _is_number(low) and _is_number(high) and low > high:
            errors.append(f"{target_id}：zone「{label}」low({low}) > high({high})")
        if direction == "below" and high is None:
            errors.append(f"{target_id}：zone「{label}」dir=below 但无 high")
        if direction == "range" and (low is None or high is None):
            errors.append(f"{target_id}：zone「{label}」dir=range 必须同时提供 low/high")
        if direction == "above" and low is None:
            errors.append(f"{target_id}：zone「{label}」dir=above 但无 low")
        if market:
            by_market.setdefault(market, []).append(zone)

    for market, zones in by_market.items():
        downside = [
            zone
            for zone in zones
            if zone.get("dir", "range") in {"below", "range"}
        ]
        warnings = [zone for zone in zones if zone.get("dir", "range") == "above"]
        if len(downside) > 1:
            errors.append(
                f"{target_id} 在同一市场 {market} 只能配置一个下行评估条件（below/range 二选一）"
            )
        if len(warnings) > 1:
            errors.append(
                f"{target_id} 在同一市场 {market} 只能配置一个 above 估值警戒线"
            )
        if len(downside) == 1 and len(warnings) == 1:
            ceiling = downside[0].get("high")
            warning = warnings[0].get("low")
            if _is_number(ceiling) and _is_number(warning) and warning <= ceiling:
                errors.append(
                    f"{target_id} 在市场 {market} 的 above.low({warning}) "
                    f"必须高于下行评估条件 high({ceiling})"
                )

    return errors


def _normalize_cik(value: Any) -> str:
    digits = str(value).strip()
    if not digits.isdigit() or len(digits) > 10:
        raise ConfigError(f"SEC CIK 非法: {value}")
    return digits.zfill(10)


def infer_sources(target: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Infer official disclosure identities from market codes, then apply overrides."""
    inferred: dict[str, dict[str, Any]] = {}
    codes = target.get("codes") or {}

    if code := codes.get("A"):
        code = str(code)
        inferred["cninfo"] = {"stock_code": code[2:], "exchange": code[:2]}
    if code := codes.get("H"):
        inferred["hkex"] = {"stock_code": str(code)[2:].zfill(5)}
    if code := codes.get("US"):
        inferred["sec"] = {"ticker": str(code)[2:].upper()}

    overrides = target.get("disclosure_sources") or {}
    unknown = sorted(set(overrides) - SUPPORTED_DISCLOSURE_SOURCES)
    if unknown:
        raise ConfigError(
            f"{target.get('id', '<unknown>')} 含不支持的披露源: {', '.join(unknown)}"
        )

    for source, override in overrides.items():
        if not isinstance(override, dict):
            raise ConfigError(f"{target.get('id')} 的 {source} 配置必须是对象")
        enabled = override.get("enabled", True)
        if not isinstance(enabled, bool):
            raise ConfigError(f"{target.get('id')} 的 {source}.enabled 必须是布尔值")
        if not enabled:
            inferred.pop(source, None)
            continue
        inferred[source] = {
            **inferred.get(source, {}),
            **{key: value for key, value in override.items() if key != "enabled"},
        }

    if hkex := inferred.get("hkex"):
        stock_code = str(hkex.get("stock_code", "")).strip()
        if not stock_code.isdigit() or len(stock_code) > 5:
            raise ConfigError(f"HKEX 股票代码非法: {stock_code}")
        hkex["stock_code"] = stock_code.zfill(5)

    if cninfo := inferred.get("cninfo"):
        stock_code = str(cninfo.get("stock_code", "")).strip()
        if not stock_code.isdigit() or len(stock_code) != 6:
            raise ConfigError(f"巨潮股票代码非法: {stock_code}")
        exchange = str(cninfo.get("exchange", "")).lower()
        if exchange not in {"sh", "sz", "bj"}:
            raise ConfigError(f"巨潮交易所非法: {exchange}")
        cninfo["stock_code"] = stock_code
        cninfo["exchange"] = exchange

    if sec := inferred.get("sec"):
        if ticker := sec.get("ticker"):
            sec["ticker"] = str(ticker).upper().strip()
        if "cik" in sec:
            sec["cik"] = _normalize_cik(sec["cik"])
        forms = sec.get("forms")
        if forms is not None:
            if not isinstance(forms, list) or not all(
                isinstance(form, str) and form.strip() for form in forms
            ):
                raise ConfigError("SEC forms 必须是非空字符串数组")
            sec["forms"] = [form.strip().upper() for form in forms]

    return inferred


def load_targets(path: str | Path) -> list[dict[str, Any]]:
    """Load trigger targets and validate identities used by daily monitoring."""
    source_path = Path(path)
    try:
        data = json.loads(source_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ConfigError(f"无法读取触发配置 {source_path}: {exc}") from exc

    targets = data.get("targets")
    if not isinstance(targets, list):
        raise ConfigError("triggers.json 缺少 targets 数组")
    seen: set[str] = set()
    for target in targets:
        if not isinstance(target, dict):
            raise ConfigError("targets 中存在非对象条目")
        target_id = str(target.get("id", "")).strip()
        if not target_id:
            raise ConfigError("存在缺少 id 的标的")
        if target_id in seen:
            raise ConfigError(f"重复标的 id: {target_id}")
        seen.add(target_id)
        zone_errors = validate_price_zones(target)
        if zone_errors:
            raise ConfigError("；".join(zone_errors))
        infer_sources(target)
    return targets

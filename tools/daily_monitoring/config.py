"""Load and validate daily-monitor configuration from human-authored triggers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


SUPPORTED_DISCLOSURE_SOURCES = frozenset({"cninfo", "hkex", "sec"})


class ConfigError(ValueError):
    """Raised when human-authored monitoring configuration is invalid."""


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
        zone_markets: set[str] = set()
        for zone in target.get("zones") or []:
            if not isinstance(zone, dict):
                raise ConfigError(f"{target_id} 的 zones 中存在非对象条目")
            market = str(zone.get("market", "")).strip()
            if market and market in zone_markets:
                raise ConfigError(
                    f"{target_id} 在同一市场 {market} 配置了多个价格区间"
                )
            if market:
                zone_markets.add(market)
        infer_sources(target)
    return targets

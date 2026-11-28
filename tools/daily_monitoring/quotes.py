"""Tencent quotes plus native-market Yahoo Finance quotes for overseas listings."""

from __future__ import annotations

import json
import math
import re
import subprocess
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo


YAHOO_MARKETS = {
    "FR": (".PA", "EUR"),
    "UK": (".L", "GBp"),
    "SE": (".ST", "SEK"),
    "NL": (".AS", "EUR"),
    "DE": (".DE", "EUR"),
    "AU": (".AX", "AUD"),
    "TW": (".TW", "TWD"),
}
_SHANGHAI = ZoneInfo("Asia/Shanghai")


def yahoo_symbol(code: str) -> str | None:
    if not re.fullmatch(r"yahoo:[A-Z0-9-]+\.[A-Z]+", code):
        return None
    symbol = code.removeprefix("yahoo:")
    return symbol if any(symbol.endswith(suffix) for suffix, _ in YAHOO_MARKETS.values()) else None


def _positive_number(value: Any) -> bool:
    return (not isinstance(value, bool) and isinstance(value, (int, float))
            and math.isfinite(value) and value > 0)


def _parse_yahoo(payload: Any, symbol: str, currency: str) -> dict[str, Any]:
    try:
        chart = payload["chart"]
        if chart.get("error") is not None:
            return {}
        meta = chart["result"][0]["meta"]
        if meta["symbol"] != symbol or meta["currency"] != currency:
            return {}
        price, timestamp = meta["regularMarketPrice"], meta["regularMarketTime"]
        if not _positive_number(price) or not _positive_number(timestamp):
            return {}
        quote_time = datetime.fromtimestamp(timestamp, _SHANGHAI)
        return {"name": meta.get("shortName") or symbol, "price": price,
                "currency": currency, "time": quote_time.strftime("%Y-%m-%d %H:%M:%S"),
                "source": "Yahoo Finance"}
    except (KeyError, IndexError, TypeError, AttributeError, ValueError, OverflowError, OSError):
        return {}


def _yahoo_quote(code: str) -> dict[str, Any]:
    symbol = yahoo_symbol(code)
    if symbol is None:
        return {}
    currency = next(currency for suffix, currency in YAHOO_MARKETS.values()
                    if symbol.endswith(suffix))
    for host in ("query1.finance.yahoo.com", "query2.finance.yahoo.com"):
        url = f"https://{host}/v8/finance/chart/{symbol}?interval=1d&range=5d"
        try:
            response = subprocess.run(
                ["/usr/bin/curl", "-sS", "--fail", "--connect-timeout", "5",
                 "--max-time", "15", "-A", "Mozilla/5.0", url],
                capture_output=True, timeout=20,
            )
            if response.returncode != 0:
                continue
            quote = _parse_yahoo(json.loads(response.stdout), symbol, currency)
            if quote:
                return quote
        except (OSError, subprocess.TimeoutExpired, ValueError, UnicodeDecodeError):
            continue
    return {}


def _tencent_time(code: str, value: Any) -> str:
    raw = str(value or "").replace("/", "-")
    pattern = "%Y%m%d%H%M%S" if re.fullmatch(r"\d{14}", raw) else "%Y-%m-%d %H:%M:%S"
    try:
        local = datetime.strptime(raw, pattern)
        timezone = ZoneInfo("America/New_York") if code.startswith("us") else _SHANGHAI
        return local.replace(tzinfo=timezone).astimezone(_SHANGHAI).strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return ""


def fetch_quotes(codes: list[str]) -> dict[str, dict[str, Any]]:
    from tools.trigger_scanner import _curl_qq

    result: dict[str, dict[str, Any]] = {}
    tencent_codes = [code for code in codes if not code.startswith("yahoo:")]
    for start in range(0, len(tencent_codes), 30):
        batch = _curl_qq(tencent_codes[start : start + 30])
        for code, quote in batch.items():
            currency = {"sh": "CNY", "sz": "CNY", "bj": "CNY", "hk": "HKD",
                        "us": "USD", "kr": "KRW", "jp": "JPY"}.get(code[:2])
            result[code] = {**quote, "currency": currency, "source": "腾讯",
                            "time": _tencent_time(code, quote.get("time"))}
    for code in codes:
        if code.startswith("yahoo:") and (quote := _yahoo_quote(code)):
            result[code] = quote
    return result

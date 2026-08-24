"""HKEXnews official announcement collector."""

from __future__ import annotations

import json
import re
from datetime import date, datetime
from typing import Any
from urllib.parse import urljoin
from zoneinfo import ZoneInfo

from ..http import SourceError, validate_official_url
from ..models import Disclosure


ACTIVE_STOCKS_EN = "https://www1.hkexnews.hk/ncms/script/eds/activestock_sehk_e.json"
ACTIVE_STOCKS_ZH = "https://www1.hkexnews.hk/ncms/script/eds/activestock_sehk_c.json"
TITLE_SEARCH_URL = "https://www1.hkexnews.hk/search/titleSearchServlet.do"
SEARCH_PAGE = "https://www1.hkexnews.hk/search/titlesearch.xhtml"


def _resolve_stock_id(stock_code: str, language: str, http: Any) -> str:
    url = ACTIVE_STOCKS_ZH if language == "zh" else ACTIVE_STOCKS_EN
    payload = http.get_json(url, source="hkex")
    rows = payload if isinstance(payload, list) else payload.get("data", [])
    for row in rows:
        if str(row.get("c") or "").zfill(5) == stock_code:
            return str(row.get("i"))
    raise SourceError("hkex", f"股票代码未映射到 stockId: {stock_code}")


def _result_rows(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict) and isinstance(payload.get("result"), str):
        try:
            payload = json.loads(payload["result"])
        except json.JSONDecodeError as exc:
            raise SourceError("hkex", "title search 双层 JSON 解析失败") from exc
    if isinstance(payload, dict):
        rows = payload.get("result") or payload.get("data") or []
        if isinstance(rows, list):
            return [row for row in rows if isinstance(row, dict)]
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    raise SourceError("hkex", "title search 返回结构异常")


def _document_type(title: str) -> str:
    normalized = title.upper()
    if any(
        word in normalized
        for word in (
            "RESULTS",
            "ANNUAL REPORT",
            "INTERIM REPORT",
            "QUARTERLY REPORT",
            "業績",
            "年報",
            "中期報告",
            "季度報告",
        )
    ):
        return "财报"
    if any(word in normalized for word in ("PROFIT WARNING", "PROFIT ALERT", "盈利警告")):
        return "业绩预告"
    return "正式公告"


def _published_at(value: Any) -> str:
    text = str(value or "").strip()
    for pattern in ("%Y/%m/%d %H:%M", "%Y/%m/%d"):
        try:
            parsed = datetime.strptime(text, pattern).replace(
                tzinfo=ZoneInfo("Asia/Hong_Kong")
            )
            return parsed.isoformat()
        except ValueError:
            continue
    return text


def _document_id(row: dict[str, Any], official_url: str) -> str:
    explicit = row.get("DOCUMENT_ID") or row.get("FILE_ID")
    if explicit:
        return str(explicit)
    match = re.search(r"(\d{13})", official_url)
    if match:
        return match.group(1)
    raise SourceError("hkex", "公告链接缺少稳定 document ID")


def collect(
    target_id: str,
    config: dict[str, Any],
    *,
    since: date,
    until: date,
    http: Any,
) -> list[Disclosure]:
    stock_code = str(config.get("stock_code") or "").zfill(5)
    language = str(config.get("language") or "en").lower()
    if language not in {"en", "zh"}:
        raise SourceError("hkex", f"不支持的语言: {language}")
    stock_id = str(config.get("stock_id") or _resolve_stock_id(stock_code, language, http))
    params = {
        "sortDir": "0",
        "sortByOptions": "DateTime",
        "category": "0",
        "market": "SEHK",
        "stockId": stock_id,
        "documentType": "-1",
        "fromDate": since.strftime("%Y%m%d"),
        "toDate": until.strftime("%Y%m%d"),
        "title": "",
        "searchType": "1",
        "t1code": "-2",
        "t2Gcode": "-2",
        "t2code": "-2",
        "rowRange": "2000",
        "lang": language,
    }
    payload = http.get_json(
        TITLE_SEARCH_URL,
        source="hkex",
        params=params,
        headers={"Referer": SEARCH_PAGE, "Accept": "application/json"},
    )
    documents: list[Disclosure] = []
    for row in _result_rows(payload):
        row_code = str(row.get("STOCK_CODE") or "").zfill(5)
        if row_code != stock_code:
            continue
        file_link = str(row.get("FILE_LINK") or "").strip()
        if not file_link:
            continue
        official_url = urljoin("https://www1.hkexnews.hk/", file_link)
        validate_official_url(official_url, "hkex")
        title = str(row.get("TITLE") or "").strip()
        documents.append(
            Disclosure(
                target_id=target_id,
                source="hkex",
                document_id=_document_id(row, official_url),
                title=title,
                published_at=_published_at(row.get("DATE_TIME")),
                document_type=_document_type(title),
                official_url=official_url,
                download_url=official_url,
            )
        )
    return documents


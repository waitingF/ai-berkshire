"""CNINFO official announcement collector."""

from __future__ import annotations

import html
import re
from datetime import date, datetime
from typing import Any
from zoneinfo import ZoneInfo

from ..http import SourceError, validate_official_url
from ..models import Disclosure


ORG_SEARCH_URL = "https://www.cninfo.com.cn/new/information/topSearch/query"
ANNOUNCEMENT_URL = "https://www.cninfo.com.cn/new/hisAnnouncement/query"
PDF_BASE = "https://static.cninfo.com.cn/"


def _clean_title(value: Any) -> str:
    text = html.unescape(str(value or ""))
    return re.sub(r"<[^>]+>", "", text).strip()


def _document_type(title: str) -> str:
    if any(word in title for word in ("年度报告", "半年度报告", "季度报告", "财务报告")):
        return "财报"
    if any(word in title for word in ("业绩预告", "业绩快报", "盈利预警")):
        return "业绩预告"
    return "正式公告"


def _org_rows(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if isinstance(payload, dict):
        for key in ("keyBoardList", "stockList", "data"):
            rows = payload.get(key)
            if isinstance(rows, list):
                return [row for row in rows if isinstance(row, dict)]
    return []


def _resolve_org_id(stock_code: str, config: dict[str, Any], http: Any) -> str:
    explicit = config.get("org_id") or config.get("orgId")
    if explicit:
        return str(explicit)
    payload = http.post_form_json(
        ORG_SEARCH_URL,
        {"keyWord": stock_code, "maxNum": 10},
        source="cninfo",
        headers={"Referer": "https://www.cninfo.com.cn/"},
    )
    for row in _org_rows(payload):
        if str(row.get("code") or row.get("secCode") or "") == stock_code:
            org_id = row.get("orgId") or row.get("orgid")
            if org_id:
                return str(org_id)
    raise SourceError("cninfo", f"股票代码未映射到 orgId: {stock_code}")


def _published_at(timestamp: Any) -> str:
    try:
        value = float(timestamp) / 1000
    except (TypeError, ValueError):
        return ""
    return datetime.fromtimestamp(value, tz=ZoneInfo("Asia/Shanghai")).isoformat()


def collect(
    target_id: str,
    config: dict[str, Any],
    *,
    since: date,
    until: date,
    http: Any,
) -> list[Disclosure]:
    stock_code = str(config.get("stock_code") or "")
    exchange = str(config.get("exchange") or "").lower()
    if not stock_code or exchange not in {"sh", "sz", "bj"}:
        raise SourceError("cninfo", "缺少有效 stock_code/exchange")
    org_id = _resolve_org_id(stock_code, config, http)
    column = {"sh": "sse", "sz": "szse", "bj": "bjse"}[exchange]
    form = {
        "pageNum": 1,
        "pageSize": 30,
        "column": column,
        "tabName": "fulltext",
        "plate": exchange,
        "stock": f"{stock_code},{org_id}",
        "searchkey": "",
        "secid": "",
        "category": "",
        "trade": "",
        "seDate": f"{since.isoformat()}~{until.isoformat()}",
        "sortName": "time",
        "sortType": "desc",
        "isHLtitle": "true",
    }
    headers = {
        "Origin": "https://www.cninfo.com.cn",
        "Referer": "https://www.cninfo.com.cn/new/commonUrl/pageOfSearch",
        "X-Requested-With": "XMLHttpRequest",
    }
    documents: list[Disclosure] = []
    for page_number in range(1, 6):
        form["pageNum"] = page_number
        payload = http.post_form_json(
            ANNOUNCEMENT_URL, form, source="cninfo", headers=headers
        )
        rows = payload.get("announcements") or []
        for row in rows:
            announcement_id = str(row.get("announcementId") or "").strip()
            adjunct = str(row.get("adjunctUrl") or "").lstrip("/")
            if not announcement_id or not adjunct:
                continue
            official_url = PDF_BASE + adjunct
            validate_official_url(official_url, "cninfo")
            title = _clean_title(row.get("announcementTitle"))
            documents.append(
                Disclosure(
                    target_id=target_id,
                    source="cninfo",
                    document_id=announcement_id,
                    title=title,
                    published_at=_published_at(row.get("announcementTime")),
                    document_type=_document_type(title),
                    official_url=official_url,
                    download_url=official_url,
                )
            )
        if not payload.get("hasMore"):
            break
    return documents

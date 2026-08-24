"""SEC EDGAR submissions collector."""

from __future__ import annotations

from datetime import date
from typing import Any

from ..http import SourceError, validate_official_url
from ..models import Disclosure


TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
DEFAULT_FORMS = frozenset({"10-K", "10-Q", "8-K", "20-F", "6-K", "40-F"})


def _normalize_cik(value: Any) -> str:
    digits = str(value).strip()
    if not digits.isdigit() or len(digits) > 10:
        raise SourceError("sec", f"CIK 非法: {value}")
    return digits.zfill(10)


def _resolve_cik(config: dict[str, Any], http: Any) -> str:
    if config.get("cik"):
        return _normalize_cik(config["cik"])
    ticker = str(config.get("ticker") or "").upper().strip()
    if not ticker:
        raise SourceError("sec", "缺少 ticker 或 CIK")
    payload = http.get_json(TICKERS_URL, source="sec")
    rows = payload.values() if isinstance(payload, dict) else payload
    for row in rows:
        if str(row.get("ticker") or "").upper() == ticker:
            return _normalize_cik(row.get("cik_str"))
    raise SourceError("sec", f"SEC ticker 未映射到 CIK: {ticker}")


def collect(
    target_id: str,
    config: dict[str, Any],
    *,
    since: date,
    until: date,
    http: Any,
) -> list[Disclosure]:
    cik = _resolve_cik(config, http)
    forms = {
        str(form).strip().upper()
        for form in (config.get("forms") or DEFAULT_FORMS)
    }
    payload = http.get_json(SUBMISSIONS_URL.format(cik=cik), source="sec")
    recent = ((payload.get("filings") or {}).get("recent") or {})
    accession_numbers = recent.get("accessionNumber") or []
    documents: list[Disclosure] = []
    for index, accession in enumerate(accession_numbers):
        try:
            filing_date = date.fromisoformat(recent["filingDate"][index])
            form = str(recent["form"][index]).upper()
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise SourceError("sec", "submissions recent 列结构异常") from exc
        if filing_date < since or filing_date > until or form not in forms:
            continue
        primary_document = str(recent.get("primaryDocument", [""])[index] or "")
        accession_compact = str(accession).replace("-", "")
        cik_compact = str(int(cik))
        filename = primary_document or f"{str(accession).replace('-', '')}-index.html"
        official_url = (
            f"https://www.sec.gov/Archives/edgar/data/{cik_compact}/"
            f"{accession_compact}/{filename}"
        )
        validate_official_url(official_url, "sec")
        accepted = (recent.get("acceptanceDateTime") or [""])[index]
        description = (recent.get("primaryDocDescription") or [""])[index]
        documents.append(
            Disclosure(
                target_id=target_id,
                source="sec",
                document_id=str(accession),
                title=str(description or f"SEC {form}"),
                published_at=str(accepted or filing_date.isoformat()),
                document_type=form,
                official_url=official_url,
                download_url=official_url,
            )
        )
    return documents


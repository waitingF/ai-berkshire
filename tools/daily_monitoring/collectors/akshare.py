"""Optional AKShare fallback that never replaces official verification."""

from __future__ import annotations

from datetime import date
from typing import Any, Callable

from ..http import UnsafeUrlError, validate_official_url
from ..models import FallbackClue


def _records(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [row for row in value if isinstance(row, dict)]
    to_dict = getattr(value, "to_dict", None)
    if callable(to_dict):
        rows = to_dict("records")
        return [row for row in rows if isinstance(row, dict)]
    return []


def _default_provider(**kwargs: Any) -> Any:
    try:
        import akshare as ak
    except ImportError as exc:
        raise RuntimeError("AKShare 未安装，备用源不可用") from exc
    return ak.stock_notice_report(symbol="全部", date=kwargs["date"])


def collect_fallback(
    target_id: str,
    config: dict[str, Any],
    *,
    since: date,
    until: date,
    provider: Callable[..., Any] | None = None,
) -> list[FallbackClue]:
    stock_code = str(config.get("stock_code") or "")
    if not stock_code:
        return []
    rows = _records((provider or _default_provider)(date=until.strftime("%Y%m%d")))
    clues: list[FallbackClue] = []
    for row in rows:
        row_code = str(row.get("代码") or row.get("股票代码") or row.get("stock_code") or "")
        if row_code != stock_code:
            continue
        published_at = str(row.get("公告日期") or row.get("日期") or "")
        try:
            published_date = date.fromisoformat(published_at[:10])
        except ValueError:
            published_date = until
        if published_date < since or published_date > until:
            continue
        url = str(row.get("网址") or row.get("公告链接") or row.get("url") or "").strip() or None
        verified = False
        if url:
            try:
                validate_official_url(url, "cninfo")
                verified = True
            except UnsafeUrlError:
                verified = False
        clues.append(
            FallbackClue(
                target_id=target_id,
                source="akshare",
                title=str(row.get("公告标题") or row.get("标题") or "未命名公告"),
                published_at=published_at,
                url=url,
                verified=verified,
                needs_human_review=not verified,
            )
        )
    return clues

"""Normalize collector routing and conservative disclosure deduplication."""

from __future__ import annotations

import re
from dataclasses import replace
from typing import Iterable

from .models import Disclosure


def _normalized_title(value: str) -> str:
    return re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "", value.casefold())


def _merge(first: Disclosure, second: Disclosure) -> Disclosure:
    urls = tuple(dict.fromkeys((*first.source_urls, *second.source_urls)))
    return replace(
        first,
        sha256=first.sha256 or second.sha256,
        source_urls=urls,
    )


def deduplicate(disclosures: Iterable[Disclosure]) -> list[Disclosure]:
    """Deduplicate by official ID, then hash, then exact normalized title/date."""
    result: list[Disclosure] = []
    key_to_index: dict[tuple[str, ...], int] = {}
    for disclosure in disclosures:
        keys = [("id", disclosure.source, disclosure.document_id)]
        if disclosure.sha256:
            keys.append(("hash", disclosure.target_id, disclosure.sha256))
        normalized_title = _normalized_title(disclosure.title)
        published_date = disclosure.published_at[:10]
        if normalized_title and published_date:
            keys.append(
                ("title-date", disclosure.target_id, normalized_title, published_date)
            )

        existing_indexes = {key_to_index[key] for key in keys if key in key_to_index}
        if existing_indexes:
            index = min(existing_indexes)
            result[index] = _merge(result[index], disclosure)
            for key in keys:
                key_to_index[key] = index
            continue

        index = len(result)
        result.append(disclosure)
        for key in keys:
            key_to_index[key] = index
    return result


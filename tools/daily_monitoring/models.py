"""Normalized immutable data structures shared by daily-monitor components."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Disclosure:
    target_id: str
    source: str
    document_id: str
    title: str
    published_at: str
    document_type: str
    official_url: str
    download_url: str | None = None
    sha256: str | None = None
    extraction_status: str = "NOT_ATTEMPTED"
    pages_used: tuple[int, ...] = ()
    source_urls: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.source_urls and self.official_url:
            object.__setattr__(self, "source_urls", (self.official_url,))


@dataclass(frozen=True)
class VerifiedFact:
    fact: str
    official_url: str
    page: int | None
    confidence: str


@dataclass(frozen=True)
class MonitorItem:
    fingerprint: str
    section: str
    priority: str
    target_id: str
    name: str
    title: str
    why_now: str
    status: str
    verified_facts: tuple[VerifiedFact, ...] = ()
    source_urls: tuple[str, ...] = ()
    next_workflow: str | None = None
    needs_human_review: bool = False
    limitations: tuple[str, ...] = ()
    notify: bool = False
    resolved: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class FallbackClue:
    target_id: str
    source: str
    title: str
    published_at: str
    url: str | None
    verified: bool
    needs_human_review: bool


@dataclass(frozen=True)
class SourceHealth:
    source: str
    status: str
    safe_message: str | None = None


@dataclass(frozen=True)
class ReportPaths:
    dated: Path
    latest: Path
    latest_json: Path


@dataclass(frozen=True)
class RunResult:
    status: str
    items: tuple[MonitorItem, ...]
    notification_items: tuple[MonitorItem, ...]
    source_health: tuple[SourceHealth, ...]
    next_state: dict[str, Any]
    report_paths: ReportPaths | None


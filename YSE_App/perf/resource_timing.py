"""
Browser-style resource timing for perf waterfall plots.

Timeline fields (start_ms, end_ms) position each resource on a shared axis so
parallel vs sequential load patterns are visible. Django test client measures
durations; scheduling models browser behavior (document first, then parallel AJAX).
"""

from __future__ import annotations

import os
import time
from dataclasses import asdict, dataclass
from typing import Dict, List, Optional, Tuple

from django.db import connection
from django.test import Client
from django.test.utils import CaptureQueriesContext

# DevTools-like phase order and colors (Safari/Chrome network panel).
WATERFALL_PHASES: Tuple[Tuple[str, str], ...] = (
    ("queued", "#e0e0e0"),
    ("dns", "#7fd14e"),
    ("connect", "#ff9800"),
    ("ssl", "#ba68c8"),
    ("waiting", "#4caf50"),
    ("download", "#42a5f5"),
)


@dataclass
class ResourceTiming:
    """One network row (like a browser Network panel entry)."""

    name: str
    url: str
    resource_type: str  # document, xhr, js, img, other
    size_bytes: int
    status_code: int
    start_ms: float = 0.0
    end_ms: float = 0.0
    queued_ms: float = 0.0
    dns_ms: float = 0.0
    connect_ms: float = 0.0
    ssl_ms: float = 0.0
    waiting_ms: float = 0.0
    download_ms: float = 0.0
    sql_ms: float = 0.0
    app_ms: float = 0.0
    sql_count: int = 0

    @property
    def total_ms(self) -> float:
        return (
            self.queued_ms
            + self.dns_ms
            + self.connect_ms
            + self.ssl_ms
            + self.waiting_ms
            + self.download_ms
        )

    def phase_ms(self) -> Dict[str, float]:
        return {
            "queued": self.queued_ms,
            "dns": self.dns_ms,
            "connect": self.connect_ms,
            "ssl": self.ssl_ms,
            "waiting": self.waiting_ms,
            "download": self.download_ms,
        }

    def place_on_timeline(self, start_ms: float) -> None:
        """Set absolute start/end from duration and timeline offset."""
        self.start_ms = start_ms
        self.end_ms = start_ms + self.total_ms

    def to_dict(self) -> dict:
        d = asdict(self)
        d["total_ms"] = round(self.total_ms, 1)
        d["start_ms"] = round(self.start_ms, 1)
        d["end_ms"] = round(self.end_ms, 1)
        return d


@dataclass
class PageLoadTimeline:
    """Full page load with resources placed on a shared time axis."""

    page_key: str
    resources: List[ResourceTiming]
    schedule_note: str = ""

    @property
    def page_load_total_ms(self) -> float:
        if not self.resources:
            return 0.0
        return max(r.end_ms for r in self.resources)

    def to_dict(self) -> dict:
        return {
            "page_key": self.page_key,
            "page_load_total_ms": round(self.page_load_total_ms, 1),
            "schedule_note": self.schedule_note,
            "resources": [r.to_dict() for r in self.resources],
        }


def timeline_total_ms(resources: List[ResourceTiming]) -> float:
    if not resources:
        return 0.0
    return max(r.end_ms for r in resources)


def schedule_parallel(resources: List[ResourceTiming], start_ms: float) -> float:
    """
  Place resources at the same start (parallel). Returns page end time.

  Durations are measured separately; only offsets are parallel.
  """
    for r in resources:
        r.place_on_timeline(start_ms)
    if not resources:
        return start_ms
    return start_ms + max(r.total_ms for r in resources)


def schedule_sequential(resources: List[ResourceTiming], start_ms: float) -> float:
    """Place resources one after another. Returns page end time."""
    cursor = start_ms
    for r in resources:
        r.place_on_timeline(cursor)
        cursor = r.end_ms
    return cursor


def _estimate_download_ms(size_bytes: int) -> float:
    if size_bytes <= 0:
        return 0.0
    mbps = float(os.environ.get("YSE_PERF_DOWNLOAD_MBPS", "10"))
    return (size_bytes * 8.0 / (mbps * 1_000_000.0)) * 1000.0


def profile_request(
    client: Client,
    url: str,
    *,
    name: str,
    resource_type: str,
    queued_ms: float = 0.0,
) -> ResourceTiming:
    """Profile one GET; map server time to waiting, size to download."""
    with CaptureQueriesContext(connection) as ctx:
        start = time.perf_counter()
        response = client.get(url)
        elapsed_ms = (time.perf_counter() - start) * 1000.0

    sql_ms = sum(float(q.get("time", 0)) for q in ctx.captured_queries) * 1000.0
    app_ms = max(0.0, elapsed_ms - sql_ms)
    size = len(response.content or b"")
    download_ms = _estimate_download_ms(size)
    waiting_ms = max(0.0, elapsed_ms - download_ms)

    return ResourceTiming(
        name=name,
        url=url,
        resource_type=resource_type,
        size_bytes=size,
        status_code=response.status_code,
        queued_ms=queued_ms,
        waiting_ms=waiting_ms,
        download_ms=download_ms,
        sql_ms=sql_ms,
        app_ms=app_ms,
        sql_count=len(ctx.captured_queries),
    )


def profile_request_optional(
    client: Client, url: str, *, name: str, resource_type: str
) -> Optional[ResourceTiming]:
    try:
        row = profile_request(client, url, name=name, resource_type=resource_type)
        if row.status_code >= 400:
            row.name = f"{name} ({row.status_code})"
        return row
    except Exception:
        return None

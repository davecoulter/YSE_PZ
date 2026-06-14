"""
Optional per-view section timing (enable with YSE_VIEW_TIMING=1).
"""

from __future__ import annotations

import logging
import os
import time
from contextlib import contextmanager
from typing import Dict, Iterator, List, Tuple

logger = logging.getLogger(__name__)

_ENABLED = os.environ.get("YSE_VIEW_TIMING", "").lower() in ("1", "true", "yes")


def enabled() -> bool:
    return _ENABLED


@contextmanager
def section(name: str, bucket: List[Tuple[str, float]]) -> Iterator[None]:
    if not _ENABLED:
        yield
        return
    start = time.perf_counter()
    try:
        yield
    finally:
        bucket.append((name, (time.perf_counter() - start) * 1000.0))


def log_sections(view_name: str, sections: List[Tuple[str, float]]) -> Dict[str, float]:
    if not sections:
        return {}
    payload = {name: round(ms, 1) for name, ms in sections}
    total = sum(payload.values())
    logger.info("YSE_VIEW_TIMING view=%s total_ms=%.1f sections=%s", view_name, total, payload)
    return payload

"""
Record and report page load metrics (wall time + SQL query count).

Metrics are always collected. Printed summary at end of test_performance module.
Optional JSON export: YSE_PERF_RECORD_PATH=/path/to/perf.json
"""

import json
import os
from dataclasses import asdict, dataclass
from typing import List, Optional


@dataclass
class PageLoadMetric:
    page: str
    url: str
    queries: int
    load_time_s: float

    @property
    def load_time_ms(self) -> float:
        return self.load_time_s * 1000.0


class LoadTimeRegistry:
    """Accumulates metrics across tests in a run."""

    _records: List[PageLoadMetric] = []

    @classmethod
    def reset(cls):
        cls._records.clear()

    @classmethod
    def record(cls, page: str, url: str, queries: int, load_time_s: float) -> PageLoadMetric:
        metric = PageLoadMetric(
            page=page, url=url, queries=queries, load_time_s=load_time_s
        )
        cls._records.append(metric)
        return metric

    @classmethod
    def records(cls) -> List[PageLoadMetric]:
        return list(cls._records)

    @classmethod
    def format_summary(cls) -> str:
        if not cls._records:
            return "Page load metrics: (none recorded)"

        lines = [
            "",
            "=== Page load metrics (wall time + queries) ===",
            f"{'Page':<42} {'Load (ms)':>10} {'Queries':>8}",
            "-" * 64,
        ]
        for m in cls._records:
            lines.append(
                f"{m.page:<42} {m.load_time_ms:>10.1f} {m.queries:>8d}"
            )
        lines.append("-" * 64)
        total_ms = sum(m.load_time_ms for m in cls._records)
        total_q = sum(m.queries for m in cls._records)
        lines.append(f"{'TOTAL':<42} {total_ms:>10.1f} {total_q:>8d}")
        lines.append("")
        return "\n".join(lines)

    @classmethod
    def write_json(cls, path: str):
        payload = {
            "metrics": [asdict(m) for m in cls._records],
            "summary": {
                "total_load_time_s": sum(m.load_time_s for m in cls._records),
                "total_queries": sum(m.queries for m in cls._records),
            },
        }
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)


def export_metrics_if_configured():
    path = os.environ.get("YSE_PERF_RECORD_PATH", "").strip()
    if path:
        LoadTimeRegistry.write_json(path)

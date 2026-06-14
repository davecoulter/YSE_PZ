"""
Measure primary page load times (wall clock + SQL count) using test fixtures.

Used by manage.py record_perf_benchmark and CI regression tests.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Dict, List, Optional
from django.db import connection
from django.test import Client, override_settings
from django.test.utils import CaptureQueriesContext

from YSE_App.tests.fixtures_minimal import (
    create_minimal_transient,
    create_test_user,
    create_transient_with_synthetic_data,
    seed_dashboard_transients,
    seed_personal_dashboard_queries,
)

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]


@dataclass
class PageBenchmark:
    page_key: str
    url: str
    ttfb_ms: float
    total_ms: float
    sql_count: int
    sections: Optional[Dict[str, float]] = None


def _profile_get(client: Client, url: str) -> tuple:
    with CaptureQueriesContext(connection) as ctx:
        start = time.perf_counter()
        response = client.get(url)
        elapsed = time.perf_counter() - start
    return response, len(ctx.captured_queries), elapsed * 1000.0


def _ms(elapsed_s: float) -> float:
    return elapsed_s * 1000.0


@override_settings(PASSWORD_HASHERS=PASSWORD_HASHERS)
def run_primary_pages() -> List[PageBenchmark]:
    """Run the three tracked pages with representative fixture data."""
    user = create_test_user("perf_benchmark_primary")
    client = Client()
    client.force_login(user)

    seed_dashboard_transients(user, count_per_status=1)
    response, n_queries, ms = _profile_get(client, "/dashboard/")
    if response.status_code != 200:
        raise RuntimeError(f"dashboard returned {response.status_code}")

    results: List[PageBenchmark] = [
        PageBenchmark(
            page_key="main_dashboard",
            url="/dashboard/",
            ttfb_ms=ms,
            total_ms=ms,
            sql_count=n_queries,
        )
    ]

    pd_user = create_test_user("perf_benchmark_pdash")
    client.force_login(pd_user)
    seed_personal_dashboard_queries(pd_user, n_queries=5)
    # Deferred shell (production default): fast first paint, sections via AJAX.
    response, n_queries, ms = _profile_get(client, "/personaldashboard/")
    if response.status_code != 200:
        raise RuntimeError(f"personaldashboard returned {response.status_code}")
    results.append(
        PageBenchmark(
            page_key="personal_dashboard",
            url="/personaldashboard/",
            ttfb_ms=ms,
            total_ms=ms,
            sql_count=n_queries,
        )
    )

    td_user = create_test_user("perf_benchmark_tdetail")
    client.force_login(td_user)
    transient = create_transient_with_synthetic_data(
        td_user, name="perf-benchmark-loaded", n_phot_points=12
    )
    url = f"/transient_detail/{transient.slug}/"
    response, n_queries, ms = _profile_get(client, url)
    if response.status_code != 200:
        raise RuntimeError(f"transient_detail returned {response.status_code}")
    results.append(
        PageBenchmark(
            page_key="transient_detail",
            url=url,
            ttfb_ms=ms,
            total_ms=ms,
            sql_count=n_queries,
        )
    )
    return results


def run_primary_pages_as_dict() -> Dict[str, PageBenchmark]:
    return {p.page_key: p for p in run_primary_pages()}

"""
Page-load performance baselines for hot paths.

Metrics tracked on every run:
  - HTTP 200
  - SQL query count (hard ceiling)
  - Wall-clock load time in ms (recorded always; ceiling unless YSE_PERF_SKIP_TIMING=1)

At end of this module, a summary table is printed. Optional JSON:
  YSE_PERF_RECORD_PATH=/tmp/yse_perf.json

Run:
  docker exec ysepz_web_container python3 manage.py test YSE_App.tests.test_performance -v2
"""

import os
import time
import unittest
from typing import Optional

from django.db import connection
from django.test import Client, TestCase, override_settings
from django.test.utils import CaptureQueriesContext

from YSE_App.tests.fixtures_minimal import (
    create_minimal_transient,
    create_test_user,
    create_transient_with_synthetic_data,
    seed_dashboard_transients,
)
from YSE_App.tests.perf_tracking import LoadTimeRegistry

# Query ceilings — tighten as views are optimized.
MAX_QUERIES_TRANSIENT_DETAIL_SHELL = 60
MAX_QUERIES_TRANSIENT_DETAIL_LOADED = 78
MAX_QUERIES_PERSONAL_DASHBOARD = 40
MAX_QUERIES_MAIN_DASHBOARD = 80

# Load-time ceilings (seconds).
MAX_SECONDS_TRANSIENT_DETAIL_SHELL = 8.0
MAX_SECONDS_TRANSIENT_DETAIL_LOADED = 12.0
MAX_SECONDS_PERSONAL_DASHBOARD = 3.0
MAX_SECONDS_MAIN_DASHBOARD = 6.0

SKIP_TIMING = os.environ.get("YSE_PERF_SKIP_TIMING", "").lower() in ("1", "true", "yes")


def setUpModule():
    LoadTimeRegistry.reset()


def tearDownModule():
    print(LoadTimeRegistry.format_summary())
    try:
        from YSE_App.tests import perf_tracking

        perf_tracking.export_metrics_if_configured()
    except OSError as exc:
        print(f"Warning: could not write YSE_PERF_RECORD_PATH: {exc}")


def _profile_get(client, url):
    """Return (response, query_count, elapsed_seconds)."""
    with CaptureQueriesContext(connection) as ctx:
        start = time.perf_counter()
        response = client.get(url)
        elapsed = time.perf_counter() - start
    return response, len(ctx.captured_queries), elapsed


def assert_page_load(
    test_case,
    *,
    page: str,
    url: str,
    response,
    n_queries: int,
    elapsed: float,
    max_queries: int,
    max_seconds: Optional[float] = None,
):
    """Assert HTTP/queries, record load time, optionally assert wall-time ceiling."""
    metric = LoadTimeRegistry.record(page, url, n_queries, elapsed)
    test_case.assertEqual(response.status_code, 200, msg=f"{page} returned {response.status_code}")
    test_case.assertLess(
        n_queries,
        max_queries,
        msg=(
            f"{page}: {n_queries} queries (max {max_queries}); "
            f"load {metric.load_time_ms:.1f} ms"
        ),
    )
    if max_seconds is not None and not SKIP_TIMING:
        test_case.assertLess(
            elapsed,
            max_seconds,
            msg=(
                f"{page}: load {metric.load_time_ms:.1f} ms exceeds "
                f"{max_seconds * 1000:.0f} ms ceiling"
            ),
        )


@override_settings(
    PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"],
)
class TransientDetailPagePerformanceTests(TestCase):
    """Transient object page: /transient_detail/<slug>/"""

    @classmethod
    def setUpTestData(cls):
        cls.user = create_test_user("perf_detail_user")
        cls.transient_shell = create_minimal_transient(
            cls.user, name="perf-detail-shell"
        )
        cls.transient_loaded = create_transient_with_synthetic_data(
            cls.user,
            name="perf-detail-loaded",
            n_phot_points=12,
        )

    def setUp(self):
        self.client = Client()
        self.client.force_login(self.user)

    def test_transient_detail_shell_returns_200(self):
        url = f"/transient_detail/{self.transient_shell.slug}/"
        response, n_queries, elapsed = _profile_get(self.client, url)
        assert_page_load(
            self,
            page="transient_detail (shell)",
            url=url,
            response=response,
            n_queries=n_queries,
            elapsed=elapsed,
            max_queries=MAX_QUERIES_TRANSIENT_DETAIL_SHELL,
            max_seconds=MAX_SECONDS_TRANSIENT_DETAIL_SHELL,
        )

    def test_transient_detail_with_synthetic_data_returns_200(self):
        url = f"/transient_detail/{self.transient_loaded.slug}/"
        response, n_queries, elapsed = _profile_get(self.client, url)
        self.assertIn(b"perf-detail-loaded", response.content)
        assert_page_load(
            self,
            page="transient_detail (loaded)",
            url=url,
            response=response,
            n_queries=n_queries,
            elapsed=elapsed,
            max_queries=MAX_QUERIES_TRANSIENT_DETAIL_LOADED,
            max_seconds=MAX_SECONDS_TRANSIENT_DETAIL_LOADED,
        )


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class PersonalDashboardPerformanceTests(TestCase):
    """User personal dashboard: /personaldashboard/"""

    @classmethod
    def setUpTestData(cls):
        cls.user = create_test_user("perf_pdash_user")

    def setUp(self):
        self.client = Client()
        self.client.force_login(self.user)

    def test_personaldashboard_empty_returns_200(self):
        url = "/personaldashboard/"
        response, n_queries, elapsed = _profile_get(self.client, url)
        assert_page_load(
            self,
            page="personaldashboard (empty)",
            url=url,
            response=response,
            n_queries=n_queries,
            elapsed=elapsed,
            max_queries=MAX_QUERIES_PERSONAL_DASHBOARD,
            max_seconds=MAX_SECONDS_PERSONAL_DASHBOARD,
        )

    def test_personaldashboard_with_seed_transients(self):
        seed_dashboard_transients(self.user, count_per_status=0)
        url = "/personaldashboard/"
        response, n_queries, elapsed = _profile_get(self.client, url)
        assert_page_load(
            self,
            page="personaldashboard (seed only)",
            url=url,
            response=response,
            n_queries=n_queries,
            elapsed=elapsed,
            max_queries=MAX_QUERIES_PERSONAL_DASHBOARD,
            max_seconds=MAX_SECONDS_PERSONAL_DASHBOARD,
        )


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class MainDashboardPerformanceTests(TestCase):
    """Staff dashboard with status buckets: /dashboard/"""

    @classmethod
    def setUpTestData(cls):
        cls.user = create_test_user("perf_mdash_user")
        seed_dashboard_transients(cls.user, count_per_status=1)

    def setUp(self):
        self.client = Client()
        self.client.force_login(self.user)

    def test_main_dashboard_returns_200(self):
        url = "/dashboard/"
        response, n_queries, elapsed = _profile_get(self.client, url)
        assert_page_load(
            self,
            page="dashboard (main)",
            url=url,
            response=response,
            n_queries=n_queries,
            elapsed=elapsed,
            max_queries=MAX_QUERIES_MAIN_DASHBOARD,
            max_seconds=MAX_SECONDS_MAIN_DASHBOARD,
        )

    @unittest.skip("Enable after dashboard query optimization PR")
    def test_main_dashboard_query_count_tight(self):
        with self.assertNumQueries(50):
            response = self.client.get("/dashboard/")
        self.assertEqual(response.status_code, 200)

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
from unittest.mock import patch

from django.db import connection, connections
from django.test import Client, TestCase, override_settings
from django.test.utils import CaptureQueriesContext

from YSE_App.tests.fixtures_minimal import (
    create_minimal_transient,
    create_test_user,
    create_transient_with_synthetic_data,
    seed_dashboard_transients,
    seed_explorer_query_catalog,
    seed_personal_dashboard_queries,
)
from YSE_App.tests.perf_tracking import LoadTimeRegistry

# Query ceilings — tighten as views are optimized.
MAX_QUERIES_TRANSIENT_DETAIL_SHELL = 50
MAX_QUERIES_TRANSIENT_DETAIL_LOADED = 72
MAX_QUERIES_PERSONAL_DASHBOARD = 40
# Cold: five explorer SQL runs + five table builds (heavy; ceiling guards regressions).
MAX_QUERIES_PERSONAL_DASHBOARD_FIVE_QUERIES_COLD = 28
# Warm: SQL results cached; exercises second-pass table build only.
MAX_QUERIES_PERSONAL_DASHBOARD_FIVE_QUERIES_WARM = 23
MAX_QUERIES_MAIN_DASHBOARD = 25
# Explorer index: empty querylog ~6 queries; with logs ~1 + N counts (django-sql-explorer).
MAX_QUERIES_EXPLORER_INDEX_CATALOG = 15
MAX_QUERIES_EXPLORER_INDEX_PER_50_WITH_LOGS = 60
MAX_EXPLORER_CATALOG_SIZE = 50
# Production-scale catalog; wall time not asserted (Python/template bound, not SQL).
MAX_EXPLORER_CATALOG_SIZE_LARGE = 200
MAX_QUERIES_EXPLORER_INDEX_200_WITH_LOGS = 15

MAX_SECONDS_PERSONAL_DASHBOARD_FIVE = 5.0
MAX_SECONDS_EXPLORER_INDEX = 15.0

# Load-time ceilings (seconds).
MAX_SECONDS_TRANSIENT_DETAIL_SHELL = 8.0
MAX_SECONDS_TRANSIENT_DETAIL_LOADED = 12.0
MAX_SECONDS_PERSONAL_DASHBOARD = 3.0
MAX_SECONDS_MAIN_DASHBOARD = 6.0
MAX_QUERIES_CALENDAR = 12
MAX_SECONDS_CALENDAR = 3.0

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

    def test_personaldashboard_with_five_saved_queries_warm_cache(self):
        """Five saved queries with cached SQL results (typical repeat visit)."""
        from django.core.cache import cache

        user_queries = seed_personal_dashboard_queries(self.user, n_queries=5)
        for i, uq in enumerate(user_queries):
            cache.set(f"user_query_{uq.id}", [f"perf-pdash-q{i}"], timeout=3600)
        url = "/personaldashboard/"
        response, n_queries, elapsed = _profile_get(self.client, url)
        assert_page_load(
            self,
            page="personaldashboard (5 queries, warm cache)",
            url=url,
            response=response,
            n_queries=n_queries,
            elapsed=elapsed,
            max_queries=MAX_QUERIES_PERSONAL_DASHBOARD_FIVE_QUERIES_WARM,
            max_seconds=MAX_SECONDS_PERSONAL_DASHBOARD_FIVE,
        )

    def test_personaldashboard_with_five_saved_queries_cold_cache(self):
        """Cold load: runs each saved SQL once (explorer DB mocked to default in tests)."""
        import YSE_App.views as views_module
        from django.core.cache import cache

        seed_personal_dashboard_queries(self.user, n_queries=5)
        cache.clear()
        url = "/personaldashboard/"
        real = connections

        class _ConnectionsForTests:
            def __getitem__(self, alias):
                if alias == "explorer":
                    return real["default"]
                return real[alias]

        with patch.object(views_module, "connections", _ConnectionsForTests()):
            response, n_queries, elapsed = _profile_get(self.client, url)

        assert_page_load(
            self,
            page="personaldashboard (5 saved queries, cold)",
            url=url,
            response=response,
            n_queries=n_queries,
            elapsed=elapsed,
            max_queries=MAX_QUERIES_PERSONAL_DASHBOARD_FIVE_QUERIES_COLD,
            max_seconds=MAX_SECONDS_PERSONAL_DASHBOARD_FIVE,
        )


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class ExplorerIndexPerformanceTests(TestCase):
    """
    Query Explorer list (/explorer/): loads all Query rows + N+1 querylog counts.

    Does not execute saved SQL on index; slowness on production is ORM/metadata.
    Isolated from personaldashboard — other pages do not load the full catalog.
    """

    @classmethod
    def setUpTestData(cls):
        cls.user = create_test_user("perf_explorer_user")
        seed_explorer_query_catalog(
            cls.user, n_queries=MAX_EXPLORER_CATALOG_SIZE, with_query_logs=False
        )

    def setUp(self):
        self.client = Client()
        self.client.force_login(self.user)

    def test_explorer_index_catalog_only(self):
        """Explorer list without query logs (fast metadata load)."""
        url = "/explorer/"
        response, n_queries, elapsed = _profile_get(self.client, url)
        assert_page_load(
            self,
            page=f"explorer index ({MAX_EXPLORER_CATALOG_SIZE} rows, no logs)",
            url=url,
            response=response,
            n_queries=n_queries,
            elapsed=elapsed,
            max_queries=MAX_QUERIES_EXPLORER_INDEX_CATALOG,
            max_seconds=MAX_SECONDS_EXPLORER_INDEX,
        )

    def test_explorer_index_with_query_logs(self):
        """
        Catalog rows with QueryLog entries.

        Current django-sql-explorer prefetches querylog_set, so COUNT N+1 may not
        appear (still ~O(N) Python work building the list). Production slowness
        with 200+ saved queries is usually this metadata pass, not running all SQL.
        """
        user = create_test_user("perf_explorer_n1_user")
        seed_explorer_query_catalog(
            user, n_queries=MAX_EXPLORER_CATALOG_SIZE, with_query_logs=True
        )
        self.client.force_login(user)
        url = "/explorer/"
        max_q = MAX_QUERIES_EXPLORER_INDEX_PER_50_WITH_LOGS * (
            MAX_EXPLORER_CATALOG_SIZE // 50
        )
        response, n_queries, elapsed = _profile_get(self.client, url)
        assert_page_load(
            self,
            page=f"explorer index ({MAX_EXPLORER_CATALOG_SIZE} rows + logs)",
            url=url,
            response=response,
            n_queries=n_queries,
            elapsed=elapsed,
            max_queries=max_q,
            max_seconds=MAX_SECONDS_EXPLORER_INDEX,
        )

    def test_explorer_index_200_queries_with_logs_query_count(self):
        """
        Production-scale explorer index: ~200 saved queries with QueryLog rows.

        Benchmark (Docker): ~12 SQL queries; wall time is dominated by Python/template
        work, not DB round-trips. Only query count is gated here (no time ceiling).
        """
        user = create_test_user("perf_explorer_200_user")
        seed_explorer_query_catalog(
            user,
            n_queries=MAX_EXPLORER_CATALOG_SIZE_LARGE,
            with_query_logs=True,
        )
        self.client.force_login(user)
        url = "/explorer/"
        response, n_queries, elapsed = _profile_get(self.client, url)
        assert_page_load(
            self,
            page=f"explorer index ({MAX_EXPLORER_CATALOG_SIZE_LARGE} rows + logs)",
            url=url,
            response=response,
            n_queries=n_queries,
            elapsed=elapsed,
            max_queries=MAX_QUERIES_EXPLORER_INDEX_200_WITH_LOGS,
            max_seconds=None,
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

    def test_main_dashboard_query_count_tight(self):
        url = "/dashboard/"
        response, n_queries, elapsed = _profile_get(self.client, url)
        self.assertEqual(response.status_code, 200)
        self.assertLess(n_queries, MAX_QUERIES_MAIN_DASHBOARD)


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class CalendarPerformanceTests(TestCase):
    """On-call calendar: /calendar/"""

    @classmethod
    def setUpTestData(cls):
        cls.user = create_test_user("perf_calendar_user")

    def setUp(self):
        self.client = Client()
        self.client.force_login(self.user)

    def test_calendar_returns_200(self):
        url = "/calendar/"
        response, n_queries, elapsed = _profile_get(self.client, url)
        assert_page_load(
            self,
            page="calendar",
            url=url,
            response=response,
            n_queries=n_queries,
            elapsed=elapsed,
            max_queries=MAX_QUERIES_CALENDAR,
            max_seconds=MAX_SECONDS_CALENDAR,
        )

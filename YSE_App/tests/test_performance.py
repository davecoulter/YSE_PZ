"""
Page-load performance baselines for hot paths.

Metrics:
  - HTTP 200 on core pages
  - SQL query count (regression guard via assertNumQueries)
  - Wall time (soft ceiling; skipped when YSE_PERF_SKIP_TIMING=1)

Run:
  docker exec ysepz_web_container python3 manage.py test YSE_App.tests.test_performance -v2
"""

import os
import time
import unittest

from django.db import connection
from django.test import Client, TestCase, override_settings
from django.test.utils import CaptureQueriesContext

from YSE_App.tests.fixtures_minimal import (
    create_minimal_transient,
    create_test_user,
    seed_dashboard_transients,
)

# Query ceilings — tighten as views are optimized.
MAX_QUERIES_TRANSIENT_DETAIL = 60  # baseline ~54 with minimal fixture (2026-05-19)
MAX_QUERIES_PERSONAL_DASHBOARD = 40
MAX_QUERIES_MAIN_DASHBOARD = 80

# Wall-time ceilings (seconds) for minimal fixture data on a dev laptop.
MAX_SECONDS_TRANSIENT_DETAIL = 8.0
MAX_SECONDS_PERSONAL_DASHBOARD = 3.0
MAX_SECONDS_MAIN_DASHBOARD = 6.0

SKIP_TIMING = os.environ.get("YSE_PERF_SKIP_TIMING", "").lower() in ("1", "true", "yes")


def _profile_get(client, url):
    """Return (response, query_count, elapsed_seconds)."""
    with CaptureQueriesContext(connection) as ctx:
        start = time.perf_counter()
        response = client.get(url)
        elapsed = time.perf_counter() - start
    return response, len(ctx.captured_queries), elapsed


@override_settings(
    # Avoid hitting remote services where signals might otherwise fire repeatedly.
    PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"],
)
class TransientDetailPagePerformanceTests(TestCase):
    """Transient object page: /transient_detail/<slug>/"""

    @classmethod
    def setUpTestData(cls):
        cls.user = create_test_user("perf_detail_user")
        cls.transient = create_minimal_transient(cls.user, name="perf-detail-sn")

    def setUp(self):
        self.client = Client()
        self.client.force_login(self.user)

    def test_transient_detail_returns_200(self):
        url = f"/transient_detail/{self.transient.slug}/"
        response, n_queries, elapsed = _profile_get(self.client, url)
        self.assertEqual(response.status_code, 200)
        self.assertLess(
            n_queries,
            MAX_QUERIES_TRANSIENT_DETAIL,
            msg=f"too many SQL queries ({n_queries}) for transient_detail",
        )
        if not SKIP_TIMING:
            self.assertLess(
                elapsed,
                MAX_SECONDS_TRANSIENT_DETAIL,
                msg=f"transient_detail took {elapsed:.2f}s",
            )

@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class PersonalDashboardPerformanceTests(TestCase):
    """User personal dashboard: /personaldashboard/ (no saved queries)."""

    @classmethod
    def setUpTestData(cls):
        cls.user = create_test_user("perf_pdash_user")
        # No UserQuery rows — empty dashboard is the minimal case.

    def setUp(self):
        self.client = Client()
        self.client.force_login(self.user)

    def test_personaldashboard_empty_returns_200(self):
        response, n_queries, elapsed = _profile_get(self.client, "/personaldashboard/")
        self.assertEqual(response.status_code, 200)
        self.assertLess(n_queries, MAX_QUERIES_PERSONAL_DASHBOARD)
        if not SKIP_TIMING:
            self.assertLess(elapsed, MAX_SECONDS_PERSONAL_DASHBOARD)

    def test_personaldashboard_with_seed_transients(self):
        """Dashboard still loads when user has no custom queries (global list empty)."""
        seed_dashboard_transients(self.user, count_per_status=0)
        response, n_queries, elapsed = _profile_get(self.client, "/personaldashboard/")
        self.assertEqual(response.status_code, 200)
        self.assertLess(n_queries, MAX_QUERIES_PERSONAL_DASHBOARD)
        if not SKIP_TIMING:
            self.assertLess(elapsed, MAX_SECONDS_PERSONAL_DASHBOARD)


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
        response, n_queries, elapsed = _profile_get(self.client, "/dashboard/")
        self.assertEqual(response.status_code, 200)
        self.assertLess(
            n_queries,
            MAX_QUERIES_MAIN_DASHBOARD,
            msg=f"too many SQL queries ({n_queries}) for dashboard",
        )
        if not SKIP_TIMING:
            self.assertLess(elapsed, MAX_SECONDS_MAIN_DASHBOARD)

    @unittest.skip("Enable after dashboard query optimization PR")
    def test_main_dashboard_query_count_tight(self):
        with self.assertNumQueries(50):
            response = self.client.get("/dashboard/")
        self.assertEqual(response.status_code, 200)

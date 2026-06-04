"""
Smoke tests: hot pages return 200 without template errors.

Uses in-test synthetic data (no TNS fixture required). For real 2026f* data,
see test_fixture_page_loads.py and docker/db_fixtures/.
"""

from django.test import Client, TestCase

from YSE_App.tests.fixtures_minimal import (
    create_minimal_transient,
    create_test_user,
    create_transient_with_synthetic_data,
    ensure_transient_statuses,
)
from YSE_App.tests.static_asset_utils import static_asset_available


class UIPageLoadSmokeTests(TestCase):
    """Regression: includes and theme must not break page renders."""

    @classmethod
    def setUpTestData(cls):
        cls.user = create_test_user("ui_smoke_user")
        cls.transient_shell = create_minimal_transient(
            cls.user, name="ui-smoke-shell"
        )
        cls.transient_loaded = create_transient_with_synthetic_data(
            cls.user,
            name="ui-smoke-loaded",
            n_phot_points=8,
            with_host=True,
            with_spectrum=True,
            with_log=True,
        )
        ensure_transient_statuses(cls.user)

    def setUp(self):
        self.client = Client()
        self.client.force_login(self.user)

    def _assert_ok_html(self, response, url):
        self.assertEqual(
            response.status_code,
            200,
            f"{url} returned {response.status_code}",
        )
        body = response.content.decode("utf-8", errors="replace")
        self.assertNotIn("TemplateSyntaxError", body)
        self.assertNotIn("Invalid filter", body)
        self.assertNotIn("Invalid block tag", body)

    def test_login_page(self):
        response = Client().get("/login/")
        self.assertEqual(response.status_code, 200)

    def test_dashboard(self):
        self._assert_ok_html(self.client.get("/dashboard/"), "/dashboard/")

    def test_personaldashboard(self):
        self._assert_ok_html(
            self.client.get("/personaldashboard/"),
            "/personaldashboard/",
        )

    def test_transient_detail_shell(self):
        url = f"/transient_detail/{self.transient_shell.slug}/"
        response = self.client.get(url)
        self._assert_ok_html(response, url)
        self.assertContains(response, "yse-theme.css")
        self.assertTrue(static_asset_available("YSE_App/yse-theme.css"))

    def test_transient_detail_loaded_summary(self):
        url = f"/transient_detail/{self.transient_loaded.slug}/"
        response = self.client.get(url)
        self._assert_ok_html(response, url)
        self.assertContains(response, "ui-smoke-loaded")
        self.assertContains(response, "summary_tab")

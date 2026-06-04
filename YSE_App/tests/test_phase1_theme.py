"""Phase 1 theme: yse-theme.css loaded on hot pages (#24–#32)."""

from django.test import Client, TestCase

from YSE_App.tests.fixtures_minimal import create_minimal_transient, create_test_user


class Phase1ThemeSmokeTests(TestCase):
    def setUp(self):
        self.user = create_test_user()
        self.client = Client()
        self.client.force_login(self.user)
        self.transient = create_minimal_transient(self.user, name="phase1-theme-sn")

    def _assert_theme_stylesheet(self, response):
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "yse-theme.css")
        self.assertContains(response, 'class="hold-transition skin-red sidebar-mini yse-theme"')

    def test_dashboard_includes_theme(self):
        self._assert_theme_stylesheet(self.client.get("/dashboard/"))

    def test_personaldashboard_includes_theme(self):
        self._assert_theme_stylesheet(self.client.get("/personaldashboard/"))

    def test_transient_detail_includes_theme(self):
        url = f"/transient_detail/{self.transient.slug}/"
        response = self.client.get(url)
        self._assert_theme_stylesheet(response)
        self.assertContains(response, "yse-page-transient-summary")

    def test_dashboard_has_page_wrapper(self):
        response = self.client.get("/dashboard/")
        self.assertContains(response, "yse-page-dashboard")

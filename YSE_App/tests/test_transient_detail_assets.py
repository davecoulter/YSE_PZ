"""
Transient detail page: local static assets must exist; optional finder chart.

Regression for browser console 404s on /static/ (e.g. yse-theme.css after
collectstatic) and missing finder PNGs for TNS fixture transients.

External JHU/SDSS cutouts (getjpeg.aspx) are third-party and not fetched in CI.
"""

from pathlib import Path

from django.conf import settings
from django.test import Client, TestCase

from YSE_App.tests.fixtures_minimal import create_minimal_transient, create_test_user
from YSE_App.tests.static_asset_utils import (
    external_skyview_urls_from_html,
    local_static_paths_from_html,
    static_asset_available,
    static_relpath_from_url,
)

YSE_THEME_REL = "YSE_App/yse-theme.css"


class YseThemeStaticTests(TestCase):
    def test_yse_theme_css_in_app_static(self):
        self.assertTrue(
            static_asset_available(YSE_THEME_REL),
            f"Missing {YSE_THEME_REL} under YSE_App/static/",
        )

    def test_collected_yse_theme_css_when_static_root_populated(self):
        """Docker/nginx serves STATIC_ROOT; skip until collectstatic has been run."""
        static_root = Path(settings.STATIC_ROOT)
        if not (static_root / "admin/css/base.css").is_file():
            self.skipTest(
                "STATIC_ROOT not populated. Run: ./docker/scripts/yse-docker.sh collectstatic"
            )
        theme = static_root / YSE_THEME_REL
        self.assertTrue(
            theme.is_file(),
            f"Run collectstatic so nginx can serve {YSE_THEME_REL}",
        )


class TransientDetailLocalStaticTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = create_test_user("detail_assets_user")
        cls.transient = create_minimal_transient(cls.user, name="2026fba")

    def setUp(self):
        self.client = Client()
        self.client.force_login(self.user)
        self.url = f"/transient_detail/{self.transient.slug}/"

    def _get_detail_html(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        return response.content.decode("utf-8", errors="replace")

    def test_transient_detail_includes_theme_stylesheet(self):
        html = self._get_detail_html()
        self.assertIn("yse-theme.css", html)

    def test_transient_detail_local_static_urls_exist(self):
        html = self._get_detail_html()
        paths = local_static_paths_from_html(html)
        self.assertTrue(paths, "Expected at least one /static/ URL in transient_detail HTML")
        missing = []
        for url_path in paths:
            rel = static_relpath_from_url(url_path)
            if not static_asset_available(rel):
                missing.append(rel)
        self.assertEqual(
            missing,
            [],
            "Missing local static files (run collectstatic for Docker/nginx): "
            + ", ".join(missing),
        )

    def test_transient_detail_no_finder_png_when_not_generated(self):
        html = self._get_detail_html()
        self.assertNotIn(".finder.png", html)
        self.assertIn("Finder chart not generated yet", html)

    def test_transient_detail_external_skyview_urls_documented(self):
        """SDSS/JHU cutouts may time out offline; ensure they are external, not /static/."""
        html = self._get_detail_html()
        for url in external_skyview_urls_from_html(html):
            self.assertTrue(
                url.startswith("http"),
                f"Expected external skyview URL, got: {url}",
            )
            self.assertNotIn("/static/", url)

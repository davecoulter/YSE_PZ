"""
Page-load tests against real TNS fixture data (2026f* manifest).

Skipped unless docker/db_fixtures/manifest.json lists transients.
Run after: manage.py build_tns_fixture && optional SQL export/import.
"""

import json
import os
from pathlib import Path

from django.conf import settings
from django.test import Client, TestCase

from YSE_App.models import Transient
from YSE_App.tests.fixtures_minimal import create_test_user
from YSE_App.tests.static_asset_utils import (
    local_static_paths_from_html,
    static_asset_available,
    static_relpath_from_url,
)


def _manifest_path():
    return Path(settings.BASE_DIR) / "docker" / "db_fixtures" / "manifest.json"


def _load_fixture_transients():
    path = _manifest_path()
    if not path.is_file():
        return []
    data = json.loads(path.read_text())
    rows = data.get("transients") or []
    return [r for r in rows if r.get("slug")]


class FixturePageLoadTests(TestCase):
    """Hit real transient pages from the TNS fixture manifest."""

    @classmethod
    def setUpTestData(cls):
        cls.user = create_test_user("fixture_page_user")
        cls.slugs = _load_fixture_transients()

    def setUp(self):
        if not self.slugs:
            self.skipTest(
                "No fixture manifest transients. Run build_tns_fixture first."
            )
        manifest_slugs = [r["slug"] for r in self.slugs[:20]]
        self.fixture_slugs_in_db = list(
            Transient.objects.filter(slug__in=manifest_slugs).values_list(
                "slug", flat=True
            )
        )
        self.client = Client()
        self.client.force_login(self.user)

    def _assert_page_ok(self, url):
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, response.content[:500])
        text = response.content.decode("utf-8", errors="replace")
        self.assertNotIn("TemplateSyntaxError", text)
        self.assertNotIn("Invalid filter", text)

    def test_dashboard_with_fixture_data(self):
        self._assert_page_ok("/dashboard/")

    def test_each_fixture_transient_detail(self):
        if not self.fixture_slugs_in_db:
            self.skipTest(
                "Manifest lists transients but none are in DB (CI/test_YSE). "
                "Import fixture SQL or run build_tns_fixture against this database."
            )
        for row in self.slugs[:20]:
            if row["slug"] not in self.fixture_slugs_in_db:
                continue
            url = f"/transient_detail/{row['slug']}/"
            with self.subTest(name=row.get("name"), url=url):
                self._assert_page_ok(url)

    def test_fixture_manifest_env_override(self):
        override = os.environ.get("YSE_FIXTURE_MANIFEST")
        if override:
            self.assertTrue(Path(override).is_file())

    def test_fixture_transient_detail_local_static_assets(self):
        """First manifest transient: no 404 for local /static/ refs (theme, etc.)."""
        row = self.slugs[0]
        if not Transient.objects.filter(slug=row["slug"]).exists():
            self.skipTest(
                f"{row['slug']} not in DB (Django tests use test_YSE). "
                "Ingest fixture into YSE or run synthetic tests: "
                "YSE_App.tests.test_transient_detail_assets"
            )
        url = f"/transient_detail/{row['slug']}/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        html = response.content.decode("utf-8", errors="replace")
        self.assertIn("yse-theme.css", html)
        missing = []
        for url_path in local_static_paths_from_html(html):
            rel = static_relpath_from_url(url_path)
            if rel.endswith(".finder.png") and not static_asset_available(rel):
                continue
            if not static_asset_available(rel):
                missing.append(rel)
        self.assertEqual(
            missing,
            [],
            "Missing static (Docker: ./docker/scripts/yse-docker.sh collectstatic): "
            + ", ".join(missing),
        )

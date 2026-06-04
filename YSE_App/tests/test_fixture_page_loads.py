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

from YSE_App.tests.fixtures_minimal import create_test_user


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
        for row in self.slugs[:20]:
            url = f"/transient_detail/{row['slug']}/"
            with self.subTest(name=row.get("name"), url=url):
                self._assert_page_ok(url)

    def test_fixture_manifest_env_override(self):
        override = os.environ.get("YSE_FIXTURE_MANIFEST")
        if override:
            self.assertTrue(Path(override).is_file())

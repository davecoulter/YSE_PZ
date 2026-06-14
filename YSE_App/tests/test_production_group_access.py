"""
Regression tests for collaboration-group access using production group names.

Covers legacy ungrouped photometry (empty M2M), ``Public``-tagged rows, and
restricted groups (YSE, UCSC, LCOGT) as on the server database — plus plot-cache
keys derived from group membership, not user id.
"""

from __future__ import annotations

import os
import unittest

from django.contrib.auth.models import Group
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from YSE_App.models import TransientPhotometry
from YSE_App.services.group_access_checks import run_production_db_checks
from YSE_App.services.visibility import (
    get_user_group_query,
    group_access_plot_cache_token,
)
from YSE_App.tests.fixtures_minimal import create_test_user
from YSE_App.tests.fixtures_production_groups import (
    EXPECTED_MAGS_BY_USER,
    GROUP_KEYS,
    PHOTOMETRY_SERIES,
    TRANSIENT_NAME,
    authorized_mags_for_user,
    seed_production_group_vis_fixture,
)


class ProductionGroupPatternTests(TestCase):
    """Synthetic transient using real production ``auth.Group`` names."""

    @classmethod
    def setUpTestData(cls):
        cls.transient, cls.users = seed_production_group_vis_fixture()

    def test_production_group_names_exist(self):
        for name in {GROUP_KEYS[k] for _, keys, _ in PHOTOMETRY_SERIES for k in keys}:
            self.assertTrue(Group.objects.filter(name=name).exists(), name)

    def test_legacy_ungrouped_photometry_visible_to_all_test_users(self):
        """Empty ``groups`` M2M (server default for public data) — all users see mag 0."""
        for username, user in self.users.items():
            with self.subTest(user=username):
                mags = authorized_mags_for_user(user, self.transient.id)
                self.assertIn(0, mags)

    def test_public_tagged_row_requires_public_group_membership(self):
        """``Public`` collaboration group (scrub script), not the same as empty M2M."""
        yse_only = self.users["prod_user_yse"]
        pub_yse = self.users["prod_user_pub_yse"]
        self.assertNotIn(1, authorized_mags_for_user(yse_only, self.transient.id))
        self.assertIn(1, authorized_mags_for_user(pub_yse, self.transient.id))

    def test_authorized_mags_per_user(self):
        for username, expected in EXPECTED_MAGS_BY_USER.items():
            user = self.users[username]
            with self.subTest(user=username):
                self.assertEqual(
                    authorized_mags_for_user(user, self.transient.id),
                    expected,
                )

    def test_get_user_group_query_uses_production_group_names(self):
        user = self.users["prod_user_pub_yse"]
        no_group, contains_group = get_user_group_query(user)
        qs = TransientPhotometry.objects.filter(
            transient_id=self.transient.id,
        ).filter(no_group | contains_group)
        mags = set()
        for phot in qs:
            for pd in phot.transientphotdata_set.all():
                if pd.mag is not None:
                    mags.add(int(round(float(pd.mag))))
        self.assertEqual(mags, EXPECTED_MAGS_BY_USER["prod_user_pub_yse"])

    def test_plot_cache_token_same_for_same_production_groups_different_users(self):
        twin = create_test_user("prod_user_pub_yse_twin", is_staff=False)
        twin.groups.set(self.users["prod_user_pub_yse"].groups.all())
        self.assertNotEqual(
            self.users["prod_user_pub_yse"].pk,
            twin.pk,
        )
        self.assertEqual(
            group_access_plot_cache_token(self.users["prod_user_pub_yse"]),
            group_access_plot_cache_token(twin),
        )

    def test_plot_cache_token_differs_for_different_production_group_sets(self):
        tokens = {
            username: group_access_plot_cache_token(user)
            for username, user in self.users.items()
        }
        self.assertEqual(len(tokens), len(set(tokens.values())))

    def test_plot_cache_token_does_not_encode_user_id(self):
        token = group_access_plot_cache_token(self.users["prod_user_yse"])
        self.assertNotIn(str(self.users["prod_user_yse"].pk), token)

    def test_lightcurve_plot_not_shared_across_production_group_sets(self):
        url = reverse(
            "lightcurveplot_detail",
            kwargs={"transient_id": self.transient.id},
        )
        client = Client()
        client.force_login(self.users["prod_user_pub_yse"])
        pub_yse_html = client.get(url).content
        client.force_login(self.users["prod_user_ucsc"])
        ucsc_html = client.get(url).content
        self.assertNotEqual(pub_yse_html, ucsc_html)

    def test_lightcurve_plot_cache_hit_for_same_production_group_membership(self):
        """Two users in Public+YSE must share cached plot HTML (not per-user cache)."""
        url = reverse(
            "lightcurveplot_detail",
            kwargs={"transient_id": self.transient.id},
        )
        twin = create_test_user("prod_user_pub_yse_cache_twin", is_staff=False)
        twin.groups.set(self.users["prod_user_pub_yse"].groups.all())
        self.assertEqual(
            group_access_plot_cache_token(self.users["prod_user_pub_yse"]),
            group_access_plot_cache_token(twin),
        )

        cache.clear()
        client = Client()
        client.force_login(self.users["prod_user_pub_yse"])
        first = client.get(url).content
        client.force_login(twin)
        second = client.get(url).content
        self.assertEqual(first, second)
        self.assertTrue(first)


class ProductionDbCheckLogicTests(TestCase):
    """Unit tests for shared check helpers (used by verify_production_group_access)."""

    def test_run_production_db_checks_on_synthetic_fixture(self):
        seed_production_group_vis_fixture()
        results = run_production_db_checks()
        failed = [r for r in results if not r.passed and not r.skipped]
        self.assertEqual(failed, [], [f"{r.name}: {r.detail}" for r in failed])


@unittest.skipUnless(
    os.environ.get("YSE_TEST_EXISTING_DB_GROUPS", "0") == "1",
    "Set YSE_TEST_EXISTING_DB_GROUPS=1 to mirror checks on default DB via test runner.",
)
class ExistingDatabaseCollaborationGroupTests(TestCase):
    """
    Delegates to the same checks as ``verify_production_group_access``.

    Prefer the management command on the **default** database (server snapshot):

      docker exec ysepz_web_container python3 manage.py verify_production_group_access
    """

    databases = {"default"}

    def test_live_database_group_regression(self):
        results = run_production_db_checks()
        failures = [r for r in results if not r.passed and not r.skipped]
        self.assertEqual(
            failures,
            [],
            "\n".join(f"{r.name}: {r.detail}" for r in failures),
        )

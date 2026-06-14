"""Security matrix: four users × mag-labeled photometry on secvis-matrix."""

from django.test import Client, TestCase
from django.urls import reverse

from YSE_App.data import PhotometryService
from YSE_App.services.visibility import group_access_plot_cache_token, user_can_view_transient
from YSE_App.tests.fixtures_security_matrix import (
    EXPECTED_MAGS_BY_USER,
    TRANSIENT_NAME,
    authorized_mags_for_user,
    seed_security_test_matrix,
)


class SecurityMatrixPhotometryTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.transient, cls.users = seed_security_test_matrix()

    def test_transient_name(self):
        self.assertEqual(self.transient.name, TRANSIENT_NAME)

    def test_all_users_can_view_transient_via_public_photometry(self):
        for username, user in self.users.items():
            with self.subTest(user=username):
                self.assertTrue(
                    user_can_view_transient(user, self.transient.id),
                    f"{username} should access transient (public mag 0)",
                )

    def test_authorized_mags_per_user(self):
        for username, expected in EXPECTED_MAGS_BY_USER.items():
            user = self.users[username]
            with self.subTest(user=username):
                mags = authorized_mags_for_user(user, self.transient.id)
                self.assertEqual(mags, expected)

    def test_photometry_series_count_per_user(self):
        for username, expected in EXPECTED_MAGS_BY_USER.items():
            user = self.users[username]
            with self.subTest(user=username):
                phot = PhotometryService.GetAuthorizedTransientPhotometry_ByUser_ByTransient(
                    user, self.transient.id
                )
                self.assertEqual(phot.count(), len(expected))

    def test_user_d_does_not_see_restricted_series(self):
        user = self.users["sec_user_d"]
        mags = authorized_mags_for_user(user, self.transient.id)
        self.assertNotIn(1, mags)
        self.assertNotIn(5, mags)
        self.assertIn(0, mags)
        self.assertIn(4, mags)

    def test_plot_cache_token_differs_by_user_groups(self):
        ab = group_access_plot_cache_token(self.users["sec_user_ab"])
        b = group_access_plot_cache_token(self.users["sec_user_b"])
        d = group_access_plot_cache_token(self.users["sec_user_d"])
        self.assertNotEqual(ab, b)
        self.assertNotEqual(ab, d)

    def test_plot_cache_token_same_for_identical_group_membership(self):
        from django.contrib.auth.models import Group

        from YSE_App.tests.fixtures_minimal import create_test_user

        twin = create_test_user("sec_user_ab_twin", is_staff=False)
        twin.groups.set(
            Group.objects.filter(
                name__in=["sec-group-a", "sec-group-b"],
            )
        )
        self.assertEqual(
            group_access_plot_cache_token(self.users["sec_user_ab"]),
            group_access_plot_cache_token(twin),
        )
        self.assertNotEqual(
            group_access_plot_cache_token(twin),
            group_access_plot_cache_token(self.users["sec_user_b"]),
        )

    def test_lightcurve_plot_html_differs_by_user(self):
        url = reverse("lightcurveplot_detail", kwargs={"transient_id": self.transient.id})
        client = Client()
        client.force_login(self.users["sec_user_ab"])
        ab_html = client.get(url).content
        client.force_login(self.users["sec_user_b"])
        b_html = client.get(url).content
        client.force_login(self.users["sec_user_d"])
        d_html = client.get(url).content
        self.assertNotEqual(ab_html, b_html)
        self.assertNotEqual(ab_html, d_html)
        self.assertTrue(ab_html)
        self.assertTrue(b_html)
        self.assertTrue(d_html)

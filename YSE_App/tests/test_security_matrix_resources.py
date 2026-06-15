"""Security matrix: group-labeled observing resources for follow-up requests."""

import re

from django.test import Client, TestCase
from django.urls import reverse

from YSE_App.models import ClassicalObservingDate, ClassicalResource, QueuedResource, ToOResource
from YSE_App.tests.fixtures_security_matrix import (
    EXPECTED_MAGS_BY_USER,
    TRANSIENT_NAME,
    authorized_resource_mags_for_user,
    seed_security_test_matrix,
)


class SecurityMatrixResourceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.transient, cls.users = seed_security_test_matrix()

    def test_each_resource_kind_seeded_for_all_series(self):
        for resource_model in (ClassicalResource, ToOResource, QueuedResource):
            with self.subTest(model=resource_model.__name__):
                self.assertEqual(
                    resource_model.objects.filter(
                        description__startswith="secvis-matrix"
                    ).count(),
                    8,
                )

    def test_authorized_classical_resources_per_user(self):
        for username, expected in EXPECTED_MAGS_BY_USER.items():
            user = self.users[username]
            with self.subTest(user=username, kind="classical"):
                mags = authorized_resource_mags_for_user(user, ClassicalResource)
                self.assertEqual(mags, expected)

    def test_authorized_too_resources_per_user(self):
        for username, expected in EXPECTED_MAGS_BY_USER.items():
            user = self.users[username]
            with self.subTest(user=username, kind="too"):
                mags = authorized_resource_mags_for_user(user, ToOResource)
                self.assertEqual(mags, expected)

    def test_authorized_queued_resources_per_user(self):
        for username, expected in EXPECTED_MAGS_BY_USER.items():
            user = self.users[username]
            with self.subTest(user=username, kind="queued"):
                mags = authorized_resource_mags_for_user(user, QueuedResource)
                self.assertEqual(mags, expected)

    def test_classical_observing_dates_idempotent_on_reseed(self):
        classical = ClassicalResource.objects.filter(
            description__startswith="secvis-matrix",
            telescope__name__startswith="SecVis-Cls-",
        )
        seed_security_test_matrix()
        self.assertEqual(
            ClassicalObservingDate.objects.filter(resource__in=classical).count(),
            8,
        )

    def test_observing_calendar_shows_only_authorized_runs(self):
        client = Client()
        url = reverse("observing_calendar")

        client.force_login(self.users["sec_user_ab"])
        response = client.get(url)
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn("SecVis-Cls-mag1-grpA", html)
        self.assertNotIn("SecVis-Cls-mag4-grpD", html)

        client.force_login(self.users["sec_user_d"])
        response = client.get(url)
        html = response.content.decode()
        self.assertIn("SecVis-Cls-mag4-grpD", html)
        self.assertNotIn("SecVis-Cls-mag2-grpB", html)

    def _select_options_html(self, html: str, field_id: str) -> str:
        match = re.search(
            rf'id="{field_id}"[^>]*>(.*?)</select>',
            html,
            re.DOTALL,
        )
        self.assertIsNotNone(match, msg=f"Missing select#{field_id}")
        return match.group(1)

    def test_followup_fragment_lists_only_authorized_classical_resources(self):
        url = reverse(
            "transient_detail_followup_rest_fragment",
            kwargs={"transient_id": self.transient.id},
        )
        client = Client()
        client.force_login(self.users["sec_user_b"])
        response = client.get(url)
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        classical_options = self._select_options_html(html, "id_classical_resource")
        too_options = self._select_options_html(html, "id_too_resource")
        self.assertIn("SecVis-Cls-mag2-grpB", classical_options)
        self.assertNotIn("SecVis-Cls-mag1-grpA", classical_options)
        self.assertIn("SecVis-Too-mag0-public", too_options)
        self.assertNotIn("SecVis-Too-mag1-grpA", too_options)

        client.force_login(self.users["sec_user_d"])
        response = client.get(url)
        html = response.content.decode()
        classical_options = self._select_options_html(html, "id_classical_resource")
        self.assertIn("SecVis-Cls-mag4-grpD", classical_options)
        self.assertNotIn("SecVis-Cls-mag2-grpB", classical_options)

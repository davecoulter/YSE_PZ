"""v1 create-time audience controls for comments and follow-ups."""

from __future__ import annotations

from django.contrib.auth.models import Group
from django.test import Client, TestCase
from django.urls import reverse
from YSE_App.models import Log, TransientFollowup
from YSE_App.services.comments import transient_comment_queryset
from YSE_App.services.visibility import (
    filter_transient_followups_for_user,
    followup_visible_to_user,
)
from YSE_App.tests.fixtures_security_matrix import (
    GROUP_NAMES,
    TRANSIENT_NAME,
    ensure_security_groups,
    seed_security_test_matrix,
)

class CommentAudienceFormTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.transient, cls.users = seed_security_test_matrix()
        cls.groups = ensure_security_groups()
        cls.user_ab = cls.users["sec_user_ab"]
        cls.user_ac = cls.users["sec_user_ac"]
        cls.group_b = cls.groups["b"]

    def test_comment_form_shows_audience_controls(self):
        client = Client()
        client.force_login(self.user_ab)
        url = reverse("transient_detail", kwargs={"slug": TRANSIENT_NAME})
        response = client.get(url)
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn("Who can see this?", html)
        self.assertIn("id_is_public", html)
        self.assertIn("sec-group-a", html)
        self.assertIn("sec-group-b", html)

    def test_default_comment_is_private_not_world_public(self):
        """Private default: not is_public; user with no shared audience group cannot see it."""
        client = Client()
        client.force_login(self.user_ab)
        response = client.post(
            reverse("add_transient_comment"),
            {
                "comment": "private AB comment",
                "transient": self.transient.id,
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        log = Log.objects.get(transient=self.transient, comment="private AB comment")
        self.assertFalse(log.is_public)
        group_names = set(log.groups.values_list("name", flat=True))
        self.assertEqual(group_names, {GROUP_NAMES["a"], GROUP_NAMES["b"]})

        self.assertEqual(
            transient_comment_queryset(self.transient.id, user=self.user_ab).count(),
            1,
        )
        # sec_user_d has only group D — no overlap with A/B audience
        user_d = self.users["sec_user_d"]
        self.assertEqual(
            transient_comment_queryset(self.transient.id, user=user_d).count(),
            0,
        )

    def test_public_comment_visible_to_other_authorized_user(self):
        client = Client()
        client.force_login(self.user_ab)
        client.post(
            reverse("add_transient_comment"),
            {
                "comment": "public to collaborators",
                "transient": self.transient.id,
                "is_public": "on",
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        log = Log.objects.get(transient=self.transient, comment="public to collaborators")
        self.assertTrue(log.is_public)
        self.assertEqual(log.groups.count(), 0)

        qs_ac = transient_comment_queryset(self.transient.id, user=self.user_ac)
        self.assertEqual(qs_ac.count(), 1)

    def test_restricted_comment_to_single_group(self):
        client = Client()
        client.force_login(self.user_ab)
        client.post(
            reverse("add_transient_comment"),
            {
                "comment": "group B only",
                "transient": self.transient.id,
                "audience_groups": [self.group_b.pk],
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        log = Log.objects.get(transient=self.transient, comment="group B only")
        self.assertFalse(log.is_public)
        self.assertEqual(
            set(log.groups.values_list("name", flat=True)),
            {GROUP_NAMES["b"]},
        )
        self.assertEqual(
            transient_comment_queryset(self.transient.id, user=self.user_ab).count(),
            1,
        )
        self.assertEqual(
            transient_comment_queryset(self.transient.id, user=self.user_ac).count(),
            0,
        )


class CommentAudienceApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.transient, cls.users = seed_security_test_matrix()
        cls.user_ab = cls.users["sec_user_ab"]
        cls.user_ac = cls.users["sec_user_ac"]
        cls.groups = ensure_security_groups()

    def test_api_create_private_comment_with_audience_group_ids(self):
        client = Client()
        client.force_login(self.user_ab)
        url = reverse(
            "api-transient-comments",
            kwargs={"transient_id": self.transient.id},
        )
        response = client.post(
            url,
            {
                "comment": "api private B only",
                "transient": self.transient.id,
                "is_public": False,
                "audience_group_ids": [self.groups["b"].pk],
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201, response.content)
        log = Log.objects.get(transient=self.transient, comment="api private B only")
        self.assertFalse(log.is_public)
        self.assertEqual(
            set(log.groups.values_list("name", flat=True)),
            {GROUP_NAMES["b"]},
        )
        self.assertEqual(
            transient_comment_queryset(self.transient.id, user=self.user_ab).count(),
            1,
        )
        self.assertEqual(
            transient_comment_queryset(self.transient.id, user=self.user_ac).count(),
            0,
        )


class FollowupAudienceFormTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.transient, cls.users = seed_security_test_matrix()
        cls.user_ab = cls.users["sec_user_ab"]
        cls.user_ac = cls.users["sec_user_ac"]
        cls.groups = ensure_security_groups()
        from YSE_App.models import FollowupStatus

        cls.status, _ = FollowupStatus.objects.get_or_create(
            name="sec-aud-requested",
            defaults={
                "created_by": cls.users["sec_user_ab"],
                "modified_by": cls.users["sec_user_ab"],
            },
        )

    def _post_followup(self, user, data):
        client = Client()
        client.force_login(user)
        from django.utils import timezone
        from datetime import timedelta

        now = timezone.now()
        payload = {
            "status": self.status.pk,
            "transient": self.transient.pk,
            "valid_start": now.isoformat(),
            "valid_stop": (now + timedelta(days=2)).isoformat(),
        }
        payload.update(data)
        return client.post(
            reverse("add_transient_followup"),
            payload,
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

    def test_default_followup_is_public(self):
        response = self._post_followup(self.user_ab, {"is_public": "on"})
        self.assertEqual(response.status_code, 200)
        followup = TransientFollowup.objects.filter(transient=self.transient).latest("id")
        self.assertTrue(followup.is_public)
        self.assertTrue(followup_visible_to_user(self.user_ac, followup))

    def test_restricted_followup_hidden_from_other_group(self):
        response = self._post_followup(
            self.user_ab,
            {
                "audience_groups": [self.groups["b"].pk],
            },
        )
        self.assertEqual(response.status_code, 200)
        followup = TransientFollowup.objects.filter(transient=self.transient).latest("id")
        self.assertFalse(followup.is_public)
        self.assertEqual(
            set(followup.groups.values_list("name", flat=True)),
            {GROUP_NAMES["b"]},
        )
        self.assertTrue(followup_visible_to_user(self.user_ab, followup))
        self.assertFalse(followup_visible_to_user(self.user_ac, followup))
        qs = filter_transient_followups_for_user(
            TransientFollowup.objects.filter(transient=self.transient),
            self.user_ac,
        )
        self.assertEqual(qs.count(), 0)

"""Group-based visibility for comments and shared helpers (issue #102)."""

from django.contrib.auth.models import Group, User
from django.test import Client, TestCase
from django.urls import reverse
from YSE_App.models import Log, TransientFollowup, TransientPhotometry
from YSE_App.services.comments import create_transient_comment, transient_comment_queryset
from YSE_App.services.visibility import (
    filter_transient_comments_for_user,
    filter_transient_followups_for_user,
    followup_visible_to_user,
    user_can_view_transient,
)
from YSE_App.tests.fixtures_minimal import (
    attach_synthetic_photometry,
    create_minimal_transient,
    create_test_user,
)


class GroupVisibilityTests(TestCase):
    def setUp(self):
        self.group_a, _ = Group.objects.get_or_create(name="sec-test-a")
        self.group_b, _ = Group.objects.get_or_create(name="sec-test-b")

        self.user_a = create_test_user("sec_user_a", is_staff=False)
        self.user_a.groups.add(self.group_a)

        self.user_b = create_test_user("sec_user_b", is_staff=False)
        self.user_b.groups.add(self.group_b)

        admin = create_test_user("sec_admin", is_staff=True)
        self.transient = create_minimal_transient(admin, name="secvis01")
        self.restricted_phot = attach_synthetic_photometry(
            admin, self.transient, n_points=3
        )
        self.restricted_phot.groups.add(self.group_a)

    def test_user_a_can_view_transient_with_group_a_photometry(self):
        self.assertTrue(
            user_can_view_transient(self.user_a, self.transient.id),
        )

    def test_user_b_cannot_view_restricted_transient(self):
        self.assertFalse(
            user_can_view_transient(self.user_b, self.transient.id),
        )

    def test_private_comment_not_visible_to_other_group(self):
        log = create_transient_comment(
            transient=self.transient,
            comment="group A only",
            user=self.user_a,
            notify=False,
            is_public=False,
            audience_groups=[self.group_a],
        )
        self.assertFalse(log.is_public)

        qs_a = transient_comment_queryset(self.transient.id, user=self.user_a)
        self.assertEqual(qs_a.count(), 1)

        qs_b = transient_comment_queryset(self.transient.id, user=self.user_b)
        self.assertEqual(qs_b.count(), 0)

        self.assertIn(
            log,
            list(filter_transient_comments_for_user(Log.objects.all(), self.user_a)),
        )

    def test_creator_only_comment_visible_only_to_author(self):
        log = create_transient_comment(
            transient=self.transient,
            comment="only me",
            user=self.user_a,
            notify=False,
            is_public=False,
            audience_groups=[],
        )
        self.assertEqual(log.groups.count(), 0)
        self.assertEqual(
            transient_comment_queryset(self.transient.id, user=self.user_a).count(),
            1,
        )
        self.assertEqual(
            transient_comment_queryset(self.transient.id, user=self.user_b).count(),
            0,
        )

    def test_public_comment_visible_to_authorized_user(self):
        create_transient_comment(
            transient=self.transient,
            comment="public to collaborators",
            user=self.user_a,
            notify=False,
            is_public=True,
        )
        qs_a = transient_comment_queryset(self.transient.id, user=self.user_a)
        self.assertEqual(qs_a.count(), 1)

    def test_api_list_denied_without_transient_access(self):
        create_transient_comment(
            transient=self.transient,
            comment="hidden",
            user=self.user_a,
            notify=False,
            is_public=True,
        )
        url = reverse(
            "api-transient-comments",
            kwargs={"transient_id": self.transient.id},
        )
        client = Client()
        client.force_login(self.user_b)
        response = client.get(url)
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        results = payload.get("results", payload)
        self.assertEqual(len(results), 0)

    def test_api_create_denied_without_transient_access(self):
        url = reverse(
            "api-transient-comments",
            kwargs={"transient_id": self.transient.id},
        )
        client = Client()
        client.force_login(self.user_b)
        response = client.post(
            url,
            {"comment": "should fail", "transient": self.transient.id},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)

    def _create_followup(self, user, *, is_public=True, groups=None):
        from YSE_App.models import FollowupStatus
        from django.utils import timezone
        from datetime import timedelta

        status, _ = FollowupStatus.objects.get_or_create(
            name="sec-test-requested",
            defaults={
                "created_by": user,
                "modified_by": user,
            },
        )
        now = timezone.now()
        followup = TransientFollowup.objects.create(
            transient=self.transient,
            status=status,
            valid_start=now,
            valid_stop=now + timedelta(days=7),
            is_public=is_public,
            requested_by=user,
            created_by=user,
            modified_by=user,
        )
        if groups:
            followup.groups.set(groups)
        return followup

    def test_private_followup_not_visible_to_other_group(self):
        followup = self._create_followup(
            self.user_a,
            is_public=False,
            groups=[self.group_a],
        )
        self.assertFalse(
            followup_visible_to_user(self.user_b, followup),
        )
        qs = filter_transient_followups_for_user(
            TransientFollowup.objects.filter(transient=self.transient),
            self.user_b,
        )
        self.assertEqual(qs.count(), 0)

    def test_public_followup_visible_to_authorized_user(self):
        followup = self._create_followup(self.user_a, is_public=True)
        self.assertTrue(
            followup_visible_to_user(self.user_a, followup),
        )
        qs = filter_transient_followups_for_user(
            TransientFollowup.objects.filter(transient=self.transient),
            self.user_a,
        )
        self.assertEqual(qs.count(), 1)

    def test_api_followup_list_denied_without_transient_access(self):
        self._create_followup(self.user_a, is_public=True)
        client = Client()
        client.force_login(self.user_b)
        response = client.get("/api/transientfollowups/")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        results = payload.get("results", payload)
        self.assertEqual(len(results), 0)

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

    def test_single_group_users_see_restricted_comment_option(self):
        """Users with one collaboration group on the transient get an explicit group checkbox."""
        url = reverse("transient_detail", kwargs={"slug": TRANSIENT_NAME})
        for username, group_name in (
            ("sec_user_b", GROUP_NAMES["b"]),
            ("sec_user_d", GROUP_NAMES["d"]),
        ):
            client = Client()
            client.force_login(self.users[username])
            response = client.get(url)
            self.assertEqual(response.status_code, 200, msg=username)
            html = response.content.decode()
            self.assertIn("Restrict to collaboration groups", html, msg=username)
            self.assertIn(group_name, html, msg=username)
            self.assertIn("id_audience_groups", html, msg=username)

    def test_default_comment_is_private_to_shared_groups(self):
        """Default form state: shared groups checked, not world-public."""
        client = Client()
        client.force_login(self.user_ab)
        response = client.post(
            reverse("add_transient_comment"),
            {
                "comment": "private AB comment",
                "transient": self.transient.id,
                "audience_groups": [
                    self.groups["a"].pk,
                    self.groups["b"].pk,
                ],
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
        user_d = self.users["sec_user_d"]
        self.assertEqual(
            transient_comment_queryset(self.transient.id, user=user_d).count(),
            0,
        )

    def test_creator_only_comment_when_no_audience_selected(self):
        """Unchecked public + unchecked groups => visible only to the author."""
        client = Client()
        user_b = self.users["sec_user_b"]
        client.force_login(user_b)
        response = client.post(
            reverse("add_transient_comment"),
            {
                "comment": "creator only b",
                "transient": self.transient.id,
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        log = Log.objects.get(transient=self.transient, comment="creator only b")
        self.assertFalse(log.is_public)
        self.assertEqual(log.groups.count(), 0)

        self.assertEqual(
            transient_comment_queryset(self.transient.id, user=user_b).count(),
            1,
        )
        self.assertEqual(
            transient_comment_queryset(self.transient.id, user=self.user_ab).count(),
            0,
        )
        self.assertEqual(
            transient_comment_queryset(self.transient.id, user=self.user_ac).count(),
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

    def test_api_create_creator_only_comment_with_empty_audience_group_ids(self):
        client = Client()
        client.force_login(self.user_ab)
        url = reverse(
            "api-transient-comments",
            kwargs={"transient_id": self.transient.id},
        )
        response = client.post(
            url,
            {
                "comment": "api creator only",
                "transient": self.transient.id,
                "is_public": False,
                "audience_group_ids": [],
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201, response.content)
        log = Log.objects.get(transient=self.transient, comment="api creator only")
        self.assertFalse(log.is_public)
        self.assertEqual(log.groups.count(), 0)
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
        from YSE_App.common.collaboration_groups import (
            ensure_user_has_public_group,
            get_or_create_public_group,
        )

        cls.public_group = get_or_create_public_group()
        for user in cls.users.values():
            ensure_user_has_public_group(user)
        from YSE_App.models import FollowupStatus

        cls.status, _ = FollowupStatus.objects.get_or_create(
            name="sec-aud-requested",
            defaults={
                "created_by": cls.users["sec_user_ab"],
                "modified_by": cls.users["sec_user_ab"],
            },
        )

    def _eligible_group_pks(self, user, resource):
        from YSE_App.services.audience import eligible_followup_audience_groups

        return [
            group.pk for group in eligible_followup_audience_groups(user, resource)
        ]

    def _classical_resource(self, mag: int, band_suffix: str):
        from YSE_App.models import ClassicalResource

        return ClassicalResource.objects.get(
            telescope__name=f"SecVis-Cls-mag{mag}-{band_suffix}"
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

    def test_default_followup_selects_eligible_groups(self):
        resource = self._classical_resource(0, "public")
        eligible = self._eligible_group_pks(self.user_ab, resource)
        response = self._post_followup(
            self.user_ab,
            {
                "classical_resource": resource.pk,
                "audience_groups": eligible,
            },
        )
        self.assertEqual(response.status_code, 200)
        followup = TransientFollowup.objects.filter(transient=self.transient).latest("id")
        self.assertFalse(followup.is_public)
        self.assertEqual(
            set(followup.groups.values_list("pk", flat=True)),
            set(eligible),
        )
        self.assertTrue(followup_visible_to_user(self.user_ac, followup))

    def test_public_group_followup_on_public_resource(self):
        resource = self._classical_resource(0, "public")
        response = self._post_followup(
            self.user_ab,
            {
                "classical_resource": resource.pk,
                "audience_groups": [self.public_group.pk],
            },
        )
        self.assertEqual(response.status_code, 200)
        followup = TransientFollowup.objects.filter(
            transient=self.transient,
            classical_resource=resource,
        ).latest("id")
        self.assertEqual(
            set(followup.groups.values_list("name", flat=True)),
            {"Public"},
        )
        self.assertTrue(followup_visible_to_user(self.user_ac, followup))

    def test_empty_groups_rejected_without_creator_only_resource(self):
        from YSE_App.models import ClassicalResource

        resource = ClassicalResource.objects.get(telescope__name="SecVis-Cls-mag2-grpB")
        response = self._post_followup(
            self.users["sec_user_b"],
            {
                "classical_resource": resource.pk,
                "audience_groups": [],
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("audience_groups", response.json())

    def test_creator_only_followup_visible_to_requester_on_transient_detail(self):
        """Requester always sees their follow-up row when filtered for the transient."""
        from YSE_App.models import ClassicalResource, TransientFollowup
        from YSE_App.services.visibility import filter_transient_followups_for_user

        resource = ClassicalResource.objects.get(telescope__name="SecVis-Cls-mag2-grpB")
        user_b = self.users["sec_user_b"]
        response = self._post_followup(
            user_b,
            {
                "classical_resource": resource.pk,
                "audience_groups": [self.groups["b"].pk],
            },
        )
        self.assertEqual(response.status_code, 200)
        followup = TransientFollowup.objects.filter(
            transient=self.transient,
            requested_by=user_b,
        ).latest("id")
        visible = filter_transient_followups_for_user(
            TransientFollowup.objects.filter(transient=self.transient),
            user_b,
        )
        self.assertIn(
            followup.id,
            list(visible.values_list("id", flat=True)),
        )

    def test_public_group_rejected_on_restricted_resource(self):
        from YSE_App.models import ClassicalResource

        resource = ClassicalResource.objects.get(telescope__name="SecVis-Cls-mag2-grpB")
        response = self._post_followup(
            self.user_ab,
            {
                "classical_resource": resource.pk,
                "audience_groups": [self.public_group.pk, self.groups["b"].pk],
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("audience_groups", response.json())

    def test_classical_followup_without_explicit_date_range(self):
        """Classical-only requests derive valid_start/stop from the resource."""
        from YSE_App.models import ClassicalResource

        resource = ClassicalResource.objects.get(
            telescope__name="SecVis-Cls-mag0-public",
        )
        client = Client()
        client.force_login(self.users["sec_user_d"])
        response = client.post(
            reverse("add_transient_followup"),
            {
                "status": self.status.pk,
                "transient": self.transient.pk,
                "classical_resource": resource.pk,
                "comment": "testing public from d",
                "audience_groups": self._eligible_group_pks(self.users["sec_user_d"], resource),
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200, response.content)
        followup = TransientFollowup.objects.filter(
            transient=self.transient,
            classical_resource=resource,
        ).latest("id")
        self.assertEqual(followup.valid_start, resource.begin_date_valid)
        self.assertEqual(followup.valid_stop, resource.end_date_valid)
        self.assertFalse(followup.is_public)
        self.assertGreater(followup.groups.count(), 0)

    def test_restricted_followup_hidden_from_other_group(self):
        from YSE_App.models import ClassicalResource

        resource = ClassicalResource.objects.get(telescope__name="SecVis-Cls-mag2-grpB")
        response = self._post_followup(
            self.user_ab,
            {
                "classical_resource": resource.pk,
                "audience_groups": [self.groups["b"].pk],
            },
        )
        self.assertEqual(response.status_code, 200)
        followup = TransientFollowup.objects.filter(
            transient=self.transient,
            classical_resource=resource,
        ).latest("id")
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

    def test_legacy_public_followup_on_restricted_resource_hidden_from_other_users(self):
        """``is_public=True`` legacy rows still require linked resource visibility."""
        from YSE_App.models import ClassicalResource

        resource = ClassicalResource.objects.get(telescope__name="SecVis-Cls-mag4-grpD")
        user_d = self.users["sec_user_d"]
        followup = TransientFollowup.objects.create(
            transient=self.transient,
            classical_resource=resource,
            status=self.status,
            valid_start=resource.begin_date_valid,
            valid_stop=resource.end_date_valid,
            is_public=True,
            requested_by=user_d,
            created_by=user_d,
            modified_by=user_d,
        )
        self.assertFalse(followup_visible_to_user(self.user_ab, followup))
        qs = filter_transient_followups_for_user(
            TransientFollowup.objects.filter(classical_resource=resource),
            self.user_ab,
        )
        self.assertEqual(qs.count(), 0)

    def test_followup_page_hides_unauthorized_telescope_sections(self):
        from YSE_App.models import ClassicalResource

        resource = ClassicalResource.objects.get(telescope__name="SecVis-Cls-mag4-grpD")
        user_d = self.users["sec_user_d"]
        TransientFollowup.objects.create(
            transient=self.transient,
            classical_resource=resource,
            status=self.status,
            valid_start=resource.begin_date_valid,
            valid_stop=resource.end_date_valid,
            is_public=True,
            requested_by=user_d,
            created_by=user_d,
            modified_by=user_d,
        )
        client = Client()
        client.force_login(self.user_ab)
        response = client.get(reverse("followup"))
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertNotIn("SecVis-Cls-mag4-grpD", html)

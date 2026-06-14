"""Tests that every user belongs to the Public collaboration group."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

from YSE_App.common.collaboration_groups import (
    PUBLIC_COLLABORATION_GROUP_NAME,
    ensure_user_has_public_group,
)
from YSE_App.tests.fixtures_minimal import create_test_user

User = get_user_model()


class PublicGroupMembershipTests(TestCase):
    def test_new_user_automatically_gets_public_group(self):
        user = User.objects.create_user(
            username="public_auto_user",
            email="public_auto@example.com",
            password="test-pass",
        )
        self.assertTrue(
            user.groups.filter(name=PUBLIC_COLLABORATION_GROUP_NAME).exists()
        )

    def test_ensure_user_has_public_group_is_idempotent(self):
        user = create_test_user("public_idempotent_user", is_staff=False)
        self.assertTrue(
            user.groups.filter(name=PUBLIC_COLLABORATION_GROUP_NAME).exists()
        )
        self.assertFalse(ensure_user_has_public_group(user))

    def test_ensure_users_in_public_group_backfills_missing_membership(self):
        user = User.objects.create_user(
            username="public_backfill_user",
            email="public_backfill@example.com",
            password="test-pass",
        )
        public_group = user.groups.get(name=PUBLIC_COLLABORATION_GROUP_NAME)
        user.groups.remove(public_group)
        self.assertFalse(
            user.groups.filter(name=PUBLIC_COLLABORATION_GROUP_NAME).exists()
        )

        call_command("ensure_users_in_public_group")

        user.refresh_from_db()
        self.assertTrue(
            user.groups.filter(name=PUBLIC_COLLABORATION_GROUP_NAME).exists()
        )

"""
Ensure every user belongs to the Public collaboration group.

Run after importing a server snapshot::

  docker exec ysepz_web_container python3 manage.py ensure_users_in_public_group
  docker exec ysepz_web_container python3 manage.py ensure_users_in_public_group --dry-run
"""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from YSE_App.common.collaboration_groups import (
    PUBLIC_COLLABORATION_GROUP_NAME,
    ensure_user_has_public_group,
    get_or_create_public_group,
)

User = get_user_model()


class Command(BaseCommand):
    help = "Add the Public collaboration group to every user who lacks it."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report counts only; do not update the database.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        public_group = get_or_create_public_group()
        missing = User.objects.exclude(groups=public_group)
        count = missing.count()
        total = User.objects.count()

        self.stdout.write(
            f"Users missing {PUBLIC_COLLABORATION_GROUP_NAME!r}: {count} of {total}"
        )

        if dry_run:
            self.stdout.write(self.style.WARNING("Dry run — no changes made."))
            return

        added = 0
        for user in missing.iterator():
            if ensure_user_has_public_group(user):
                added += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Added {PUBLIC_COLLABORATION_GROUP_NAME!r} to {added} user(s)."
            )
        )

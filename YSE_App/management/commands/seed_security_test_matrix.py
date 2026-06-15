"""Seed four security-test users and secvis-matrix transient (mag-labeled photometry + resources)."""

from __future__ import annotations

from django.core.management.base import BaseCommand

from YSE_App.tests.fixtures_security_matrix import (
    DEFAULT_TEST_PASSWORD,
    EXPECTED_MAGS_BY_USER,
    TEST_USERS,
    TRANSIENT_NAME,
    seed_security_test_matrix,
)


class Command(BaseCommand):
    help = (
        "Create security demo users (sec_user_ab, sec_user_ac, sec_user_b, sec_user_d) "
        f"and transient {TRANSIENT_NAME} with mag-labeled photometry and observing "
        "resources (0=public … 7=overlap)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--password",
            default=DEFAULT_TEST_PASSWORD,
            help=f"Password for test users (default: {DEFAULT_TEST_PASSWORD})",
        )

    def handle(self, *args, **options):
        password = options["password"]
        transient, users = seed_security_test_matrix(password=password)

        self.stdout.write(self.style.SUCCESS("Security test matrix seeded."))
        self.stdout.write("")
        self.stdout.write(f"Transient: {transient.name} (slug: {transient.slug})")
        self.stdout.write(f"URL: /transient_detail/{transient.slug}/")
        self.stdout.write("")
        self.stdout.write("Users (password: %s)" % password)
        for username, group_keys in TEST_USERS:
            groups = ", ".join(group_keys)
            expected = sorted(EXPECTED_MAGS_BY_USER[username])
            self.stdout.write(
                f"  {username:14} groups={groups:8} expected LC mags: {expected}"
            )
        self.stdout.write("")
        self.stdout.write(
            "Observing resources: SecVis-{Cls|Too|Que}-mag{N}-{suffix} "
            "(same group rules as LC mags 0–7). Open Follow-up tab on transient detail."
        )
        self.stdout.write("")
        self.stdout.write("Log in at /login/ and open the transient URL above.")

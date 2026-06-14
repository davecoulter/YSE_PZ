"""Verify collaboration-group access against the live database (not the test DB)."""

from __future__ import annotations

from django.core.management.base import BaseCommand

from YSE_App.services.group_access_checks import run_production_db_checks


class Command(BaseCommand):
    help = (
        "Run production collaboration-group regression checks on the default database "
        "(empty M2M semantics, tagged photometry, plot cache tokens). "
        "Use after importing a server snapshot — not via manage.py test."
    )

    def handle(self, *args, **options):
        results = run_production_db_checks()
        failures = 0
        skips = 0
        for result in results:
            if result.skipped:
                skips += 1
                self.stdout.write(f"SKIP {result.name}: {result.detail}")
            elif result.passed:
                self.stdout.write(self.style.SUCCESS(f"OK   {result.name}: {result.detail}"))
            else:
                failures += 1
                self.stdout.write(self.style.ERROR(f"FAIL {result.name}: {result.detail}"))

        if failures:
            self.stdout.write(self.style.ERROR(f"\n{failures} check(s) failed."))
            raise SystemExit(1)
        self.stdout.write(
            self.style.SUCCESS(
                f"\nAll checks passed ({len(results) - skips - failures} ok, {skips} skipped)."
            )
        )

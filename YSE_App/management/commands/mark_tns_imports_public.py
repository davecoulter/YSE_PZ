"""
Tag existing TNS-import photometry and spectra with the Public collaboration group.

Run against the default database after importing a server snapshot::

  docker exec ysepz_web_container python3 manage.py mark_tns_imports_public
  docker exec ysepz_web_container python3 manage.py mark_tns_imports_public --dry-run
"""

from __future__ import annotations

import re

from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.db.models import Q

from YSE_App.common.collaboration_groups import PUBLIC_COLLABORATION_GROUP_NAME
from YSE_App.models import TransientPhotometry, TransientSpectrum

# Standard TNS IAU names (e.g. 2026fba) — same filter used in TNS_uploads ingest.
TNS_TRANSIENT_NAME_RE = re.compile(r"^20[0-9]{2}[a-zA-Z][a-zA-Z0-9]*$")


def tns_transient_name_q() -> Q:
    return Q(transient__name__regex=TNS_TRANSIENT_NAME_RE.pattern)


class Command(BaseCommand):
    help = (
        "Add the Public collaboration group to TNS transient photometry and spectra "
        "that have no groups M2M rows yet."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report counts only; do not update the database.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        public_group, created = Group.objects.get_or_create(
            name=PUBLIC_COLLABORATION_GROUP_NAME,
        )
        if created:
            self.stdout.write(f"Created collaboration group {PUBLIC_COLLABORATION_GROUP_NAME!r}")

        phot_qs = (
            TransientPhotometry.objects.filter(tns_transient_name_q())
            .filter(groups__isnull=True)
            .distinct()
        )
        spec_qs = (
            TransientSpectrum.objects.filter(tns_transient_name_q())
            .filter(groups__isnull=True)
            .distinct()
        )

        phot_count = phot_qs.count()
        spec_count = spec_qs.count()
        self.stdout.write(
            f"TNS photometry headers to tag: {phot_count}; spectra: {spec_count}"
        )

        if dry_run:
            self.stdout.write(self.style.WARNING("Dry run — no changes made."))
            return

        tagged_phot = 0
        for phot in phot_qs.iterator():
            if not phot.groups.filter(pk=public_group.pk).exists():
                phot.groups.add(public_group)
                tagged_phot += 1

        tagged_spec = 0
        for spec in spec_qs.iterator():
            if not spec.groups.filter(pk=public_group.pk).exists():
                spec.groups.add(public_group)
                tagged_spec += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Tagged {tagged_phot} photometry header(s) and {tagged_spec} spectrum(s) "
                f"with {PUBLIC_COLLABORATION_GROUP_NAME!r}."
            )
        )

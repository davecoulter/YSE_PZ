"""Shared checks for production collaboration-group access (tests + manage.py)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Set

from django.contrib.auth.models import Group, User
from django.db.models import Count

from YSE_App.data import PhotometryService
from YSE_App.models import TransientPhotometry
from YSE_App.services.visibility import group_access_plot_cache_token
from YSE_App.tests.fixtures_production_groups import PRODUCTION_COLLABORATION_GROUPS


@dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str = ""
    skipped: bool = False


def check_production_groups_present(
    minimum: int = 3,
) -> CheckResult:
    present: Set[str] = set(
        Group.objects.filter(name__in=PRODUCTION_COLLABORATION_GROUPS).values_list(
            "name", flat=True
        )
    )
    if "Public" not in present:
        return CheckResult(
            "production_groups_present",
            False,
            f"'Public' missing; found {sorted(present)}",
        )
    if len(present) < minimum:
        return CheckResult(
            "production_groups_present",
            False,
            f"Expected >={minimum} production groups; found {sorted(present)}",
        )
    return CheckResult(
        "production_groups_present",
        True,
        f"{len(present)} groups including Public",
    )


def check_empty_m2m_isnull_semantics() -> CheckResult:
    by_count = TransientPhotometry.objects.annotate(gc=Count("groups")).filter(gc=0).count()
    by_isnull = (
        TransientPhotometry.objects.filter(groups__isnull=True).distinct().count()
    )
    if by_count == 0 and by_isnull == 0:
        return CheckResult(
            "empty_m2m_semantics",
            True,
            "No ungrouped photometry (skipped)",
            skipped=True,
        )
    if by_count != by_isnull:
        return CheckResult(
            "empty_m2m_semantics",
            False,
            f"gc=0 count {by_count} != groups__isnull count {by_isnull}",
        )
    return CheckResult(
        "empty_m2m_semantics",
        True,
        f"{by_count} ungrouped photometry rows (counts agree)",
    )


def check_ungrouped_visible_to_outsider(
    outsider: Optional[User] = None,
) -> CheckResult:
    ungrouped = (
        TransientPhotometry.objects.annotate(gc=Count("groups")).filter(gc=0).first()
    )
    if ungrouped is None:
        return CheckResult(
            "ungrouped_visible",
            True,
            "No ungrouped photometry (skipped)",
            skipped=True,
        )
    if outsider is None:
        outsider = User.objects.filter(is_superuser=False).first()
    if outsider is None:
        return CheckResult("ungrouped_visible", True, "No non-staff user (skipped)", skipped=True)

    allowed = PhotometryService.GetAuthorizedTransientPhotometry_ByUser_ByTransient(
        outsider,
        ungrouped.transient_id,
    )
    ids = list(allowed.values_list("pk", flat=True))
    if ungrouped.pk not in ids:
        return CheckResult(
            "ungrouped_visible",
            False,
            f"Ungrouped phot {ungrouped.pk} not visible to {outsider.username}",
        )
    return CheckResult(
        "ungrouped_visible",
        True,
        f"Ungrouped phot {ungrouped.pk} visible to {outsider.username}",
    )


def check_tagged_photometry_restricted(
    member: Optional[User] = None,
    outsider: Optional[User] = None,
) -> CheckResult:
    tagged = (
        TransientPhotometry.objects.annotate(gc=Count("groups"))
        .filter(gc__gt=0)
        .prefetch_related("groups")
        .first()
    )
    if tagged is None:
        return CheckResult(
            "tagged_restricted",
            True,
            "No group-tagged photometry (skipped)",
            skipped=True,
        )

    required = set(tagged.groups.values_list("name", flat=True))
    if member is None:
        member = User.objects.filter(groups__name__in=required).distinct().first()
    if member is None:
        return CheckResult(
            "tagged_restricted",
            True,
            f"No user in {required} (skipped)",
            skipped=True,
        )
    if outsider is None:
        outsider = (
            User.objects.filter(is_superuser=False)
            .exclude(pk=member.pk)
            .first()
        )
    if outsider is None:
        return CheckResult("tagged_restricted", True, "No outsider user (skipped)", skipped=True)

    outsider.groups.clear()
    allowed_member = PhotometryService.GetAuthorizedTransientPhotometry_ByUser_ByTransient(
        member, tagged.transient_id
    )
    allowed_outsider = PhotometryService.GetAuthorizedTransientPhotometry_ByUser_ByTransient(
        outsider, tagged.transient_id
    )
    member_ids = set(allowed_member.values_list("pk", flat=True))
    outsider_ids = set(allowed_outsider.values_list("pk", flat=True))
    if tagged.pk not in member_ids:
        return CheckResult(
            "tagged_restricted",
            False,
            f"Tagged phot {tagged.pk} not visible to member {member.username}",
        )
    if tagged.pk in outsider_ids:
        return CheckResult(
            "tagged_restricted",
            False,
            f"Tagged phot {tagged.pk} visible to outsider {outsider.username} (groups {required})",
        )
    return CheckResult(
        "tagged_restricted",
        True,
        f"Tagged phot {tagged.pk} restricted to groups {sorted(required)}",
    )


def check_plot_cache_token_by_groups_not_user() -> CheckResult:
    from YSE_App.tests.fixtures_minimal import create_test_user

    groups = Group.objects.filter(name__in=("YSE", "Public")).order_by("name")
    if not groups.exists():
        groups = Group.objects.all().order_by("name")[:2]
    if groups.count() < 1:
        return CheckResult(
            "plot_cache_by_groups",
            True,
            "No groups in DB (skipped)",
            skipped=True,
        )

    u1 = create_test_user("prodgrp_cache_check_1", is_staff=False)
    u2 = create_test_user("prodgrp_cache_check_2", is_staff=False)
    u1.groups.set(groups)
    u2.groups.set(groups)
    t1 = group_access_plot_cache_token(u1)
    t2 = group_access_plot_cache_token(u2)
    if t1 != t2:
        return CheckResult(
            "plot_cache_by_groups",
            False,
            f"Tokens differ for same groups: {t1} vs {t2}",
        )
    if str(u1.pk) in t1 or str(u2.pk) in t2:
        return CheckResult(
            "plot_cache_by_groups",
            False,
            f"Token appears to embed user id: {t1}",
        )
    return CheckResult(
        "plot_cache_by_groups",
        True,
        f"Shared token {t1} for users {u1.pk}, {u2.pk}",
    )


def run_production_db_checks() -> List[CheckResult]:
    return [
        check_production_groups_present(),
        check_empty_m2m_isnull_semantics(),
        check_ungrouped_visible_to_outsider(),
        check_tagged_photometry_restricted(),
        check_plot_cache_token_by_groups_not_user(),
    ]

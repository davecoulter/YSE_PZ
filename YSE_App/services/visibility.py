"""Shared group-based visibility helpers for YSE data and comments."""

from __future__ import annotations

from enum import Enum
from typing import Iterable, List, Optional, Set, Union

from django.contrib.auth.models import Group, User
from django.db.models import Q, QuerySet


class ResourceVisibilityPolicy(str, Enum):
    """Default visibility when creating new rows (empty M2M = public on existing data)."""

    PUBLIC = "public"
    PRIVATE = "private"


def user_group_names(user: User) -> List[str]:
    if not user.is_authenticated:
        return []
    return list(user.groups.values_list("name", flat=True))


def group_access_plot_cache_token(user: User) -> str:
    """Cache suffix from collaboration-group membership (not user id).

    Users who share the same set of ``auth.Group`` names receive the same token,
    so plot HTML is reused across users with identical data access.
    """
    import hashlib

    if not user.is_authenticated:
        return "anon"
    if user.is_staff or user.is_superuser:
        return "staff"
    names = sorted(user_group_names(user))
    if not names:
        return "nogroups"
    digest = hashlib.sha256("|".join(names).encode()).hexdigest()[:12]
    return f"g{digest}"


# Backward-compatible alias (deprecated name).
user_plot_cache_token = group_access_plot_cache_token


def get_user_group_query(user: User):
    """Same semantics as PhotometryService: ungrouped OR intersects user groups."""
    names = user_group_names(user)
    no_group = Q(groups__isnull=True)
    contains_group = Q(groups__name__in=names)
    return no_group, contains_group


def object_has_groups(obj) -> bool:
    return obj.groups.exists()


def object_visible_to_user(user: User, obj) -> bool:
    """Object with optional ``groups`` M2M (photometry, spectrum, resource, log)."""
    if not user.is_authenticated:
        return False
    if user.is_staff or user.is_superuser:
        return True
    if not object_has_groups(obj):
        return True
    names = set(user_group_names(user))
    obj_names = set(obj.groups.values_list("name", flat=True))
    return bool(names.intersection(obj_names))


def transient_visible_group_names(transient_id: int) -> Set[str]:
    from YSE_App.models import TransientPhotometry, TransientSpectrum

    names: Set[str] = set()
    for qs in (
        TransientPhotometry.objects.filter(transient_id=transient_id),
        TransientSpectrum.objects.filter(transient_id=transient_id),
    ):
        for row in qs.prefetch_related("groups"):
            names.update(row.groups.values_list("name", flat=True))
    return names


def shared_groups_for_transient(user: User, transient_id: int) -> QuerySet[Group]:
    """Collaboration groups the user shares with restricted data on this transient."""
    on_transient = transient_visible_group_names(transient_id)
    if not on_transient:
        return user.groups.all()
    return user.groups.filter(name__in=on_transient)


def user_can_view_transient(user: User, transient_id: int) -> bool:
    """True if user may access this transient's collaboration surfaces (comments, etc.)."""
    if not user.is_authenticated:
        return False
    if user.is_staff or user.is_superuser:
        return True
    from YSE_App.data import PhotometryService, SpectraService

    if PhotometryService.GetAuthorizedTransientPhotometry_ByUser_ByTransient(
        user, transient_id
    ).exists():
        return True
    if SpectraService.GetAuthorizedTransientSpectrum_ByUser_ByTransient(
        user, transient_id
    ).exists():
        return True
    return False


def default_comment_audience_groups(user: User, transient_id: int) -> List[Group]:
    """Private-by-default: groups user shares with transient's restricted data."""
    shared = list(shared_groups_for_transient(user, transient_id))
    if shared:
        return shared
    return list(user.groups.all())


def filter_transient_comments_for_user(queryset: QuerySet, user: User) -> QuerySet:
    """Filter transient-level comment logs for read access."""
    if user.is_staff or user.is_superuser:
        return queryset
    names = user_group_names(user)
    return queryset.filter(
        Q(is_public=True) | Q(groups__name__in=names)
    ).distinct()


def log_visible_to_user(user: User, log) -> bool:
    if not user.is_authenticated:
        return False
    if user.is_staff or user.is_superuser:
        return True
    if getattr(log, "is_public", True):
        return True
    if not object_has_groups(log):
        return False
    names = set(user_group_names(user))
    obj_names = set(log.groups.values_list("name", flat=True))
    return bool(names.intersection(obj_names))


def filter_transients_by_user_access(
    user: User, transients: Union[QuerySet, Iterable],
):
    """Post-filter transients (e.g. after SQL Explorer) by photometry/spectrum access."""
    if user.is_staff or user.is_superuser:
        return transients
    from YSE_App.models import Transient

    if isinstance(transients, QuerySet):
        ids = list(transients.values_list("id", flat=True))
        allowed = [
            pk
            for pk in ids
            if user_can_view_transient(user, pk)
        ]
        return transients.filter(id__in=allowed)
    return [t for t in transients if user_can_view_transient(user, t.id)]


def _followup_linked_resource_group_q(user: User) -> Q:
    """Q for follow-up visible via linked telescope resource groups."""
    names = user_group_names(user)
    return (
        Q(classical_resource__groups__name__in=names)
        | Q(too_resource__groups__name__in=names)
        | Q(queued_resource__groups__name__in=names)
    )


def filter_transient_followups_for_user(queryset: QuerySet, user: User) -> QuerySet:
    """Filter follow-up rows for read access (default public for legacy rows)."""
    if user.is_staff or user.is_superuser:
        return queryset
    from YSE_App.data import PhotometryService, SpectraService

    names = user_group_names(user)
    phot_transients = PhotometryService.GetAuthorizedTransientPhotometry_ByUser(
        user
    ).values_list("transient_id", flat=True)
    spec_transients = SpectraService.GetAuthorizedTransientSpectrum_ByUser(
        user
    ).values_list("transient_id", flat=True)
    return queryset.filter(
        Q(transient_id__in=phot_transients) | Q(transient_id__in=spec_transients),
        Q(is_public=True)
        | Q(groups__name__in=names)
        | Q(requested_by=user)
        | _followup_linked_resource_group_q(user),
    ).distinct()


def followup_visible_to_user(user: User, followup) -> bool:
    if not user.is_authenticated:
        return False
    if user.is_staff or user.is_superuser:
        return True
    transient_id = getattr(followup, "transient_id", None)
    if transient_id is not None and not user_can_view_transient(user, transient_id):
        return False
    if getattr(followup, "is_public", True):
        return True
    if followup.requested_by_id == user.id:
        return True
    if object_has_groups(followup):
        names = set(user_group_names(user))
        obj_names = set(followup.groups.values_list("name", flat=True))
        if names.intersection(obj_names):
            return True
    for attr in ("classical_resource", "too_resource", "queued_resource"):
        res = getattr(followup, attr, None)
        if res is not None and object_visible_to_user(user, res):
            return True
    return False

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

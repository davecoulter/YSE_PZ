"""Shared group-based visibility helpers for YSE data and comments."""

from __future__ import annotations

from enum import Enum
from typing import Iterable, List, Optional, Set, Union

from django.contrib.auth.models import Group, User
from django.db.models import Count, Exists, OuterRef, Q, QuerySet

from YSE_App.common.collaboration_groups import PUBLIC_COLLABORATION_GROUP_NAME


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
    return queryset.annotate(
        _audience_group_count=Count("groups", distinct=True),
    ).filter(
        Q(is_public=True)
        | Q(groups__name__in=names)
        | Q(created_by=user, is_public=False, _audience_group_count=0)
    ).distinct()


def log_visible_to_user(user: User, log) -> bool:
    if not user.is_authenticated:
        return False
    if user.is_staff or user.is_superuser:
        return True
    if getattr(log, "is_public", True):
        return True
    if not object_has_groups(log):
        return log.created_by_id == user.id
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


def _user_in_public_group(user: User) -> bool:
    return PUBLIC_COLLABORATION_GROUP_NAME in user_group_names(user)


def _linked_followup_resource(followup):
    for attr in ("classical_resource", "too_resource", "queued_resource"):
        resource = getattr(followup, attr, None)
        if resource is not None:
            return resource
    return None


def user_can_see_linked_followup_resource(user: User, followup) -> bool:
    """Whether ``user`` may view the observing resource linked to a follow-up."""
    resource = _linked_followup_resource(followup)
    if resource is None:
        return True
    return object_visible_to_user(user, resource)


def _observing_resource_ids_visible_to_user(model, user: User) -> Set[int]:
    names = user_group_names(user)
    public_ids = set(
        model.objects.annotate(_resource_group_count=Count("groups"))
        .filter(_resource_group_count=0)
        .values_list("pk", flat=True)
    )
    grouped_ids = set(
        model.objects.filter(groups__name__in=names).values_list("pk", flat=True)
    )
    return public_ids | grouped_ids


def _linked_resource_visible_q(user: User) -> Q:
    """Q matching follow-ups whose linked observing resource is visible to ``user``."""
    from YSE_App.models import ClassicalResource, QueuedResource, ToOResource

    classical_ids = _observing_resource_ids_visible_to_user(ClassicalResource, user)
    too_ids = _observing_resource_ids_visible_to_user(ToOResource, user)
    queued_ids = _observing_resource_ids_visible_to_user(QueuedResource, user)
    q = Q(
        classical_resource__isnull=True,
        too_resource__isnull=True,
        queued_resource__isnull=True,
    )
    if classical_ids:
        q |= Q(classical_resource__in=classical_ids)
    if too_ids:
        q |= Q(too_resource__in=too_ids)
    if queued_ids:
        q |= Q(queued_resource__in=queued_ids)
    return q


def _legacy_public_followup_ids(user: User) -> List[int]:
    """PKs for legacy ``is_public=True`` follow-ups with no explicit groups."""
    from YSE_App.models import TransientFollowup

    qs = TransientFollowup.objects.annotate(_followup_group_count=Count("groups")).filter(
        is_public=True,
        _followup_group_count=0,
    )
    if not _user_in_public_group(user):
        qs = qs.filter(requested_by=user)
    return list(qs.values_list("pk", flat=True))


def filter_transient_followups_for_user(queryset: QuerySet, user: User) -> QuerySet:
    """Filter follow-up rows for read access (default public for legacy rows)."""
    if user.is_staff or user.is_superuser:
        return queryset
    from YSE_App.data import PhotometryService, SpectraService
    from YSE_App.models import TransientFollowup

    names = user_group_names(user)
    phot_transients = PhotometryService.GetAuthorizedTransientPhotometry_ByUser(
        user
    ).values_list("transient_id", flat=True)
    spec_transients = SpectraService.GetAuthorizedTransientSpectrum_ByUser(
        user
    ).values_list("transient_id", flat=True)
    scoped = queryset.filter(
        Q(transient_id__in=phot_transients) | Q(transient_id__in=spec_transients),
    ).filter(_linked_resource_visible_q(user))
    followup_group_link = TransientFollowup.groups.through.objects.filter(
        transientfollowup_id=OuterRef("pk"),
    )
    by_audience = scoped.filter(
        Exists(followup_group_link),
        groups__name__in=names,
    )
    creator_only = scoped.filter(
        ~Exists(followup_group_link),
        is_public=False,
        requested_by=user,
    )
    legacy_ids = _legacy_public_followup_ids(user)
    legacy = scoped.filter(pk__in=legacy_ids) if legacy_ids else scoped.none()
    return (by_audience | creator_only | legacy).distinct()


def followup_visible_to_user(user: User, followup) -> bool:
    if not user.is_authenticated:
        return False
    if user.is_staff or user.is_superuser:
        return True
    transient_id = getattr(followup, "transient_id", None)
    if transient_id is not None and not user_can_view_transient(user, transient_id):
        return False
    if not user_can_see_linked_followup_resource(user, followup):
        return False
    if object_has_groups(followup):
        names = set(user_group_names(user))
        obj_names = set(followup.groups.values_list("name", flat=True))
        return bool(names.intersection(obj_names))
    if getattr(followup, "is_public", False):
        if followup.requested_by_id == user.id:
            return True
        return _user_in_public_group(user)
    if followup.requested_by_id == user.id:
        return True
    return False

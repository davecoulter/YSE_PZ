"""Create-time audience resolution for comments and follow-ups (v1)."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

from django.contrib.auth.models import Group, User
from rest_framework.exceptions import PermissionDenied, ValidationError

from YSE_App.common.collaboration_groups import PUBLIC_COLLABORATION_GROUP_NAME
from YSE_App.services.visibility import (
    default_comment_audience_groups,
    object_has_groups,
    shared_groups_for_transient,
)


def selectable_audience_groups(user: User, transient_id: int):
    """Collaboration groups the user may assign at create time."""
    return shared_groups_for_transient(user, transient_id).order_by("name")


def _groups_from_ids(
    user: User,
    transient_id: int,
    audience_group_ids: Optional[Iterable[int]],
) -> List[Group]:
    if audience_group_ids is None:
        return []
    ids = list(audience_group_ids)
    if not ids:
        return []
    allowed = selectable_audience_groups(user, transient_id)
    selected = list(allowed.filter(id__in=ids))
    if not selected:
        raise ValidationError(
            {"audience_groups": "Select at least one valid collaboration group."}
        )
    user_ids = set(user.groups.values_list("id", flat=True))
    if any(group.id not in user_ids for group in selected):
        raise PermissionDenied(
            {"message": "You cannot assign collaboration groups you do not belong to."}
        )
    return selected


def resolve_comment_audience(
    user: User,
    transient_id: int,
    *,
    is_public: bool,
    audience_group_ids: Optional[Iterable[int]] = None,
    audience_groups: Optional[Iterable[Group]] = None,
) -> Tuple[bool, List[Group]]:
    """
    Return ``(is_public, audience_groups)`` for a new transient comment.

    - ``is_public=True``: all collaborators who can open the transient.
    - Explicit empty group selection: creator-only (``is_public=False``, no groups).
    - No explicit audience in the request: private to shared collaboration groups.
    """
    if is_public:
        return True, []

    explicit_audience = audience_groups is not None or audience_group_ids is not None

    if audience_groups is not None:
        selected = list(audience_groups)
    elif audience_group_ids is not None:
        selected = _groups_from_ids(user, transient_id, audience_group_ids)
    else:
        selected = default_comment_audience_groups(user, transient_id)
        if not selected:
            return True, []
        return False, selected

    if not selected:
        if explicit_audience:
            return False, []
        fallback = default_comment_audience_groups(user, transient_id)
        if not fallback:
            return True, []
        return False, fallback
    return False, selected


def linked_telescope_resource(classical=None, too=None, queued=None):
    """Return the single linked observing resource, if any."""
    return classical or too or queued


def resource_is_public(resource) -> bool:
    """Ungrouped telescope resources are visible to all authorized users."""
    if resource is None:
        return True
    return not object_has_groups(resource)


def resource_audience_group_ids(resource) -> Set[int]:
    if resource is None:
        return set()
    return set(resource.groups.values_list("id", flat=True))


def resource_is_creator_only(resource) -> bool:
    """
    True when the observing resource is private to the requester only.

    No production resources use this yet; set ``creator_only`` on a resource row
    when that workflow is introduced.
    """
    if resource is None:
        return False
    return bool(getattr(resource, "creator_only", False))


def eligible_followup_audience_groups(user: User, resource) -> List[Group]:
    """Collaboration groups the user may assign for a restricted follow-up."""
    user_groups = list(user.groups.order_by("name"))
    if resource_is_public(resource):
        return user_groups
    resource_ids = resource_audience_group_ids(resource)
    return [
        group
        for group in user_groups
        if group.name != PUBLIC_COLLABORATION_GROUP_NAME and group.id in resource_ids
    ]


def build_followup_audience_choices(user: User, resource) -> List[Dict[str, Any]]:
    """All user groups with enabled/checked flags for the follow-up picker."""
    eligible_ids = {group.id for group in eligible_followup_audience_groups(user, resource)}
    resource_public = resource_is_public(resource)
    choices: List[Dict[str, Any]] = []
    for group in user.groups.order_by("name"):
        is_public_group = group.name == PUBLIC_COLLABORATION_GROUP_NAME
        if is_public_group:
            enabled = resource_public
        else:
            enabled = group.id in eligible_ids
        choices.append(
            {
                "group": group,
                "enabled": enabled,
                "checked": enabled,
                "is_public_group": is_public_group,
            }
        )
    return choices


def build_followup_resource_audience_map(form) -> Dict[str, Dict[str, Any]]:
    """Map ``field_name:pk`` to resource audience metadata for client-side sync."""
    resource_map: Dict[str, Dict[str, Any]] = {}
    for field_name in ("classical_resource", "too_resource", "queued_resource"):
        for resource in form.fields[field_name].queryset.prefetch_related("groups"):
            resource_map[f"{field_name}:{resource.pk}"] = {
                "is_public": resource_is_public(resource),
                "group_ids": list(resource.groups.values_list("pk", flat=True)),
            }
    return resource_map


def _followup_groups_from_ids(
    user: User,
    linked_resource,
    audience_group_ids: Iterable[int],
) -> List[Group]:
    ids = list(audience_group_ids)
    if not ids:
        return []
    eligible_ids = {group.id for group in eligible_followup_audience_groups(user, linked_resource)}
    selected = list(user.groups.filter(id__in=ids))
    if not selected:
        raise ValidationError(
            {"audience_groups": "Select at least one valid collaboration group."}
        )
    invalid = [group for group in selected if group.id not in eligible_ids]
    if invalid:
        raise ValidationError(
            {
                "audience_groups": (
                    "One or more selected groups cannot see the linked observing resource."
                )
            }
        )
    return selected


def resolve_followup_audience(
    user: User,
    transient_id: int,
    *,
    audience_group_ids: Optional[Iterable[int]] = None,
    audience_groups: Optional[Iterable[Group]] = None,
    linked_resource=None,
    explicit_audience: bool = True,
) -> Tuple[bool, List[Group]]:
    """
    Return ``(is_public, audience_groups)`` for a new follow-up request.

    New follow-ups are always stored with ``is_public=False``; audience is set
    via collaboration groups. Select the ``Public`` group to share with all
    members of that group (only when the linked resource is itself public).

    Creator-only (no groups) is allowed only for creator-only observing resources.
    """
    eligible = eligible_followup_audience_groups(user, linked_resource)
    eligible_ids = {group.id for group in eligible}

    if audience_groups is not None:
        selected = list(audience_groups)
    elif audience_group_ids is not None:
        selected = _followup_groups_from_ids(user, linked_resource, audience_group_ids)
    elif explicit_audience:
        selected = []
    else:
        selected = eligible

    if not selected:
        if resource_is_creator_only(linked_resource):
            return False, []
        raise ValidationError(
            {"audience_groups": "Select at least one collaboration group."}
        )

    invalid = [group for group in selected if group.id not in eligible_ids]
    if invalid:
        raise ValidationError(
            {
                "audience_groups": (
                    "One or more selected groups cannot see the linked observing resource."
                )
            }
        )
    if any(
        group.name == PUBLIC_COLLABORATION_GROUP_NAME for group in selected
    ) and not resource_is_public(linked_resource):
        raise ValidationError(
            {
                "audience_groups": (
                    "The Public group can only be selected for public observing resources."
                )
            }
        )
    return False, selected

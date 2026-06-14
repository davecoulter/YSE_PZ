"""Create-time audience resolution for comments and follow-ups (v1)."""

from __future__ import annotations

from typing import Iterable, List, Optional, Tuple

from django.contrib.auth.models import Group, User
from rest_framework.exceptions import PermissionDenied, ValidationError

from YSE_App.services.visibility import (
    default_comment_audience_groups,
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
    allowed = selectable_audience_groups(user, transient_id)
    selected = list(allowed.filter(id__in=audience_group_ids))
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

    Default (unchecked ``is_public``, no explicit groups): private audience =
    groups the user shares with restricted data on this transient.
    """
    if is_public:
        return True, []

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
        fallback = default_comment_audience_groups(user, transient_id)
        if not fallback:
            return True, []
        return False, fallback
    return False, selected


def resolve_followup_audience(
    user: User,
    transient_id: int,
    *,
    is_public: bool,
    audience_group_ids: Optional[Iterable[int]] = None,
    audience_groups: Optional[Iterable[Group]] = None,
) -> Tuple[bool, List[Group]]:
    """Return ``(is_public, audience_groups)`` for a new follow-up request."""
    if is_public:
        return True, []

    if audience_groups is not None:
        selected = list(audience_groups)
    elif audience_group_ids is not None:
        selected = _groups_from_ids(user, transient_id, audience_group_ids)
    else:
        selected = list(selectable_audience_groups(user, transient_id))
        if not selected:
            return True, []
        return False, selected

    if not selected:
        raise ValidationError(
            {"audience_groups": "Select collaboration groups for a restricted follow-up."}
        )
    return False, selected

"""Transient comment (Log) create helpers."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from django.contrib.auth.models import Group, User
from rest_framework.exceptions import PermissionDenied

from YSE_App.models import Log, Transient
from YSE_App.services.visibility import (
    default_comment_audience_groups,
    filter_transient_comments_for_user,
    user_can_view_transient,
)


def transient_comment_queryset(transient_id: int, user: Optional[User] = None):
    """Comments on the transient itself (not follow-up rows)."""
    qs = (
        Log.objects.filter(
            transient_id=transient_id,
            transient_followup__isnull=True,
        )
        .select_related("created_by")
        .prefetch_related("groups")
        .order_by("-modified_date")
    )
    if user is not None:
        qs = filter_transient_comments_for_user(qs, user)
    return qs


def format_comment_datetime(dt) -> str:
    return (
        dt.strftime("%b. %-d, %Y, %H:%M ")
        + dt.strftime("%p").lower()[0]
        + "."
        + dt.strftime("%p").lower()[1]
        + "."
    )


def log_to_comment_dict(log: Log) -> Dict[str, Any]:
    return {
        "id": log.id,
        "created_by": str(log.created_by),
        "modified_date": format_comment_datetime(log.modified_date),
        "comment": log.comment,
    }


def create_transient_comment(
    *,
    transient: Transient,
    comment: str,
    user: User,
    notify: bool = True,
    is_public: Optional[bool] = None,
    audience_groups: Optional[List[Group]] = None,
) -> Log:
    if not user_can_view_transient(user, transient.id):
        raise PermissionDenied(
            {"message": "You do not have access to comment on this transient."}
        )

    if is_public is None:
        is_public = False
    if audience_groups is None and not is_public:
        audience_groups = default_comment_audience_groups(user, transient.id)
        if not audience_groups:
            # No collaboration groups to scope to (e.g. public-only transient).
            is_public = True
    elif audience_groups == [] and not is_public:
        audience_groups = []

    log = Log.objects.create(
        transient=transient,
        comment=comment,
        created_by=user,
        modified_by=user,
        is_public=is_public,
    )
    if audience_groups and not is_public:
        log.groups.set(audience_groups)

    if notify:
        from YSE_App.services.notifications import notify_transient_comment

        notify_transient_comment(log)
    return log

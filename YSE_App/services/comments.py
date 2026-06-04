"""Transient comment (Log) create helpers."""

from __future__ import annotations

from typing import Any, Dict, Optional

from django.contrib.auth.models import User

from YSE_App.models import Log, Transient


def transient_comment_queryset(transient_id: int):
    """Comments on the transient itself (not follow-up rows)."""
    return (
        Log.objects.filter(
            transient_id=transient_id,
            transient_followup__isnull=True,
        )
        .select_related("created_by")
        .order_by("-modified_date")
    )


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
) -> Log:
    log = Log.objects.create(
        transient=transient,
        comment=comment,
        created_by=user,
        modified_by=user,
    )
    if notify:
        from YSE_App.services.notifications import notify_transient_comment

        notify_transient_comment(log)
    return log

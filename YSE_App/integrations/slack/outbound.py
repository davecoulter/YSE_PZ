"""Post YSE transient comments to Slack."""

from __future__ import annotations

from django.conf import settings

from YSE_App.integrations.slack.client import chat_post_message
from YSE_App.models import Log
from YSE_App.models.integration_models import SlackThreadLink


def _detail_url(log: Log) -> str:
    base = getattr(settings, "YSE_PUBLIC_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
    return f"{base}/transient_detail/{log.transient.slug}/"


def post_transient_comment(log: Log) -> None:
    if not log.transient_id:
        return
    channel = getattr(settings, "SLACK_DEFAULT_CHANNEL_ID", "") or ""
    if not channel:
        return
    transient = log.transient
    link = SlackThreadLink.objects.filter(
        transient=transient,
        slack_channel_id=channel,
    ).first()
    text = "*%s* on <%s|%s>:\n%s" % (
        log.created_by,
        _detail_url(log),
        transient.name,
        log.comment,
    )
    if link:
        chat_post_message(channel, text, thread_ts=link.slack_thread_ts)
        return
    resp = chat_post_message(channel, text)
    if resp.get("ok") and resp.get("ts"):
        SlackThreadLink.objects.update_or_create(
            transient=transient,
            slack_channel_id=channel,
            defaults={"slack_thread_ts": resp["ts"]},
        )

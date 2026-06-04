"""Slack Events API → YSE Log comments."""

from __future__ import annotations

import json
from typing import Any, Dict

from django.contrib.auth.models import User
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from django.conf import settings

from YSE_App.integrations.slack.verify import verify_slack_signature
from YSE_App.models.integration_models import SlackThreadLink
from YSE_App.services.comments import create_transient_comment


def _slack_service_user() -> User:
    username = getattr(settings, "SLACK_SERVICE_USERNAME", "slack_bot")
    user, _ = User.objects.get_or_create(
        username=username,
        defaults={"email": "slack-bot@yse.local"},
    )
    return user


@csrf_exempt
@require_POST
def slack_events(request):
    signing_secret = getattr(settings, "SLACK_SIGNING_SECRET", "") or ""
    if signing_secret:
        sig = request.headers.get("X-Slack-Signature", "")
        ts = request.headers.get("X-Slack-Request-Timestamp", "")
        if not verify_slack_signature(signing_secret, ts, request.body, sig):
            return HttpResponse(status=403)

    payload: Dict[str, Any] = json.loads(request.body.decode("utf-8"))

    if payload.get("type") == "url_verification":
        return JsonResponse({"challenge": payload.get("challenge", "")})

    if payload.get("type") != "event_callback":
        return HttpResponse(status=200)

    event = payload.get("event") or {}
    if event.get("type") != "message" or event.get("subtype"):
        return HttpResponse(status=200)

    channel = event.get("channel")
    thread_ts = event.get("thread_ts") or event.get("ts")
    text = (event.get("text") or "").strip()
    if not channel or not text or event.get("bot_id"):
        return HttpResponse(status=200)

    link = SlackThreadLink.objects.filter(
        slack_channel_id=channel,
        slack_thread_ts=thread_ts,
    ).first()
    if not link and event.get("thread_ts"):
        link = SlackThreadLink.objects.filter(
            slack_channel_id=channel,
            slack_thread_ts=event.get("thread_ts"),
        ).first()
    if not link:
        return HttpResponse(status=200)

    create_transient_comment(
        transient=link.transient,
        comment=text,
        user=_slack_service_user(),
        notify=False,
    )
    return HttpResponse(status=200)

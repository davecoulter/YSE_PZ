"""Slack Web API helpers."""

from __future__ import annotations

import json
from typing import Any, Dict, Optional
from urllib import request

from django.conf import settings


def _post_api(method: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    token = getattr(settings, "SLACK_BOT_TOKEN", "") or ""
    if not token:
        return {"ok": False, "error": "missing_token"}
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(
        f"https://slack.com/api/{method}",
        data=data,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8",
        },
        method="POST",
    )
    with request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def chat_post_message(
    channel: str,
    text: str,
    *,
    thread_ts: Optional[str] = None,
) -> Dict[str, Any]:
    body: Dict[str, Any] = {"channel": channel, "text": text}
    if thread_ts:
        body["thread_ts"] = thread_ts
    return _post_api("chat.postMessage", body)

"""Slack request signature verification."""

from __future__ import annotations

import hashlib
import hmac
import time


def verify_slack_signature(
    signing_secret: str,
    timestamp: str,
    body: bytes,
    signature: str,
    *,
    max_age_seconds: int = 300,
) -> bool:
    if not signing_secret or not timestamp or not signature:
        return False
    try:
        if abs(time.time() - int(timestamp)) > max_age_seconds:
            return False
    except (TypeError, ValueError):
        return False
    basestring = f"v0:{timestamp}:{body.decode('utf-8')}"
    digest = hmac.new(
        signing_secret.encode("utf-8"),
        basestring.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    expected = f"v0={digest}"
    return hmac.compare_digest(expected, signature)

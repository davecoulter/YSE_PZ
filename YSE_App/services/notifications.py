"""Comment notification: email mentions + optional Slack."""

from __future__ import annotations

import re
from typing import List

import numpy as np
from django.conf import settings
from django.contrib.auth.models import User

from YSE_App.common import alert
from YSE_App.models import Log


def _comment_base_url() -> str:
    if getattr(settings, "YSE_PUBLIC_BASE_URL", None):
        return settings.YSE_PUBLIC_BASE_URL.rstrip("/") + "/"
    if settings.DEBUG:
        return "http://127.0.0.1:8000/"
    return "https://ziggy.ucolick.org/yse/"


def collect_mention_emails(comment_text: str) -> List[str]:
    emaillist = []
    if "@channel" in comment_text:
        for user in User.objects.all():
            if user.email:
                emaillist.append(user.email)
    else:
        for username in re.compile(r"@(\w+)").findall(comment_text):
            usermatch = User.objects.filter(username=username)
            if len(usermatch) and usermatch[0].email:
                emaillist.append(usermatch[0].email)
    return list(np.unique(emaillist))


def notify_email_mentions(log: Log) -> None:
    if not log.transient_id or not log.comment:
        return
    emaillist = collect_mention_emails(log.comment)
    if not emaillist:
        return
    transient_name = log.transient.name
    base_url = _comment_base_url()
    subject = "YSE_PZ: new comment added to event %s" % transient_name
    body = """\
<html>
<head></head>
<body>
<h1>Comment added!</h1>
<p>
<a href='%stransient_detail/%s/'>%s</a><br>
%s says:<br>
%s <br>
</p>
<br />
<p>Go to <a href='%sdashboard/'>YSE Dashboard</a></p>
</body>
</html>
""" % (
        base_url,
        log.transient.slug,
        transient_name,
        str(log.created_by),
        log.comment,
        base_url,
    )
    for email in emaillist:
        alert.send_email_simple(email, subject, body)


def notify_slack_transient_comment(log: Log) -> None:
    if not getattr(settings, "SLACK_ENABLED", False):
        return
    from YSE_App.integrations.slack.outbound import post_transient_comment

    post_transient_comment(log)


def notify_transient_comment(log: Log) -> None:
    notify_email_mentions(log)
    notify_slack_transient_comment(log)

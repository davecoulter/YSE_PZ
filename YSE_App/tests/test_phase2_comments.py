"""Phase 2: transient comments on Summary, API, fragment, Slack verify."""

import hashlib
import hmac
import json
import os
import time
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from rest_framework.authtoken.models import Token

from YSE_App.integrations.slack.verify import verify_slack_signature
from YSE_App.models import Log
from YSE_App.services.comments import create_transient_comment, transient_comment_queryset
from YSE_App.tests.fixtures_minimal import create_minimal_transient, create_test_user


class Phase2CommentTests(TestCase):
    def setUp(self):
        self.user = create_test_user("phase2_comment_user")
        self.transient = create_minimal_transient(
            self.user,
            name="phase2comment01",
        )
        self.client = Client()
        self.client.force_login(self.user)

    def test_transient_detail_summary_has_comments_section(self):
        url = reverse("transient_detail", kwargs={"slug": self.transient.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn("yse-comments-section", html)
        self.assertIn("yse-comment-thread", html)
        self.assertNotIn('id="comments_tab"', html)

    @patch.dict(os.environ, {"YSE_TRANSIENT_DETAIL_DEFER": "1"})
    def test_deferred_transient_detail_renders_saved_comments(self):
        Log.objects.filter(transient=self.transient).delete()
        create_transient_comment(
            transient=self.transient,
            comment="visible on deferred shell",
            user=self.user,
            notify=False,
        )
        url = reverse("transient_detail", kwargs={"slug": self.transient.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn("visible on deferred shell", html)
        self.assertNotIn("No comments yet.", html)

    def test_comments_fragment_returns_panel(self):
        url = reverse("comments_fragment", kwargs={"slug": self.transient.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("yse-comment-thread", response.content.decode())

    def test_add_transient_comment_ajax(self):
        Log.objects.filter(transient=self.transient).delete()
        response = self.client.post(
            reverse("add_transient_comment"),
            {
                "comment": "Phase 2 test comment",
                "transient": self.transient.id,
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("comment", data["data"])
        self.assertEqual(
            Log.objects.filter(transient=self.transient).count(),
            1,
        )

    def test_add_transient_comment_non_ajax_redirects_to_transient_detail(self):
        Log.objects.filter(transient=self.transient).delete()
        response = self.client.post(
            reverse("add_transient_comment"),
            {
                "comment": "Non-AJAX fallback comment",
                "transient": self.transient.id,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response["Location"],
            reverse("transient_detail", kwargs={"slug": self.transient.slug}),
        )
        self.assertEqual(
            Log.objects.filter(
                transient=self.transient,
                comment="Non-AJAX fallback comment",
            ).count(),
            1,
        )

    def test_transient_comment_queryset_excludes_followup_logs(self):
        Log.objects.filter(transient=self.transient).delete()
        create_transient_comment(
            transient=self.transient,
            comment="on transient",
            user=self.user,
            notify=False,
        )
        self.assertEqual(transient_comment_queryset(self.transient.id).count(), 1)

    def test_api_list_create_transient_comments(self):
        token, _ = Token.objects.get_or_create(user=self.user)
        list_url = reverse(
            "api-transient-comments",
            kwargs={"transient_id": self.transient.id},
        )
        response = self.client.get(
            list_url,
            HTTP_AUTHORIZATION="Token " + token.key,
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.post(
            list_url,
            {"comment": "via api", "transient": self.transient.id},
            content_type="application/json",
            HTTP_AUTHORIZATION="Token " + token.key,
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["comment"], "via api")

    def test_slack_signature_verify(self):
        secret = "test_secret"
        body = b'{"type":"url_verification","challenge":"abc"}'
        ts = str(int(time.time()))
        basestring = f"v0:{ts}:{body.decode('utf-8')}"
        digest = hmac.new(
            secret.encode(),
            basestring.encode(),
            hashlib.sha256,
        ).hexdigest()
        sig = f"v0={digest}"
        self.assertTrue(
            verify_slack_signature(secret, ts, body, sig),
        )

    @patch("YSE_App.integrations.slack.outbound.chat_post_message")
    def test_slack_outbound_when_enabled(self, mock_post):
        mock_post.return_value = {"ok": True, "ts": "123.456"}
        with self.settings(
            SLACK_ENABLED=True,
            SLACK_DEFAULT_CHANNEL_ID="C_TEST",
            SLACK_BOT_TOKEN="xoxb-test",
        ):
            log = create_transient_comment(
                transient=self.transient,
                comment="slack test",
                user=self.user,
            )
        self.assertTrue(mock_post.called)
        self.assertIsNotNone(log.id)

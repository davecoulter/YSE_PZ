from django.db import models

from YSE_App.models.transient_models import Transient


class SlackThreadLink(models.Model):
    """Maps a YSE transient to a Slack channel thread."""

    transient = models.ForeignKey(
        Transient,
        on_delete=models.CASCADE,
        related_name="slack_threads",
    )
    slack_channel_id = models.CharField(max_length=64)
    slack_thread_ts = models.CharField(max_length=32)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("transient", "slack_channel_id")

    def __str__(self):
        return f"{self.transient.name} → {self.slack_channel_id}:{self.slack_thread_ts}"

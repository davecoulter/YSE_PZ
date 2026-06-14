"""Django signals for YSE_App."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from YSE_App.common.collaboration_groups import ensure_user_has_public_group

User = get_user_model()


@receiver(post_save, sender=User, dispatch_uid="yse_ensure_user_public_group")
def add_public_group_to_user(sender, instance, created, **kwargs):
    """Every user belongs to the Public collaboration group."""
    ensure_user_has_public_group(instance)

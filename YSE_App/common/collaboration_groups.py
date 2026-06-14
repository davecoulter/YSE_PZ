"""
Collaboration group names and helpers for ingest / visibility.

``Public`` is the scrub-script collaboration group for world-readable TNS data.
"""

from __future__ import annotations

from typing import Iterable, List, Sequence, Union

PUBLIC_COLLABORATION_GROUP_NAME = "Public"

# Collaboration groups applied to photometry/spectra ingested from TNS.
TNS_IMPORT_COLLABORATION_GROUPS: Sequence[str] = (PUBLIC_COLLABORATION_GROUP_NAME,)

GroupNamesInput = Union[str, Sequence[str], None]


def normalize_collaboration_group_names(value: GroupNamesInput) -> List[str]:
    """Accept comma-separated strings or sequences of group names."""
    if not value:
        return []
    if isinstance(value, str):
        return [part.strip() for part in value.split(",") if part.strip()]
    return [str(part).strip() for part in value if str(part).strip()]


def collaboration_groups_from_photometry_upload(photometry: dict) -> List[str]:
    """Read group names from a photometry upload block (header or photdata rows)."""
    header_groups = normalize_collaboration_group_names(photometry.get("groups"))
    if header_groups:
        return header_groups
    names: set[str] = set()
    for point in photometry.get("photdata", {}).values():
        names.update(normalize_collaboration_group_names(point.get("groups")))
    return sorted(names)


def apply_collaboration_groups_to_photometry(transientphot, group_names: Iterable[str]) -> None:
    """Attach collaboration groups to a saved ``TransientPhotometry`` row."""
    from django.contrib.auth.models import Group

    if not transientphot.pk or not group_names:
        return
    for name in group_names:
        group = Group.objects.filter(name=name).first()
        if group is None:
            continue
        if not transientphot.groups.filter(pk=group.pk).exists():
            transientphot.groups.add(group)


def get_or_create_public_group():
    """Return the ``Public`` collaboration group, creating it if needed."""
    from django.contrib.auth.models import Group

    group, _ = Group.objects.get_or_create(name=PUBLIC_COLLABORATION_GROUP_NAME)
    return group


def ensure_user_has_public_group(user) -> bool:
    """
    Add ``Public`` to the user's collaboration groups if missing.

    Returns True when membership was added, False if already present.
    """
    if user is None or not getattr(user, "pk", None):
        return False
    public_group = get_or_create_public_group()
    if user.groups.filter(pk=public_group.pk).exists():
        return False
    user.groups.add(public_group)
    return True

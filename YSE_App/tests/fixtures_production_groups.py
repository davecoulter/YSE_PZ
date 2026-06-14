"""
Production-style collaboration groups for visibility / plot-cache regression tests.

Uses the same ``auth.Group`` names as the live YSE database (Public, YSE, UCSC, …),
not the synthetic ``sec-group-*`` names from the security matrix demo.
"""

from __future__ import annotations

import datetime
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

from django.contrib.auth.models import Group, User
from django.utils import timezone

from YSE_App.models import (
    PhotometricBand,
    Transient,
    TransientPhotData,
    TransientPhotometry,
)
from YSE_App.tests.fixtures_minimal import (
    attach_synthetic_host,
    audit_fields,
    create_instrument_stack,
    create_minimal_transient,
    create_test_user,
    ensure_transient_statuses,
)

# Names observed on production / scrubbed snapshots (see scrub_private_data.py).
PRODUCTION_COLLABORATION_GROUPS: Tuple[str, ...] = (
    "Public",
    "YSE",
    "UCSC",
    "LCOGT",
    "DEBASS",
    "Foundation",
    "K2",
    "KITS",
    "OUTSIDE",
    "SIRAH",
    "SOAR",
    "SSS",
    "TESS",
)

TRANSIENT_NAME = "prodgrp-vis-test"
DEFAULT_TEST_PASSWORD = "prodgrp-test-pass"

# Keys into PRODUCTION_COLLABORATION_GROUPS by short alias.
GROUP_KEYS: Dict[str, str] = {
    "public": "Public",
    "yse": "YSE",
    "ucsc": "UCSC",
    "lcogt": "LCOGT",
}

# (mag label, group key tuple — empty = legacy ungrouped / world-readable in app)
PHOTOMETRY_SERIES: Tuple[Tuple[int, Tuple[str, ...], str], ...] = (
    (0, (), "legacy-public"),
    (1, ("public",), "tagged-public"),
    (2, ("yse",), "yse-only"),
    (3, ("ucsc",), "ucsc-only"),
    (4, ("lcogt",), "lcogt-only"),
    (5, ("yse", "ucsc"), "yse-ucsc"),
    (6, ("yse", "lcogt"), "yse-lcogt"),
)

TEST_USERS: Tuple[Tuple[str, Tuple[str, ...]], ...] = (
    ("prod_user_pub_yse", ("public", "yse")),
    ("prod_user_yse", ("yse",)),
    ("prod_user_ucsc", ("ucsc",)),
    ("prod_user_lcogt", ("lcogt",)),
)

EXPECTED_MAGS_BY_USER: Dict[str, Set[int]] = {
    "prod_user_pub_yse": {0, 1, 2, 5, 6},
    "prod_user_yse": {0, 2, 5, 6},
    "prod_user_ucsc": {0, 3, 5},
    "prod_user_lcogt": {0, 4, 6},
}


def ensure_production_groups(
    names: Iterable[str] = PRODUCTION_COLLABORATION_GROUPS,
) -> Dict[str, Group]:
    """Get or create collaboration groups using production names."""
    groups: Dict[str, Group] = {}
    for name in names:
        groups[name], _ = Group.objects.get_or_create(name=name)
    return groups


def _resolve_group_keys(
    group_keys: Sequence[str],
    groups_by_name: Dict[str, Group],
) -> List[Group]:
    resolved = []
    for key in group_keys:
        name = GROUP_KEYS[key]
        resolved.append(groups_by_name[name])
    return resolved


def create_production_group_test_users(
    *,
    password: str = DEFAULT_TEST_PASSWORD,
    groups_by_name: Optional[Dict[str, Group]] = None,
) -> Dict[str, User]:
    if groups_by_name is None:
        groups_by_name = ensure_production_groups(
            {GROUP_KEYS[k] for _, keys, _ in PHOTOMETRY_SERIES for k in keys}
        )
    users: Dict[str, User] = {}
    for username, group_keys in TEST_USERS:
        user = create_test_user(username, is_staff=False)
        user.set_password(password)
        user.save(update_fields=["password"])
        user.groups.set(_resolve_group_keys(group_keys, groups_by_name))
        users[username] = user
    return users


def _series_reference(mag: int) -> str:
    return f"prodgrp-vis-mag-{mag}"


def _attach_labeled_series(
    admin: User,
    transient: Transient,
    *,
    mag: int,
    group_keys: Sequence[str],
    band_suffix: str,
    groups_by_name: Dict[str, Group],
) -> TransientPhotometry:
    audit = audit_fields(admin)
    obs_group, instrument, _ = create_instrument_stack(
        admin, obs_group_name=f"prodgrp-{band_suffix}"
    )
    band_name = f"r-{band_suffix}"
    band, _ = PhotometricBand.objects.get_or_create(
        name=band_name,
        defaults={
            "instrument": instrument,
            "disp_color": "#DC143C",
            "disp_symbol": "circle",
            **audit,
        },
    )

    reference = _series_reference(mag)
    photometry, _ = TransientPhotometry.objects.update_or_create(
        transient=transient,
        reference=reference,
        defaults={
            "instrument": instrument,
            "obs_group": obs_group,
            **audit,
        },
    )
    photometry.groups.clear()
    for group in _resolve_group_keys(group_keys, groups_by_name):
        photometry.groups.add(group)

    obs_date = timezone.now() - datetime.timedelta(days=mag + 1)
    TransientPhotData.objects.filter(photometry=photometry).delete()
    TransientPhotData.objects.create(
        photometry=photometry,
        band=band,
        obs_date=obs_date,
        mag=float(mag),
        mag_err=0.01,
        discovery_point=(mag == 0),
        **audit,
    )
    return photometry


def create_production_group_vis_transient(admin: User) -> Transient:
    ensure_transient_statuses(admin)
    groups_by_name = ensure_production_groups(
        {GROUP_KEYS[k] for _, keys, _ in PHOTOMETRY_SERIES for k in keys}
    )
    transient = create_minimal_transient(
        admin,
        name=TRANSIENT_NAME,
        obs_group_name="prodgrp-survey",
        ra=151.0,
        dec=3.0,
    )
    attach_synthetic_host(admin, transient, name=f"host-{TRANSIENT_NAME}")

    for mag, group_keys, band_suffix in PHOTOMETRY_SERIES:
        _attach_labeled_series(
            admin,
            transient,
            mag=mag,
            group_keys=group_keys,
            band_suffix=band_suffix,
            groups_by_name=groups_by_name,
        )
    return transient


def seed_production_group_vis_fixture(
    *,
    password: str = DEFAULT_TEST_PASSWORD,
) -> Tuple[Transient, Dict[str, User]]:
    admin = create_test_user("prodgrp_admin", is_staff=True)
    users = create_production_group_test_users(password=password)
    transient = create_production_group_vis_transient(admin)
    return transient, users


def authorized_mags_for_user(user: User, transient_id: int) -> Set[int]:
    from YSE_App.data import PhotometryService

    photdata = PhotometryService.GetAuthorizedTransientPhotData_ByUser_ByTransient(
        user, transient_id, includeBadData=True
    )
    mags: Set[int] = set()
    for row in photdata:
        if row.mag is not None:
            mags.add(int(round(float(row.mag))))
    return mags

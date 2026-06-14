"""
Security visibility demo: four users, one transient, mag-labeled photometry.

Magnitude on each point equals its test ID (0 = public, 1 = group A only, …).
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

TRANSIENT_NAME = "secvis-matrix"
DEFAULT_TEST_PASSWORD = "sec-test-pass"

GROUP_NAMES = {
    "a": "sec-group-a",
    "b": "sec-group-b",
    "c": "sec-group-c",
    "d": "sec-group-d",
}

# (mag label, collaboration group keys, band suffix for legend)
PHOTOMETRY_SERIES: Tuple[Tuple[int, Tuple[str, ...], str], ...] = (
    (0, (), "public"),
    (1, ("a",), "grpA"),
    (2, ("b",), "grpB"),
    (3, ("c",), "grpC"),
    (4, ("d",), "grpD"),
    (5, ("a", "b"), "grpAB"),
    (6, ("a", "c"), "grpAC"),
    (7, ("b", "c"), "grpBC"),
)

TEST_USERS: Tuple[Tuple[str, Tuple[str, ...]], ...] = (
    ("sec_user_ab", ("a", "b")),
    ("sec_user_ac", ("a", "c")),
    ("sec_user_b", ("b",)),
    ("sec_user_d", ("d",)),
)

# Expected magnitudes visible on the LC plot per test user.
EXPECTED_MAGS_BY_USER: Dict[str, Set[int]] = {
    "sec_user_ab": {0, 1, 2, 5, 6, 7},
    "sec_user_ac": {0, 1, 3, 5, 6, 7},
    "sec_user_b": {0, 2, 5, 7},
    "sec_user_d": {0, 4},
}


def ensure_security_groups() -> Dict[str, Group]:
    groups = {}
    for key, name in GROUP_NAMES.items():
        groups[key], _ = Group.objects.get_or_create(name=name)
    return groups


def create_security_test_users(
    *,
    password: str = DEFAULT_TEST_PASSWORD,
) -> Dict[str, User]:
    groups = ensure_security_groups()
    users: Dict[str, User] = {}
    for username, group_keys in TEST_USERS:
        user = create_test_user(username, is_staff=False)
        user.set_password(password)
        user.save(update_fields=["password"])
        user.groups.set([groups[k] for k in group_keys])
        users[username] = user
    return users


def _series_reference(mag: int) -> str:
    return f"secvis-matrix-mag-{mag}"


def _attach_labeled_series(
    admin: User,
    transient: Transient,
    *,
    mag: int,
    group_keys: Sequence[str],
    band_suffix: str,
    groups: Dict[str, Group],
) -> TransientPhotometry:
    audit = audit_fields(admin)
    obs_group, instrument, _default_band = create_instrument_stack(
        admin, obs_group_name=f"secvis-{band_suffix}"
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
    for key in group_keys:
        photometry.groups.add(groups[key])

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


def create_secvis_matrix_transient(admin: User) -> Transient:
    """Idempotent: one transient with mag-labeled public/private photometry."""
    ensure_transient_statuses(admin)
    groups = ensure_security_groups()
    transient = create_minimal_transient(
        admin,
        name=TRANSIENT_NAME,
        obs_group_name="secvis-matrix-survey",
        ra=150.0,
        dec=2.5,
    )
    attach_synthetic_host(admin, transient, name=f"host-{TRANSIENT_NAME}")

    for mag, group_keys, band_suffix in PHOTOMETRY_SERIES:
        _attach_labeled_series(
            admin,
            transient,
            mag=mag,
            group_keys=group_keys,
            band_suffix=band_suffix,
            groups=groups,
        )
    return transient


def seed_security_test_matrix(
    *,
    password: str = DEFAULT_TEST_PASSWORD,
) -> Tuple[Transient, Dict[str, User]]:
    admin = create_test_user("sec_admin", is_staff=True)
    users = create_security_test_users(password=password)
    transient = create_secvis_matrix_transient(admin)
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

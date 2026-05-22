"""Minimal ORM rows for page-load and performance tests."""

import datetime

from django.contrib.auth.models import User
from django.utils import timezone

from YSE_App.models import (
    Host,
    Instrument,
    Log,
    ObservationGroup,
    Observatory,
    PhotometricBand,
    Telescope,
    Transient,
    TransientPhotData,
    TransientPhotometry,
    TransientSpectrum,
    TransientStatus,
    UserQuery,
)

# Status names used by dashboard and transient_detail views.
TRANSIENT_STATUSES = (
    "New",
    "FollowupRequested",
    "Following",
    "Interesting",
    "Watch",
    "FollowupFinished",
    "NeedsTemplate",
    "Ignore",
)


def audit_fields(user):
    return {"created_by": user, "modified_by": user}


def ensure_transient_statuses(user):
    statuses = {}
    audit = audit_fields(user)
    for name in TRANSIENT_STATUSES:
        statuses[name], _ = TransientStatus.objects.get_or_create(
            name=name, defaults=audit
        )
    return statuses


def create_test_user(username="perf_test_user", **user_defaults):
    defaults = {"email": f"{username}@example.com", "is_staff": True}
    defaults.update(user_defaults)
    user, _ = User.objects.get_or_create(username=username, defaults=defaults)
    return user


def create_instrument_stack(user, *, obs_group_name="perf-test-group"):
    """Observatory → telescope → instrument → r band for synthetic photometry."""
    audit = audit_fields(user)
    obs_group, _ = ObservationGroup.objects.get_or_create(
        name=obs_group_name, defaults=audit
    )
    observatory, _ = Observatory.objects.get_or_create(
        name=f"PerfObs-{obs_group_name}",
        defaults={"utc_offset": 0, "tz_name": "UTC", **audit},
    )
    telescope, _ = Telescope.objects.get_or_create(
        name=f"PerfTel-{obs_group_name}",
        defaults={
            "observatory": observatory,
            "latitude": 0.0,
            "longitude": 0.0,
            "elevation": 0.0,
            **audit,
        },
    )
    instrument, _ = Instrument.objects.get_or_create(
        name=f"PerfInst-{obs_group_name}",
        defaults={"telescope": telescope, **audit},
    )
    band, _ = PhotometricBand.objects.get_or_create(
        name=f"r-{obs_group_name}",
        defaults={
            "instrument": instrument,
            "disp_color": "#ff0000",
            "disp_symbol": "circle",
            **audit,
        },
    )
    return obs_group, instrument, band


def attach_synthetic_photometry(
    user,
    transient,
    *,
    obs_group=None,
    instrument=None,
    band=None,
    n_points=12,
):
    """Synthetic light-curve points (sequential dates, one discovery point)."""
    audit = audit_fields(user)
    if obs_group is None or instrument is None or band is None:
        obs_group, instrument, band = create_instrument_stack(
            user, obs_group_name=f"phot-{transient.name}"
        )
    photometry = TransientPhotometry.objects.create(
        transient=transient,
        instrument=instrument,
        obs_group=obs_group,
        **audit,
    )
    base_date = timezone.now() - datetime.timedelta(days=n_points)
    points = []
    for i in range(n_points):
        points.append(
            TransientPhotData(
                photometry=photometry,
                band=band,
                obs_date=base_date + datetime.timedelta(days=i),
                mag=18.0 + 0.05 * i,
                mag_err=0.1,
                discovery_point=(i == 0),
                **audit,
            )
        )
    TransientPhotData.objects.bulk_create(points)
    return photometry


def attach_synthetic_host(user, transient, *, name=None):
    audit = audit_fields(user)
    host = Host.objects.create(
        ra=transient.ra,
        dec=transient.dec,
        name=name or f"host-{transient.name}",
        redshift=0.05,
        **audit,
    )
    transient.host = host
    transient.save(update_fields=["host"])
    return host


def attach_synthetic_spectrum(user, transient, *, obs_group=None, instrument=None):
    audit = audit_fields(user)
    if obs_group is None or instrument is None:
        obs_group, instrument, _ = create_instrument_stack(
            user, obs_group_name=f"spec-{transient.name}"
        )
    return TransientSpectrum.objects.create(
        transient=transient,
        instrument=instrument,
        obs_group=obs_group,
        ra=transient.ra,
        dec=transient.dec,
        obs_date=timezone.now(),
        redshift=0.05,
        **audit,
    )


def attach_synthetic_log(user, transient, comment="Synthetic perf-test log entry."):
    audit = audit_fields(user)
    return Log.objects.create(transient=transient, comment=comment, **audit)


def create_transient_with_synthetic_data(
    user,
    name="perf-detail-sn",
    *,
    status_name="New",
    n_phot_points=12,
    with_host=True,
    with_spectrum=True,
    with_log=True,
):
    """
    Transient detail page with realistic related rows (synthetic photometry, etc.).
    """
    audit = audit_fields(user)
    statuses = ensure_transient_statuses(user)
    obs_group, instrument, band = create_instrument_stack(
        user, obs_group_name=f"bundle-{name}"
    )
    transient, _ = Transient.objects.get_or_create(
        name=name,
        defaults={
            "ra": 10.0,
            "dec": 20.0,
            "status": statuses[status_name],
            "obs_group": obs_group,
            "disc_date": timezone.now() - datetime.timedelta(days=5),
            **audit,
        },
    )
    if not transient.slug:
        transient.save()
    attach_synthetic_photometry(
        user,
        transient,
        obs_group=obs_group,
        instrument=instrument,
        band=band,
        n_points=n_phot_points,
    )
    if with_host:
        attach_synthetic_host(user, transient)
    if with_spectrum:
        attach_synthetic_spectrum(
            user, transient, obs_group=obs_group, instrument=instrument
        )
    if with_log:
        attach_synthetic_log(user, transient)
    transient.refresh_from_db()
    return transient


def create_minimal_transient(
    user,
    name="perf-test-sn",
    *,
    status_name="New",
    obs_group_name="perf-test-group",
    ra=10.0,
    dec=20.0,
):
    """One transient with no photometry (detail page shell only)."""
    audit = audit_fields(user)
    statuses = ensure_transient_statuses(user)
    obs_group, _ = ObservationGroup.objects.get_or_create(
        name=obs_group_name, defaults=audit
    )
    transient, _ = Transient.objects.get_or_create(
        name=name,
        defaults={
            "ra": ra,
            "dec": dec,
            "status": statuses[status_name],
            "obs_group": obs_group,
            **audit,
        },
    )
    if not transient.slug:
        transient.save()
    return transient


def seed_dashboard_transients(user, count_per_status=1):
    """A few transients so dashboard tables have rows to render."""
    statuses = ensure_transient_statuses(user)
    audit = audit_fields(user)
    obs_group, _ = ObservationGroup.objects.get_or_create(
        name="perf-dashboard-group", defaults=audit
    )
    created = []
    for status_name, status in statuses.items():
        for i in range(count_per_status):
            name = f"perf-{status_name.lower()}-{i}"
            t, _ = Transient.objects.get_or_create(
                name=name,
                defaults={
                    "ra": 10.0 + i * 0.01,
                    "dec": 20.0,
                    "status": status,
                    "obs_group": obs_group,
                    **audit,
                },
            )
            created.append(t)
    return created


def seed_personal_dashboard_queries(user, n_queries=5):
    """
    Mimic a user's saved dashboard: N explorer SQL queries, each returning one transient.

    Matches production pattern where personaldashboard runs each UserQuery SQL once
    (cached under user_query_<id> for 1 hour).
    """
    from explorer.models import Query

    ensure_transient_statuses(user)
    audit = audit_fields(user)
    user_queries = []

    for i in range(n_queries):
        transient = create_minimal_transient(
            user,
            name=f"perf-pdash-q{i}",
            obs_group_name="perf-pdash-group",
            ra=10.0 + i * 0.01,
        )
        sql = (
            "SELECT name FROM YSE_App_transient "
            f"WHERE name = '{transient.name}'"
        )
        explorer_query = Query.objects.create(
            title=f"Perf dashboard query {i}",
            sql=sql,
            description="Synthetic personal-dashboard query for perf tests",
            snapshot=False,
            created_by_user=user,
        )
        user_queries.append(
            UserQuery.objects.create(
                user=user, query=explorer_query, **audit
            )
        )
    return user_queries


def seed_explorer_query_catalog(user, n_queries=50, *, with_query_logs=False):
    """
    Populate django-sql-explorer Query rows for /explorer/ list page tests.

    SQL is not executed on the index view. With with_query_logs=True, also creates
    QueryLog rows so ListQueryView's per-row querylog_set.count() matches production N+1.
    """
    from explorer.models import Query, QueryLog

    catalog = []
    for i in range(n_queries):
        q = Query.objects.create(
            title=f"Perf explorer - query {i}",
            sql="SELECT name FROM YSE_App_transient WHERE 1=0",
            description="Synthetic catalog row for explorer index perf tests",
            snapshot=False,
            created_by_user=user,
        )
        catalog.append(q)
        if with_query_logs:
            QueryLog.objects.create(
                query=q,
                sql=q.sql,
                run_by_user=user,
                duration=0.0,
            )
    return catalog

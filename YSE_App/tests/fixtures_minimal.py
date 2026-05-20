"""Minimal ORM rows for page-load and performance tests."""

from django.contrib.auth.models import User

from YSE_App.models import ObservationGroup, Transient, TransientStatus

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
    transient, created = Transient.objects.get_or_create(
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

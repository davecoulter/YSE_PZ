"""
Collect multi-resource waterfalls with real start/end offsets on a page timeline.

Scheduling models browser behavior:
  - Document first (t=0)
  - Blocking/head JS in parallel with document where applicable
  - Deferred section XHRs in parallel after document (personal/main dashboard)
  - Transient detail: document + bokeh parallel, then main-tab XHR wave in parallel
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple
from unittest.mock import patch

from django.test import Client, override_settings

from YSE_App.perf.resource_timing import (
    PageLoadTimeline,
    ResourceTiming,
    profile_request,
    profile_request_optional,
    schedule_parallel,
)
from YSE_App.tests.fixtures_minimal import (
    create_test_user,
    create_transient_with_synthetic_data,
    seed_dashboard_transients,
    seed_personal_dashboard_queries,
)
from YSE_App.views import _DASHBOARD_STATUS_SECTIONS

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

UrlSpec = Tuple[str, str, str]  # url, name, resource_type


@override_settings(PASSWORD_HASHERS=PASSWORD_HASHERS)
def collect_all_waterfalls() -> Dict[str, List[ResourceTiming]]:
    timelines = collect_all_timelines()
    return {k: t.resources for k, t in timelines.items()}


@override_settings(PASSWORD_HASHERS=PASSWORD_HASHERS)
def collect_all_timelines() -> Dict[str, PageLoadTimeline]:
    return {
        "main_dashboard": _timeline_main_dashboard(),
        "personal_dashboard": _timeline_personal_dashboard(),
        "transient_detail": _timeline_transient_detail(),
    }


def _measure_batch(
    client: Client, specs: List[UrlSpec]
) -> List[ResourceTiming]:
    rows: List[ResourceTiming] = []
    for url, name, rtype in specs:
        row = profile_request_optional(client, url, name=name, resource_type=rtype)
        if row:
            rows.append(row)
    return rows


def _timeline_main_dashboard() -> PageLoadTimeline:
    user = create_test_user("perf_wf_mdash")
    client = Client()
    client.force_login(user)
    seed_dashboard_transients(user, count_per_status=1)

    doc = profile_request(
        client, "/dashboard/", name="dashboard", resource_type="document"
    )
    doc.place_on_timeline(0.0)

    section_specs: List[UrlSpec] = []
    for _title, statusname in _DASHBOARD_STATUS_SECTIONS:
        if statusname == "New":
            continue
        key = statusname.lower()
        section_specs.append(
            (f"/dashboard/section/{key}/", f"section:{key}", "xhr")
        )
    sections = _measure_batch(client, section_specs)
    doc_end = doc.end_ms
    schedule_parallel(sections, doc_end)

    resources = [doc] + sections
    return PageLoadTimeline(
        page_key="main_dashboard",
        resources=resources,
        schedule_note=(
            f"document [0, {doc_end:.0f}ms]; "
            f"{len(sections)} section XHRs parallel from {doc_end:.0f}ms"
        ),
    )


def _timeline_personal_dashboard() -> PageLoadTimeline:
    import YSE_App.views as views_module
    from django.core.cache import cache
    from django.db import connections

    user = create_test_user("perf_wf_pdash")
    client = Client()
    client.force_login(user)
    user_queries = seed_personal_dashboard_queries(user, n_queries=5)
    cache.clear()

    doc = profile_request(
        client,
        "/personaldashboard/",
        name="personaldashboard",
        resource_type="document",
    )
    doc.place_on_timeline(0.0)
    doc_end = doc.end_ms

    section_specs = [
        (f"/personaldashboard/section/{uq.id}/", f"section:q{uq.id}", "xhr")
        for uq in user_queries
    ]

    class _ConnectionsForTests:
        def __getitem__(self, alias):
            if alias == "explorer":
                return connections["default"]
            return connections[alias]

    with patch.object(views_module, "connections", _ConnectionsForTests()):
        sections = _measure_batch(client, section_specs)
    schedule_parallel(sections, doc_end)

    return PageLoadTimeline(
        page_key="personal_dashboard",
        resources=[doc] + sections,
        schedule_note=(
            f"shell document [0, {doc_end:.0f}ms]; "
            f"{len(sections)} sections parallel from {doc_end:.0f}ms"
        ),
    )


def _timeline_transient_detail() -> PageLoadTimeline:
    user = create_test_user("perf_wf_tdetail")
    client = Client()
    client.force_login(user)
    transient = create_transient_with_synthetic_data(
        user, name="perf-waterfall-loaded", n_phot_points=12
    )
    pk = transient.id
    slug = transient.slug

    doc = profile_request(
        client,
        f"/transient_detail/{slug}/",
        name=slug,
        resource_type="document",
    )
    doc.place_on_timeline(0.0)

    # Bokeh script in page <head> — overlaps document parse/download.
    bokeh = profile_request_optional(
        client,
        "/static/YSE_App/bokeh-2.4.2.min.js",
        name="bokeh-2.4.2.min.js",
        resource_type="js",
    )
    if bokeh:
        bokeh.place_on_timeline(0.0)

    # document.ready handlers fire XHR/plot requests together (template ~L2469+).
    parallel_after_doc = _measure_batch(
        client,
        [
            (f"/lightcurveplot_detail/{pk}/", f"lightcurveplot_detail/{pk}", "xhr"),
            (f"/spectrumplot/{pk}/", f"spectrumplot/{pk}", "xhr"),
            (f"/get_ps1_image/{pk}/", f"get_ps1_image/{pk}", "xhr"),
            (f"/get_legacy_image/{pk}/", f"get_legacy_image/{pk}", "xhr"),
        ],
    )
    html_ready_ms = max(doc.end_ms, bokeh.end_ms if bokeh else 0.0)
    schedule_parallel(parallel_after_doc, html_ready_ms)

    resources: List[ResourceTiming] = [doc]
    if bokeh:
        resources.append(bokeh)
    resources.extend(parallel_after_doc)

    return PageLoadTimeline(
        page_key="transient_detail",
        resources=resources,
        schedule_note=(
            f"document + bokeh from 0ms; "
            f"{len(parallel_after_doc)} XHRs parallel from {html_ready_ms:.0f}ms "
            "(after max(document, bokeh))"
        ),
    )

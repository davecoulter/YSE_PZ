# YSE speed improvements (progressive loading)

**Canonical repo tracker** for the performance program on branch `perf/progressive-loading`.

**Full design spec (architecture, tab matrix, phased follow-up, infra):** Cursor plan `yse_speed_improvements_07b82bf7.plan.md` (`.cursor/plans/` on your machine: `yse_speed_improvements_07b82bf7.plan.md`). This file is the **repo mirror** for execution status, metrics, and runbooks.

**Execution checklist (phases + CI gate):** Cursor plan `yse_progressive_loading_perf_7f163f3a.plan.md`.

---

## Strategy

Load **something useful immediately** (Progressive First Paint), then fill heavy sections in the background. Optimize server work in parallel, but prioritize **perceived speed** (document TTFB) over speeding up one monolithic request.

**Branch:** `perf/progressive-loading` from `yse/develop` + merged `fix/spectrumplot-regression` (PR [#14](https://github.com/Young-Supernova-Experiment/YSE_PZ/pull/14) equivalent). PR #14 can land on `develop` independently.

**Key commits:** `40dd5528` (harness + PFP), `3e65b01c` (CI on perf branch), `ae363b18` (benchmark test DB), `a3e94e08` (transient PFP + phased follow-up), `803a5a17` (plot cache + downsample).

```bash
git fetch yse develop fix/spectrumplot-regression perf/progressive-loading
git checkout perf/progressive-loading
```

---

## Master phase tracker

| Phase | Work | Status | Notes |
|-------|------|--------|-------|
| 0a | Branch + spectrumplot merge | **done** | |
| 0b | Baseline speed test + `metrics_history` iteration 0 | **done** | `baseline-pre-pfp`; gate before other commits |
| 0b | Benchmark harness + CI regression + static `perf/` | **done** | `record_perf_benchmark`, `test_page_load_regression` |
| 1 | `YSE_VIEW_TIMING` instrumentation | **done** | `YSE_App/perf/view_timing.py`; personal dashboard shell |
| 2 | Personal dashboard PFP | **done** | `YSE_PERSONAL_DASHBOARD_DEFER=1`; `/personaldashboard/section/<id>/` |
| 3 | Main dashboard PFP | **done** | `YSE_MAIN_DASHBOARD_DEFER=1`; “New” sync + `/dashboard/section/<status>/` |
| 4a | Transient detail slim shell | **done** | `YSE_TRANSIENT_DETAIL_DEFER=1` |
| 4b | Main-tab plots + cutouts (parallel AJAX) | **done** | LC, spectrum, PS1, Legacy on `document.ready` |
| 4c | HST/Chandra status probes + images on tab click | **done** | `get_hst_status`, `get_chandra_status`; full fetch on tab |
| 4d | Follow-up tab phased load | **done** | requests → **classical** → ToO/automated; background + tab click |
| 4e | Rare tabs click-to-load only | **done** | Comments, GW, Spectra tab + summary spectrum tools via fragments |
| 4f / 7 | LC/spectrum plot optimizations | **done** | DQ prefetch, downsample, HTML cache (`803a5a17`) |
| 5 | ORM explicit prefetch audit | **partial** | Hot paths in PFP/plots; django-auto-prefetch **deferred** (Django 4.0) |
| 5c | nplusone / debug-toolbar / Silk (local staging) | **optional** | See [Profiling tools](#profiling-tools-debug-toolbar--silk) |
| 6 | Apache / Gunicorn / Redis infra checklist | **pending** | See [Infra checklist](#infra-checklist-yse_test--ziggy) |
| 7 | ziggy / `yse_test` validation | **pending** | Before/after TTFB on real deploy |

---

## Production baseline (`yse_test`, pre-PFP)

Measured server **Waiting** (motivation for this work):

| Endpoint | TTFB (approx) | Behavior before PFP |
|----------|---------------|------------------------|
| `/personaldashboard/` | ~10.9 s | All saved SQL + all tables before HTML |
| `/dashboard/` | ~11.1 s | Seven status sections built synchronously |
| `/transient_detail/<slug>/` | ~6.2 s | Large sync context; plots via separate AJAX |
| `/lightcurveplot_detail/<id>/` | ~4.3 s | Heavy phot + Bokeh `file_html` |
| `/spectrumplot/<id>/` | 500 (fixed on branch) | Plot endpoint regression (PR #14) |

**Targets after PFP:**

| Metric | Target |
|--------|--------|
| Dashboard / personal **document** TTFB | &lt; 1.5 s (shell + placeholders) |
| Personal section fragments | Stream in parallel; page usable immediately |
| Transient detail **document** TTFB | &lt; 1.5 s (core main-tab info only) |
| Main-tab plot AJAX (each) | &lt; 2–4 s; downsampled for display |

---

## Docker fixture metrics (`metrics_history.json`)

| Iteration | main_dashboard | personal_dashboard | transient_detail |
|-----------|----------------|-------------------|------------------|
| `baseline-pre-pfp` (sync) | 150 ms, 19 q | 172 ms, 23 q | 416 ms, 66 q |
| `personal-pfp` | 356 ms, 19 q | **136 ms**, 8 q | 363 ms, 229 q |
| `transient-detail-pfp` | — | — | **176 ms**, 40 q (document) |
| `plot-optimizations` | — | — | document ~282 ms; LC cache + downsample |

Personal deferred shell ≈ **21%** of sync cold path. Transient document TTFB **~58%** lower than baseline (416 → 176 ms).

**CI regression** (`YSE_App/tests/perf_baselines.json`, 20% tolerance): personal ≤200 ms, main ≤250 ms, transient ≤250 ms.

**Artifacts:** `YSE_App/static/YSE_App/perf/metrics_history.json`, `waterfall_*.png`, `trend_*.png` — served at `/static/YSE_App/perf/…`.

---

## Implemented: progressive loading

### Personal dashboard

- **Flag:** `YSE_PERSONAL_DASHBOARD_DEFER=1` (default)
- **Shell:** `/personaldashboard/` — query list only, no explorer SQL
- **Fragments:** `/personaldashboard/section/<query_id>/` — parallel `$.get` from template

### Main dashboard

- **Flag:** `YSE_MAIN_DASHBOARD_DEFER=1` (default)
- **Shell:** `/dashboard/` — “New Transients” sync only
- **Fragments:** `/dashboard/section/<status>/`

### Transient detail

- **Flag:** `YSE_TRANSIENT_DETAIL_DEFER=1` (default)
- **Shell:** `/transient_detail/<slug>/` — core main tab, lightweight mag summary; no sync follow-ups, bulk photometry, resource tables, HST/Chandra images
- **Tab fragments:**
  - `/transient_detail/<id>/followup_fragment/` — past requests + observation tasks
  - `/transient_detail/<id>/followup_classical_fragment/` — classical resource form (**phase 2, prioritized**)
  - `/transient_detail/<id>/followup_rest_fragment/` — follow-up + obs-task + ToO + automated spectrum forms
  - `/transient_detail/<id>/resources_fragment/` — classical/ToO resource tables
  - `/transient_detail/<id>/photometry_fragment/` — photometry + diff-image tables
  - `/transient_detail/<id>/comments_fragment/` — comment history (form stays in shell)
  - `/transient_detail/<id>/gw_fragment/` — GW candidate table (tab shown when `GW Candidate` tag)
  - `/transient_detail/<id>/spectra_tab_fragment/` — spectra list table
  - `/transient_detail/<id>/summary_spectra_tools_fragment/` — Summary tab spectrum dropdown (background)
- **HST/Chandra:** `get_hst_status`, `get_chandra_status` on load; `get_hst_image` / `get_chandra_image` on tab click only
- **Follow-up load order:** (1) requests → (2) classical → (3) rest; `setTimeout(0)` after main-tab plot XHRs start

### Tab loading matrix (target vs shipped)

| Tab / area | Policy | Shipped |
|------------|--------|---------|
| Main (core) | Sync in shell | Yes |
| Main (LC, spectrum, cutouts) | Parallel AJAX after shell | Yes |
| HST / Chandra (label) | Lightweight probe | Yes |
| HST / Chandra (images) | Tab click only | Yes |
| Follow-up | Phased background; classical before ToO/automated | Yes |
| Resources, Detailed photometry | Tab click (fragment) | Yes |
| Logs, GW, Spectra list | Click-to-load / background fragment | Yes |

---

## Implemented: benchmark harness

| Path | Role |
|------|------|
| `YSE_App/perf/benchmark.py` | Measure three primary pages |
| `YSE_App/perf/waterfall_collect.py` | Multi-resource timelines (browser-style) |
| `YSE_App/perf/plots.py` | Waterfall + trend PNGs |
| `YSE_App/perf/test_db.py` | Migrated test DB for `record_perf_benchmark` |
| `YSE_App/management/commands/record_perf_benchmark.py` | CLI `--label` |
| `YSE_App/tests/test_performance.py` | Query/time ceilings |
| `YSE_App/tests/test_page_load_regression.py` | TTFB vs `perf_baselines.json` |
| `docker/scripts/run-baseline-benchmark.sh` | Compose up → test → benchmark → down → prune |

**Waterfall semantics:** shared time axis per resource (`start_ms` → `end_ms`); `page_load_total_ms` = critical path (latest `end_ms`). See master plan § Phase 0b for scheduling rules (document first; parallel sections/XHRs after shell).

---

## Feature flags and plot tuning

| Env | Default | Effect |
|-----|---------|--------|
| `YSE_PERSONAL_DASHBOARD_DEFER` | `1` | Personal shell + AJAX sections |
| `YSE_MAIN_DASHBOARD_DEFER` | `1` | Main dashboard: “New” only sync |
| `YSE_TRANSIENT_DETAIL_DEFER` | `1` | Transient shell + tab fragments; HST/Chandra on tab click |
| `YSE_PERSONAL_DASHBOARD_DEFER` | `0` | Legacy sync (performance tests) |
| `YSE_MAIN_DASHBOARD_DEFER` | `0` | Legacy full dashboard (performance tests) |
| `YSE_TRANSIENT_DETAIL_DEFER` | `0` | Legacy full transient detail (performance tests) |
| `YSE_VIEW_TIMING` | off | Per-section timing logs |
| `YSE_PLOT_HTML_CACHE` | `1` | Cache LC/spectrum plot HTML (900 s TTL) |
| `YSE_LC_PLOT_MAX_POINTS` | `3000` | Downsample photometry for LC display |
| `YSE_SPEC_PLOT_MAX_PIXELS` | `800` | Cap spectrum interpolation pixels |
| `YSE_PERF_SKIP_TIMING` | off | Skip wall-time assertions in `test_performance` |
| `YSE_PERF_RECORD_PATH` | — | Optional JSON export from perf tests |

---

## How to run

### Docker protocol (mandatory between test series)

Do **not** reuse images between series. Mirrors [`.github/workflows/ci.yml`](../.github/workflows/ci.yml).

```bash
export DOCKER_HOST=unix://$HOME/.docker/run/docker.sock
# If pull fails on credentials:
# export DOCKER_CONFIG=/tmp/docker-nocreds

cd docker
YSE_DOCKER_PRUNE=0 docker compose up -d

docker exec ysepz_web_container python3 manage.py test \
  YSE_App.tests.test_performance \
  YSE_App.tests.test_page_load_regression \
  YSE_App.tests.test_lightcurve \
  YSE_App.tests.test_post_merge_hotfix -v2

docker exec ysepz_web_container python3 manage.py record_perf_benchmark --label my-iteration

docker compose down -v
bash scripts/prune-yse-docker.sh aggressive
```

Shortcut: `bash docker/scripts/run-baseline-benchmark.sh [label]`

### Apple Silicon notes

Use `DOCKER_HOST=unix://$HOME/.docker/run/docker.sock`. Empty `DOCKER_CONFIG` if credential helper errors.

---

## Remaining work

### Phase 4e — Rare transient tabs (click-to-load) — **done**

Fragments: `comments_fragment`, `gw_fragment`, `spectra_tab_fragment`, `summary_spectra_tools_fragment` (background after shell). Deferred shell skips full `Log` list and GW ORM; `new_comment` uses a single `.exists()` query.

### Profiling tools (debug-toolbar / Silk)

| Tool | Helps find improvements? | This repo (Django 4.0) |
|------|--------------------------|-------------------------|
| [django-debug-toolbar](https://github.com/django-commons/django-debug-toolbar) | Yes — SQL panel, templates, timing per request | **Latest (6.x) requires Django ≥ 5.2.** Use **4.2.x** locally with `DEBUG=1` only; never on production. |
| [django-silk](https://github.com/jazzband/django-silk) | Yes — request profiling, SQL analysis, stored history | Compatible with Django 4.x; **staging/local only** (DB overhead, `/silk/` UI). |
| **Already in tree** | `YSE_VIEW_TIMING`, `test_performance` query ceilings, `record_perf_benchmark`, waterfalls | Preferred for this branch — safe in CI and repeatable. |

Recommendation: use existing perf tests + optional **Silk or debug-toolbar 4.2** on a local/staging container when exploring new N+1s; do not add either to production ziggy without `DEBUG`/access controls.

### Phase 5 — ORM / tooling

- **Done ad hoc:** prefetch on dashboard annotations, LC/spectrum, transient fragments
- **Deferred:** [django-auto-prefetch](https://pypi.org/project/django-auto-prefetch/) until Django 4.2+ (project on Django 4.0)
- **Optional:** [nplusone](https://pypi.org/project/nplusone/) in CI; debug-toolbar local only
- **Avoid:** django-cachalot on explorer SQL paths

### Phase 6 — Infra checklist (`yse_test` / ziggy)

| Layer | Check | Action |
|-------|-------|--------|
| **Apache** | gzip for HTML fragments | Enable `mod_deflate` for `text/html` |
| **Apache** | KeepAlive | Tune `KeepAliveTimeout` vs Gunicorn |
| **Apache** | Proxy timeout | Align with fragment max (~60 s); shell &lt; 5 s |
| **Apache** | Static files | Serve `/static/` from Apache, not Django |
| **Gunicorn** | Workers × threads | ≥2 workers; scale if parallel fragments queue |
| **Gunicorn** | `--timeout` | &gt; slowest plot fragment, not shell |
| **Redis** | `REDIS_URL` | Fragment/name-list + plot HTML cache across workers |
| **MySQL** | Explorer timeout | `max_execution_time` for personal SQL sections |
| **TLS** | Mixed-content cutouts | Prefer `https://` cutout URLs where supported |

Confirm on deploy: `REDIS_URL`, Gunicorn workers, `CONN_MAX_AGE`.

### Phase 7 — Production validation

1. Deploy `perf/progressive-loading` to `yse_test` / ziggy.
2. Record document TTFB (Safari Network or harness against prod URLs) for:
   - `/personaldashboard/`
   - `/dashboard/`
   - `/transient_detail/<representative-slug>/`
3. Append iteration to `metrics_history.json` (label e.g. `ziggy-post-pfp`).
4. Compare to [Production baseline](#production-baseline-yse_test-pre-pfp).

**Automated gate (each PR iteration):**

```bash
docker exec ysepz_web_container python3 manage.py test \
  YSE_App.tests.test_performance \
  YSE_App.tests.test_post_merge_hotfix \
  YSE_App.tests.test_page_load_regression -v2
docker exec ysepz_web_container python3 manage.py record_perf_benchmark
```

### Optional later

- Staff `/perf/status/` page embedding latest charts
- Waterfall sections fed fully from `YSE_VIEW_TIMING`
- Main dashboard re-benchmark for deferred shell only (separate from full-page benchmark)
- Fragment HTML cache in Redis (user + section + data version key)

---

## PR stack progress (`perf/progressive-loading`)

| Step | Status |
|------|--------|
| 0. Spectrumplot merge + baseline | done |
| 1. Harness + CI | done |
| 2. Instrumentation | done (basic) |
| 3. Personal dashboard PFP | done |
| 4. Main dashboard PFP | done |
| 5. Transient detail PFP + HST/Chandra | done |
| 6. Follow-up tab phased (classical first) | done |
| 7. Plot optimizations | done |
| 8. Infra checklist + ziggy validation | **next** |

After each future step: `record_perf_benchmark` → review `static/YSE_App/perf/trend_*.png`.

---

## Success criteria

| User-visible | Target | Docker fixtures (deferred shell) |
|--------------|--------|----------------------------------|
| Personal dashboard chrome | &lt; 1.5 s | ~136 ms |
| Main dashboard chrome | &lt; 1.5 s | Re-benchmark deferred shell TBD |
| Transient detail core | &lt; 1.5 s | ~176 ms document TTFB |
| Phot + spectrum plots | Non-blocking; concurrent | Async XHR; plot cache on repeat |
| HST/Chandra labels | Probe only until tab open | Shipped |
| Follow-up tab | Background; classical before ToO | Shipped |
| Rare tabs | Zero cost until clicked | Shipped (comments/GW/spectra fragments) |

Trend PNGs should improve across iterations; CI must not regress past `perf_baselines.json`.

---

## Out of scope

- Full HTMX/React rewrite (jQuery parallel `$.get` is sufficient for v1)
- django-auto-prefetch until Django 4.2+
- Bokeh 3 migration
- Reverting Tier A caching policies without review

---

## Related files (quick index)

| Area | Primary files |
|------|----------------|
| Views / PFP | `YSE_App/views.py`, `YSE_App/urls.py` |
| Plots | `YSE_App/view_utils.py` (`lightcurveplot_detail`, `spectrumplot`) |
| Templates | `YSE_App/templates/YSE_App/personaldashboard.html`, `dashboard.html`, `transient_detail.html`, `transient_detail_*` partials |
| Perf harness | `YSE_App/perf/`, `YSE_App/tests/test_performance.py`, `perf_baselines.json` |
| CI | `.github/workflows/ci.yml` |
| Docker | `docker/scripts/run-baseline-benchmark.sh`, `docker/scripts/prune-yse-docker.sh` |

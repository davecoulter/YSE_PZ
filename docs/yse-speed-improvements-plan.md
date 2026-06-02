# YSE speed improvements (progressive loading)

**Branch:** `perf/progressive-loading` (pushed to `yse`; from `develop` @ `d60d5ef0` + merged `fix/spectrumplot-regression` / PR #14 equivalent).

**Commits:** `40dd5528` (harness + PFP), `3e65b01c` (CI), `ae363b18` (benchmark DB fix), `a3e94e08` (transient PFP + phased follow-up).

---

## Completed

| Phase | Deliverable |
|-------|-------------|
| 0a | Branch + spectrumplot merge |
| 0b | Baseline `baseline-pre-pfp` in `metrics_history.json` |
| 1 | `YSE_App/perf/`, `record_perf_benchmark`, plots, `perf_baselines.json`, `test_page_load_regression` |
| 1 | CI: regression step + artifact upload; workflow runs on `perf/progressive-loading` |
| 1 | `docker/scripts/run-baseline-benchmark.sh` |
| 2 | `YSE_VIEW_TIMING` via `YSE_App/perf/view_timing.py` (personal dashboard shell) |
| 3 | Personal dashboard PFP: shell + `/personaldashboard/section/<id>/` |
| 4 | Transient detail PFP: slim shell + tab fragments; HST/Chandra status probes + images on tab click |
| 4b | Follow-up tab phased load: requests → classical → ToO/automated (classical prioritized) |
| 6 | Main dashboard PFP: “New” sync + `/dashboard/section/<status>/` |
| 7 | LC/spectrum plot cache, DQ prefetch labels, display downsample |

### Measured iterations (Docker, fixture DB)

| Iteration | main_dashboard | personal_dashboard | transient_detail |
|-----------|----------------|-------------------|------------------|
| `baseline-pre-pfp` (sync) | 150 ms, 19 q | 172 ms, 23 q | 416 ms, 66 q |
| `personal-pfp` (deferred shells) | 356 ms, 19 q | **136 ms**, 8 q | 363 ms, 229 q |
| `transient-detail-pfp` | — | — | **176 ms**, 40 q (shell); plots/cutouts async |
| `plot-optimizations` | — | — | document ~282 ms; LC/spectrum cache + downsample |

Personal shell: **~21% of** sync cold path. Transient document TTFB **~60% lower** than `baseline-pre-pfp` (416 ms → 176 ms).

**Regression tests** track deferred shells (`perf_baselines.json`): personal ≤200 ms, main ≤250 ms, transient ≤250 ms.

---

## Remaining

| Phase | Work |
|-------|------|
| 8 | Infra: Redis, Gunicorn, Apache checklist on `yse_test` |
| 9 | Production validation on ziggy (real TTFB before/after deploy) |

Optional later: `/perf/status/` staff page; waterfall sections from `YSE_VIEW_TIMING`; django-auto-prefetch after Django 4.2+.

---

## How to run

### Local Docker (Apple Silicon notes)

```bash
export DOCKER_HOST=unix://$HOME/.docker/run/docker.sock
# If pull fails on credentials: export DOCKER_CONFIG=/tmp/docker-nocreds  # empty config.json
cd docker
bash scripts/run-baseline-benchmark.sh [label]
```

Protocol: `compose up` → tests/benchmark → `compose down -v` → `prune-yse-docker.sh aggressive` (no images between series).

### Benchmark only

```bash
docker exec ysepz_web_container python3 manage.py record_perf_benchmark --label my-iteration
```

### Static assets (production-servable)

- `/static/YSE_App/perf/metrics_history.json`
- `/static/YSE_App/perf/trend_*.png`, `waterfall_*.png`

**Waterfall plots** mimic the browser Network panel: one row per resource, positioned on a **shared time axis** (`start_ms` → `end_ms`), not all starting at zero. Scheduling models real load order: document first; deferred dashboard sections in **parallel** after the shell; transient detail has document + bokeh overlapping from 0, then plot/cutout XHRs in **parallel** after `max(document, bokeh)`. **Page load total** = latest `end_ms` (critical path). Stacked phases per row: Queued, DNS, Connect, SSL, Waiting, Download. `metrics_history.json` stores `page_load_total_ms`, `schedule_note`, and per-resource `[start, end]` intervals.

### Feature flags (default on)

| Env | Effect |
|-----|--------|
| `YSE_PERSONAL_DASHBOARD_DEFER=1` | Personal shell + AJAX sections |
| `YSE_MAIN_DASHBOARD_DEFER=1` | Main dashboard: only “New” sync |
| `YSE_TRANSIENT_DETAIL_DEFER=1` | Transient shell; follow-up/resources/photometry fragments; HST/Chandra on tab click |
| `YSE_PERSONAL_DASHBOARD_DEFER=0` | Legacy sync path (performance tests) |
| `YSE_MAIN_DASHBOARD_DEFER=0` | Legacy full dashboard (performance tests) |
| `YSE_TRANSIENT_DETAIL_DEFER=0` | Legacy full transient detail (performance tests) |
| `YSE_VIEW_TIMING=1` | Log per-section ms |
| `YSE_PLOT_HTML_CACHE=1` | Cache rendered LC/spectrum plot HTML (default on; 900s TTL) |
| `YSE_LC_PLOT_MAX_POINTS=3000` | Downsample photometry points for LC display |
| `YSE_SPEC_PLOT_MAX_PIXELS=800` | Cap interpolated spectrum pixels per spectrum |

---

## Success criteria (targets)

| Page | Target | Current (deferred shell, Docker fixtures) |
|------|--------|-------------------------------------------|
| Personal dashboard chrome | &lt; 1.5 s | ~136 ms |
| Main dashboard chrome | &lt; 1.5 s | TBD (deferred; re-benchmark needed) |
| Transient detail core | &lt; 1.5 s | ~176 ms document TTFB (deferred shell) |

Full design (transient tab matrix, architecture): see Cursor plan `yse_speed_improvements_07b82bf7.plan.md`.

# YSE speed improvements (progressive loading)

Canonical tracker for branch `perf/progressive-loading` → PR to `develop`.

| Resource | Location |
|----------|----------|
| Full design (tab matrix, mermaid, infra detail) | Cursor plan `yse_speed_improvements_07b82bf7.plan.md` |
| CI gate + phase checklist | Cursor plan `yse_progressive_loading_perf_7f163f3a.plan.md` |
| Metrics & charts (committed) | `YSE_App/static/YSE_App/perf/` |

---

## Summary

Progressive First Paint (PFP): return a fast HTML shell, load heavy tables and rare tabs via AJAX fragments. Includes spectrumplot regression fix (PR [#14](https://github.com/Young-Supernova-Experiment/YSE_PZ/pull/14) equivalent, merged on this branch).

**Branch:** `perf/progressive-loading` from `yse/develop` @ `d60d5ef0`.

**Commits (newest first):** `76643449` (4e rare tabs + URL fix), `fe08924c` (docs), `803a5a17` (plot cache), `a3e94e08` (transient PFP), `ae363b18` (benchmark DB), `3e65b01c` (CI), `40dd5528` (harness + dashboards PFP).

```bash
git fetch yse develop perf/progressive-loading
git checkout perf/progressive-loading
```

---

## Phase status

| Phase | Status |
|-------|--------|
| 0 — Branch, spectrumplot, baseline `baseline-pre-pfp` | done |
| 1 — Harness, CI regression, static `perf/` | done |
| 2 — Personal dashboard PFP | done |
| 3 — Main dashboard PFP | done |
| 4 — Transient PFP (shell, plots, HST/Chandra, follow-up phased, 4e rare tabs) | done |
| 5 — LC/spectrum cache, DQ prefetch, downsample | done |
| 6 — Infra checklist (Apache/Gunicorn/Redis) | **post-merge deploy** |
| 7 — Production TTFB on ziggy / `yse_test` | **post-merge deploy** |

ORM: explicit prefetch on hot paths; django-auto-prefetch deferred until Django 4.2+.

---

## Results (Docker fixtures)

Production motivation (`yse_test`, pre-PFP): personal ~10.9 s, main ~11.1 s, transient ~6.2 s document TTFB.

### Document TTFB (shell) — primary PR metric

| Iteration | main_dashboard | personal_dashboard | transient_detail |
|-----------|----------------|-------------------|------------------|
| `baseline-pre-pfp` (sync) | 150 ms, 19 q | 172 ms, 23 q | 416 ms, 66 q |
| `pre-pr-develop` (**deferred, current**) | **178 ms**, 7 q | **91 ms**, 8 q | **102 ms**, 27 q |

Deferred transient shell is **~75% faster** than sync baseline (416 → 102 ms). Personal shell **~47% faster** (172 → 91 ms).

### Full page load (waterfall critical path)

Includes parallel XHR after shell (sections, plots, cutouts). Dominated by external cutouts (e.g. PS1) on transient detail — not a shell regression.

| Iteration | main | personal | transient |
|-----------|------|----------|-----------|
| `pre-pr-develop` | ~234 ms | ~146 ms | ~903 ms |

Charts: `/static/YSE_App/perf/trend_*.png`, `waterfall_*.png`. History: `metrics_history.json` (iteration `pre-pr-develop` = index 8).

**CI ceilings** (`perf_baselines.json`, 20% tolerance): main ≤250 ms, personal ≤200 ms, transient ≤250 ms document TTFB.

---

## Progressive loading (shipped)

### Flags (default on in production after merge)

| Env | Default | Effect |
|-----|---------|--------|
| `YSE_PERSONAL_DASHBOARD_DEFER` | `1` | Shell + `/personaldashboard/section/<id>/` |
| `YSE_MAIN_DASHBOARD_DEFER` | `1` | “New” sync + `/dashboard/section/<status>/` |
| `YSE_TRANSIENT_DETAIL_DEFER` | `1` | Slim shell + tab fragments |
| `YSE_*_DEFER=0` | — | Legacy sync (perf tests) |
| `YSE_PLOT_HTML_CACHE` | `1` | LC/spectrum HTML cache (900 s) |
| `YSE_VIEW_TIMING` | off | Per-section logs |

Rollback: set defer flags to `0` if needed.

### Transient detail fragments

All routes are registered **before** `transient_detail/<slug>/` so numeric IDs work.

| Endpoint | Loads |
|----------|--------|
| `followup_fragment/` | Past requests |
| `followup_classical_fragment/` | Classical form (before ToO) |
| `followup_rest_fragment/` | Follow-up + ToO + automated forms |
| `resources_fragment/` | Resource tables |
| `photometry_fragment/` | Photometry + diff images |
| `comments_fragment/` | Comment history |
| `gw_fragment/` | GW table (tab if `GW Candidate` tag) |
| `spectra_tab_fragment/` | Spectra list |
| `summary_spectra_tools_fragment/` | Summary dropdown (background) |

HST/Chandra: `get_hst_status` / `get_chandra_status` on load; full images on tab click.

---

## Benchmark harness

| Path | Role |
|------|------|
| `YSE_App/perf/benchmark.py` | Three primary pages (deferred defaults) |
| `YSE_App/perf/waterfall_collect.py` | Browser-style timelines |
| `YSE_App/perf/plots.py` | Trend + waterfall PNGs |
| `YSE_App/management/commands/record_perf_benchmark.py` | `--label <name>` |
| `YSE_App/tests/test_page_load_regression.py` | CI vs `perf_baselines.json` |
| `docker/scripts/run-baseline-benchmark.sh` | Full protocol script |

### Run locally

```bash
export DOCKER_HOST=unix://$HOME/.docker/run/docker.sock
# export DOCKER_CONFIG=/tmp/docker-nocreds  # if credential helper fails

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

Do not reuse Docker images between series (see `prune-yse-docker.sh`).

---

## Post-merge (not blocking PR)

### Infra checklist (`yse_test` / ziggy)

| Layer | Action |
|-------|--------|
| Apache | gzip HTML; serve `/static/` directly; tune proxy timeout |
| Gunicorn | ≥2 workers; timeout > slowest plot fragment |
| Redis | `REDIS_URL` for cache + plot HTML across workers |
| MySQL | `max_execution_time` on explorer SQL |

### Production validation

After deploy, record TTFB for the three primary URLs and append `metrics_history.json` iteration `ziggy-post-pfp`.

### Optional profiling (Django 4.0)

| Tool | Notes |
|------|--------|
| [django-debug-toolbar](https://github.com/django-commons/django-debug-toolbar) 4.2.x | `DEBUG=1` only; v6.x needs Django ≥5.2 |
| [django-silk](https://github.com/jazzband/django-silk) | Staging/local; SQL + request history |
| In-repo harness | Preferred for CI — repeatable |

---

## PR checklist

- [x] CI green on `perf/progressive-loading`
- [x] `pre-pr-develop` benchmark iteration committed
- [x] `perf_baselines.json` aligned with deferred shells
- [ ] Manual smoke: three pages + fragment tabs (Follow-up, Comments, GW if tagged)
- [ ] Open PR to `develop` with flag/rollback notes
- [ ] After merge: infra + ziggy validation (phases 6–7)

---

## Out of scope

HTMX/React rewrite; django-auto-prefetch on Django 4.0; Bokeh 3 migration.

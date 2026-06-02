# YSE speed improvements (progressive loading)

Branch: `perf/progressive-loading` (from `develop` + spectrumplot fix).

## Baseline

Iteration `baseline-pre-pfp` in `YSE_App/static/YSE_App/perf/metrics_history.json` was captured before progressive-loading changes via `YSE_App.tests.test_performance` in Docker.

Re-run locally:

```bash
cd docker
bash scripts/run-baseline-benchmark.sh
```

## Benchmarks and plots

- `python manage.py record_perf_benchmark`
- Static URLs: `/static/YSE_App/perf/metrics_history.json`, `trend_*.png`, `waterfall_*.png`
- CI: `test_page_load_regression` vs `YSE_App/tests/perf_baselines.json`

## Progressive loading status

| Area | Status |
|------|--------|
| Personal dashboard | Shell + parallel `personaldashboard/section/<id>/` fragments (`YSE_PERSONAL_DASHBOARD_DEFER=1`, default) |
| Main dashboard | “New” sync; other sections via `dashboard/section/<status>/` (`YSE_MAIN_DASHBOARD_DEFER=1`) |
| Transient detail | Planned: slim shell, plot AJAX, HST/Chandra on tab click |
| View timing | `YSE_VIEW_TIMING=1` logs section ms via `YSE_App.perf.view_timing` |

Disable deferred personal dashboard for sync tests: `YSE_PERSONAL_DASHBOARD_DEFER=0`.

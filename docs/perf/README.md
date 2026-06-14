# Page load diagnostics (HAR snapshots)

Capture a HAR in Safari/Chrome while loading a hot page, then convert it to JSON for
regression tracking and charts.

## Add a snapshot

You do **not** need to copy the `.har` into the repo. Keep it anywhere (e.g. `~/Downloads/`) and pass the path to the converter. Only the generated **JSON** is committed under `docs/perf/har_snapshots/`.

```bash
python3 -m YSE_App.tests.har_perf ~/Downloads/127.0.0.1.2.har \
  -o docs/perf/har_snapshots/transient_detail_2026fba_2026-06-04_after_perf.json \
  --label transient_detail_2026fba_after_perf
```

Checked-in snapshots for `transient_detail/2026fba/`:

| File | Label |
|------|--------|
| `transient_detail_2026fba_2026-06-04.json` | Before Aladin defer / early XHR (baseline) |
| `transient_detail_2026fba_2026-06-04_after_perf.json` | After perf changes |

Baseline vs after (first YSE XHR / spectrumplot): ~3416 ms → ~1991 ms.

Each JSON file includes:

- `page_timings_ms` — document load milestones
- `milestones_ms` — first YSE XHR, spectrum/lightcurve, Aladin JS
- `by_category` — totals for `yse_api`, `static`, `aladin`, `external_sky`, etc.
- `slowest` — top 15 requests by duration
- `entries` — full timeline (start_ms, duration_ms, path, category)

## Plot a snapshot (optional)

```bash
python3 docs/perf/plot_har_snapshot.py \
  docs/perf/har_snapshots/transient_detail_2026fba_2026-06-04.json
```

Writes a PNG next to the JSON (requires `matplotlib`).

## Server-side baselines

Django wall-time + SQL ceilings: `YSE_App.tests.test_performance` and
`YSE_PERF_RECORD_PATH` (see [CONTRIBUTING.md](../../CONTRIBUTING.md)).

## transient_detail optimizations (2026-06)

- Aladin Lite vendored under `YSE_App/static/YSE_App/vendor/aladin-lite/` and loaded
  only when the carousel shows the DSS slide (not on initial paint).
- Spectrum/lightcurve/cutout `$.get` calls run immediately after Bokeh loads, not
  after tag/DataTable/Aladin setup.
- Bokeh fragments use `components()` so plots do not pull `cdn.bokeh.org` again.

After template/static changes: `./docker/scripts/yse-docker.sh collectstatic`

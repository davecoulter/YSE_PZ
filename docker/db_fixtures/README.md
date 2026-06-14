# YSE test fixture database (2026f* TNS sample)

One-time (or rare) build of a **small real-data** MySQL snapshot for UI tests, performance baselines, and manual QA.

## Prerequisites

- Docker stack running (`./docker/scripts/yse-docker.sh up`)
- TNS needs **two** things (see [TNS API docs](https://www.wis-tns.org/api)):
  - **Marker** (User-Agent identity): `tns_bot_id`, `tns_bot_name`, and `tns_marker_type` in `YSE_PZ/settings.ini` — for a personal account, use your TNS user id/name with `tns_marker_type=user` (e.g. `151` / `rfoley`). Bot keys from [wis-tns.org/bots](https://www.wis-tns.org/bots) may still require the **user** marker, not the bot display name.
  - **Secret API key**: `tnsapikey` in settings.ini or `TNS_API_KEY=...` in `docker/.env.secrets` (from the bot row on [wis-tns.org/bots](https://www.wis-tns.org/bots), not the `tns_marker` string)
- Django user for `/add_transient/`: set `dblogin`/`dbpassword` in `settings.ini`, or pass `YSE_DB_LOGIN` / `YSE_DB_PASSWORD` (e.g. `ci_admin` / `ci_password` from `docker/.env`)
- Pan-STARRS scores: automatic via MAST in `get_ps_score` (no extra flag)
- Optional: `--with-prost` requires `astro_prost` (local dev image only; see rebuild below)

## Local dev image (astro-prost)

Published `ghcr.io/davecoulter/yse_pz:latest` does not include `astro-prost`. Rebuild once:

```bash
YSE_DOCKER_BUILD_LOCAL=1 ./docker/scripts/yse-docker.sh rebuild
```

## Build ingest (into running Docker DB)

By default, `build_tns_fixture` uses **dashboard-only** mode: TNS discovery metadata, TNS photometry (for “Last Mag” / “Last Obs.”), Milky Way E(B-V), and **TNS spectra when present**. It does **not** query Chandra, HST, Spitzer, or Antares ZTF unless you opt in.

```bash
docker exec \
  -e YSE_DB_LOGIN=ci_admin -e YSE_DB_PASSWORD=ci_password \
  ysepz_web_container python3 manage.py build_tns_fixture --prefix 2026f --max 50
```

Optional flags:

- `--with-prost` — host association (slow; not required for dashboard columns)
- `--with-ps` — Pan-STARRS score per object (MAST Casjobs)
- `--skip-spectra` — skip TNS spectrum download (not recommended)
- `--full-ingest` — legacy cron-style ingest (archival + Antares + spectra)

Re-ingest spectra for one object (e.g. 2026fba) without a full rebuild:

```bash
docker exec \
  -e YSE_DB_LOGIN=ci_admin -e YSE_DB_PASSWORD=ci_password \
  ysepz_web_container python3 manage.py build_tns_fixture --prefix 2026fba --max 1
```

Then refresh `http://127.0.0.1:8080/transient_detail/2026fba/` (spectrum plot loads via `/spectrumplot/<id>/`).
- `--max N` — cap count (TNS may return hundreds for `2026f`)

Dry-run (list TNS names only):

```bash
docker exec ysepz_web_container python3 manage.py build_tns_fixture --prefix 2026f --dry-run
```

This writes [`manifest.json`](manifest.json) with transient names/slugs.

If you see a huge HTML dump in the terminal, `/add_transient/` returned a Django **DEBUG** error page (usually SMTP placeholders in `settings.ini` or a batch upload failure). Dashboard-only mode now uploads **one transient per POST** and prints a short error summary instead of the full HTML.

## Export static snapshot (create once)

From repo root:

```bash
./docker/scripts/build-test-fixture-db.sh export
```

Produces `docker/db_fixtures/yse_2026f_fixture.sql.gz` (gitignored if large; commit via Git LFS if the team wants it in-repo).

## Restore snapshot on a fresh volume

```bash
./docker/scripts/yse-docker.sh down
cd docker && docker compose down -v && cd ..
./docker/scripts/yse-docker.sh up
./docker/scripts/build-test-fixture-db.sh import
```

## Static files (fixes `yse-theme.css` 404 on :8080)

Nginx serves `/static/` from `STATIC_VOL` (see `docker/public.env`). After pulling
theme or app static changes:

```bash
./docker/scripts/yse-docker.sh collectstatic
```

## Run fixture-backed tests

```bash
docker exec ysepz_web_container python3 manage.py test \
  YSE_App.tests.test_transient_detail_assets -v2
```

Against the running stack (after `collectstatic`), from the host:

```bash
YSE_LIVE_SMOKE=1 YSE_LIVE_URL=http://127.0.0.1:8080 \
  python3 manage.py test YSE_App.tests.test_live_static_smoke -v2
```

Requires `docker/db_fixtures/manifest.json` (and ingested data, or import SQL).

## Clean perf junk without full wipe

```python
from YSE_App.models import Transient
Transient.objects.filter(name__startswith="perf-").delete()
Transient.objects.filter(name__startswith="lc-test-").delete()
```

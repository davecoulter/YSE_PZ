# YSE test fixture database (2026f* TNS sample)

One-time (or rare) build of a **small real-data** MySQL snapshot for UI tests, performance baselines, and manual QA.

## Prerequisites

- Docker stack running (`./docker/scripts/yse-docker.sh up`)
- `YSE_PZ/settings.ini` with valid `[main]` TNS API fields (`tnsapi`, `tnsapikey`, `tns_bot_id`, `tns_bot_name`) or `TNS_API_KEY` env
- `dblogin` / `dbpassword` in settings.ini must match a Django user that can call `/add_transient/` (or create `ci_admin` first)
- Pan-STARRS scores: automatic via MAST in `get_ps_score` (no extra flag)
- Optional: `--with-prost` requires `astro_prost` in the container (not in default Docker image)

## Build ingest (into running Docker DB)

```bash
docker exec ysepz_web_container python3 manage.py build_tns_fixture --prefix 2026f
```

Pan-STARRS scores are fetched automatically in `getTNSData` when MAST is reachable. Host association via `astro_prost` is optional:

```bash
docker exec ysepz_web_container python3 manage.py build_tns_fixture --prefix 2026f --with-prost
```

Dry-run (list TNS names only):

```bash
docker exec ysepz_web_container python3 manage.py build_tns_fixture --prefix 2026f --dry-run
```

This writes [`manifest.json`](manifest.json) with transient names/slugs.

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

## Run fixture-backed tests

```bash
docker exec ysepz_web_container python3 manage.py test YSE_App.tests.test_fixture_page_loads -v2
```

Requires `docker/db_fixtures/manifest.json` (and ingested data, or import SQL).

## Clean perf junk without full wipe

```python
from YSE_App.models import Transient
Transient.objects.filter(name__startswith="perf-").delete()
Transient.objects.filter(name__startswith="lc-test-").delete()
```

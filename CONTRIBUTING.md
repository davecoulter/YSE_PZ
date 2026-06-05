# Contributing to astrofoley/YSE_PZ

This fork’s day-to-day development targets **`main`** on [astrofoley/YSE_PZ](https://github.com/astrofoley/YSE_PZ). Upstream is [davecoulter/YSE_PZ](https://github.com/davecoulter/YSE_PZ) (`develop`); cross-fork PRs come later when that workflow is verified.

**Upstream policy:** Do **not** open pull requests to [davecoulter/YSE_PZ](https://github.com/davecoulter/YSE_PZ) (legacy upstream). Integration work from [astrofoley/YSE_PZ](https://github.com/astrofoley/YSE_PZ) lands here via branches such as `integrate/yse-*` (see open integration PRs).

## Workflow

1. Branch from current `main`:
   ```bash
   git fetch astrofoley
   git checkout main-unified   # or: git checkout main && git pull astrofoley main
   git checkout -b fix/issue-N-short-description
   ```
2. Make changes; reference the [issue](https://github.com/astrofoley/YSE_PZ/issues) in commits/PR body (`Fixes #N`).
3. Open a PR into **`main`** on astrofoley/YSE_PZ (not direct pushes unless trivial).
4. Wait for CI; merge when green.

**Remotes:** `astrofoley` → this fork; `origin` → davecoulter/YSE_PZ.

## Local Docker

Web container image: **`ghcr.io/young-supernova-experiment/yse_pz:latest`** from [Young-Supernova-Experiment/YSE_PZ](https://github.com/Young-Supernova-Experiment/YSE_PZ) (not the legacy `davecoulter` GHCR image). `yse-docker.sh up` pulls this image; your clone is mounted at `/app`.

### First-time setup

```bash
cp YSE_PZ/public_settings.ini YSE_PZ/settings.ini
cp docker/public.env docker/.env
```

Edit `docker/.env` so paths are **absolute** (required for Docker Desktop on macOS):

- `VOL` — repo root
- `VOL_DB` — e.g. `…/YSE_PZ/database`
- `STATIC_VOL` — e.g. `…/YSE_PZ/YSE_PZ/static`
- `VOL_GHOST` — e.g. `…/YSE_PZ/ghost_logs`

Then from the repo root:

```bash
./docker/scripts/yse-docker.sh up
```

Open **http://127.0.0.1:8080/login/** (port from `LOCAL_HTTP_PORT` in `.env`).

More detail: [docker/readme.txt](docker/readme.txt).

### Static files (`collectstatic`)

Nginx serves files from `STATIC_VOL` (host `YSE_PZ/static/`). Most assets are committed; if the admin UI or CSS looks broken after a fresh clone, gather static files into that directory:

```bash
./docker/scripts/yse-docker.sh collectstatic
```

This runs `manage.py collectstatic --noinput` inside `ysepz_web_container` and writes into `YSE_PZ/static/` on the host (via the app volume).

### Disk space and pruning

Docker pull/build cycles can use 10–20 GB per iteration on macOS. **`yse-docker.sh` prunes automatically** after successful `up`, `pull`, and `rebuild` unless disabled.

| Command | What it does |
|---------|----------------|
| `./docker/scripts/yse-docker.sh up` | Start stack; light prune after success |
| `./docker/scripts/yse-docker.sh pull` | Pull `ghcr.io/davecoulter/yse_pz:latest`; aggressive prune |
| `./docker/scripts/yse-docker.sh rebuild` | Build local dev image + start; aggressive prune |
| `./docker/scripts/yse-docker.sh prune` | Prune only (`prune aggressive` for more) |
| `./docker/scripts/yse-docker.sh down` | Stop stack (**keeps** MySQL data in `VOL_DB`) |
| `./docker/scripts/yse-docker.sh collectstatic` | Populate `YSE_PZ/static/` for nginx |

**Skip pruning for one command:**

```bash
YSE_DOCKER_PRUNE=0 ./docker/scripts/yse-docker.sh up
```

**What pruning removes:** dangling layers, build cache, and old `ghcr.io/davecoulter/yse_pz` / `local/yse_pz_web` images not used by `ysepz_*` containers.

**What pruning does not remove:** MySQL data under `VOL_DB`.

**Intentional database wipe:**

```bash
cd docker && docker compose down -v
```

**If Docker Desktop still shows a huge disk image:** Docker Desktop → Troubleshoot → Clean / Purge data, or:

```bash
docker system df
./docker/scripts/yse-docker.sh prune aggressive
```

Keep several GB free on the host; git and Docker both fail when the disk is full.

## Tests

```bash
docker exec ysepz_web_container python3 manage.py test YSE_App.tests --verbosity=2
```

### Performance baselines

Page-load regression tests track **SQL query count** and **wall-clock load time (ms)** for each page. A summary table prints at the end of the run.

```bash
docker exec ysepz_web_container python3 manage.py test YSE_App.tests.test_performance --verbosity=2
```

| Variable | Effect |
|----------|--------|
| `YSE_PERF_SKIP_TIMING=1` | Skip load-time ceiling assertions (queries still checked) |
| `YSE_PERF_RECORD_PATH=/tmp/yse_perf.json` | Export metrics JSON for CI or local comparison |

Targets: `/transient_detail/<slug>/` (shell + synthetic loaded), `/personaldashboard/`, `/dashboard/`, `/explorer/` (including 200-row catalog + logs; query count only).

CI runs the same flow via [.github/workflows/ci.yml](.github/workflows/ci.yml).

## Secrets (optional)

For production or shared machines, prefer environment variables over committing secrets in `settings.ini`:

| Variable | Purpose |
|----------|---------|
| `DJANGO_SECRET_KEY` | Django `SECRET_KEY` |
| `TNS_API_KEY` | TNS bot API key |
| `TNS_DECAM_API_KEY` | DECam TNS bot key |
| `SLACK_BOT_TOKEN` | TNS Slack notifications (`TNS_Bot.py`) |

## Database

Local Docker uses init SQL under `docker/db_init/` only. Do not import the full production database on a laptop unless you intend to.

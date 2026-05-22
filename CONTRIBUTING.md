# Contributing to Young-Supernova-Experiment/YSE_PZ

Development targets **`develop`** on [Young-Supernova-Experiment/YSE_PZ](https://github.com/Young-Supernova-Experiment/YSE_PZ).

## Workflow

1. Branch from current `develop`:
   ```bash
   git fetch yse
   git checkout develop
   git pull yse develop
   git checkout -b fix/short-description
   ```
2. Make changes; reference GitHub issues in commits/PR body (`Fixes #N`) when applicable.
3. Open a PR into **`develop`** on Young-Supernova-Experiment/YSE_PZ.
4. Wait for CI; merge when green.

**Suggested remote:** `yse` → https://github.com/Young-Supernova-Experiment/YSE_PZ.git

## Local Docker

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

### Run stack

```bash
./docker/scripts/yse-docker.sh up
```

Open **http://127.0.0.1:8080/login/** (nginx on port 8080).

### Tests (inside container)

```bash
docker exec ysepz_web_container python3 manage.py check
docker exec ysepz_web_container python3 manage.py test YSE_App.tests --verbosity=2
```

If test DB creation fails with access denied, grant the dev user from MySQL root:

```bash
docker exec ysepz_db_container mysql -uroot -p"$DB_PWD" -e \
  "GRANT CREATE, DROP ON *.* TO 'dev'@'%'; FLUSH PRIVILEGES;"
```

### Prune

| Command | Effect |
|---------|--------|
| `./docker/scripts/yse-docker.sh up` | Start stack; light prune after success |
| `./docker/scripts/yse-docker.sh pull` | Pull `ghcr.io/davecoulter/yse_pz:latest`; aggressive prune |
| `./docker/scripts/yse-docker.sh rebuild` | Local dev image build + up; aggressive prune |
| `./docker/scripts/yse-docker.sh prune` | Prune only (`aggressive` optional) |
| `YSE_DOCKER_PRUNE=0 ./docker/scripts/yse-docker.sh up` | Skip auto-prune |

**What pruning removes:** dangling layers, build cache, and old `ghcr.io/davecoulter/yse_pz` / `local/yse_pz_web` images not used by `ysepz_*` containers.

### collectstatic

If static assets are missing locally:

```bash
./docker/scripts/yse-docker.sh collectstatic
```

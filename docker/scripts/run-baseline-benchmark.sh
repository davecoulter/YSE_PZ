#!/usr/bin/env bash
# Baseline / iteration benchmark: compose up → test → benchmark → down → aggressive prune.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
DOCKER_DIR="$ROOT/docker"
export DOCKER_HOST="${DOCKER_HOST:-unix://${HOME}/.docker/run/docker.sock}"

cd "$DOCKER_DIR"
if [[ ! -f .env ]]; then
  printf '%s\n' \
    "VOL=$ROOT" \
    "VOL_DB=$ROOT/database" \
    "VOL_GHOST=$ROOT/ghost_logs" \
    "STATIC_VOL=$ROOT/YSE_PZ/static" \
    "DB_PWD=password" \
    "LOCAL_DB_PORT=53306" \
    "LOCAL_HTTP_PORT=8080" \
    "DJANGO_SUPERUSER_USERNAME=ci_admin" \
    "DJANGO_SUPERUSER_PASSWORD=ci_password" \
    "DJANGO_SUPERUSER_EMAIL=ci@example.com" \
    > .env
fi

LABEL="${1:-$(git -C "$ROOT" rev-parse --short HEAD 2>/dev/null || echo manual)}"

YSE_DOCKER_PRUNE=0 docker compose up -d
for i in $(seq 1 60); do
  if docker exec ysepz_web_container python3 manage.py check >/dev/null 2>&1; then
    break
  fi
  sleep 5
done

docker exec ysepz_web_container python3 manage.py test \
  YSE_App.tests.test_performance \
  YSE_App.tests.test_page_load_regression \
  --noinput -v2

docker exec ysepz_web_container python3 manage.py record_perf_benchmark --label "$LABEL"

docker compose down -v
bash "$DOCKER_DIR/scripts/prune-yse-docker.sh" aggressive

echo "Done. Metrics: $ROOT/YSE_App/static/YSE_App/perf/metrics_history.json"

#!/usr/bin/env bash
# Wrapper for local YSE Docker workflows with automatic post-success pruning.
#
# Usage (from repo root or docker/):
#   ./docker/scripts/yse-docker.sh up          # compose up -d, light prune
#   ./docker/scripts/yse-docker.sh pull        # pull web image, prune old layers
#   ./docker/scripts/yse-docker.sh rebuild     # local dev image build + up, aggressive prune
#   ./docker/scripts/yse-docker.sh prune       # prune only
#   ./docker/scripts/yse-docker.sh down        # compose down (keeps DB volume)
#   ./docker/scripts/yse-docker.sh collectstatic  # manage.py collectstatic in web container
#
# Set YSE_DOCKER_PRUNE=0 to skip pruning for a single invocation.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKER_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$DOCKER_DIR"

COMPOSE=(docker compose -f docker-compose.yml)
if [[ "${YSE_DOCKER_BUILD_LOCAL:-0}" == "1" ]]; then
  COMPOSE+=( -f docker-compose.dev.yml )
fi

run_prune() {
  local mode="${1:-light}"
  if [[ "${YSE_DOCKER_PRUNE:-1}" == "0" ]]; then
    echo "==> Skipping prune (YSE_DOCKER_PRUNE=0)"
    return 0
  fi
  bash "$SCRIPT_DIR/prune-yse-docker.sh" "$mode"
}

load_dotenv() {
  if [[ -f "$DOCKER_DIR/.env" ]]; then
    set -a
    # shellcheck disable=SC1091
    source "$DOCKER_DIR/.env"
    set +a
  fi
}

static_vol_path() {
  load_dotenv
  local static_vol="${STATIC_VOL:-../YSE_PZ/static/}"
  if [[ "$static_vol" != /* ]]; then
    static_vol="$(cd "$DOCKER_DIR" && cd "$static_vol" && pwd)"
  fi
  static_vol="${static_vol%/}"
  echo "$static_vol"
}

warn_if_static_incomplete() {
  local static_root
  static_root="$(static_vol_path)"
  if [[ ! -f "$static_root/admin/css/base.css" ]]; then
    echo "==> Static files look incomplete under $static_root"
    echo "    Run: ./docker/scripts/yse-docker.sh collectstatic"
  fi
}

run_collectstatic() {
  load_dotenv
  if ! docker ps --format '{{.Names}}' | grep -qx 'ysepz_web_container'; then
    echo "ysepz_web_container is not running. Start the stack first:" >&2
    echo "  ./docker/scripts/yse-docker.sh up" >&2
    exit 1
  fi
  docker exec ysepz_web_container python3 manage.py collectstatic --noinput "$@"
  warn_if_static_incomplete
}

usage() {
  cat <<'EOF'
YSE Docker helper (auto-prunes superseded images after success)

  yse-docker.sh up       Start stack (docker compose up -d)
  yse-docker.sh pull     Pull published web image (ghcr.io/davecoulter/yse_pz:latest) and prune old copies
  yse-docker.sh rebuild  Build local dev web image, start stack, aggressive prune
  yse-docker.sh prune    Prune only (--aggressive optional second arg)
  yse-docker.sh down     Stop stack (does not delete MySQL volume)
  yse-docker.sh collectstatic  Run manage.py collectstatic in the web container

Environment:
  YSE_DOCKER_PRUNE=0     Disable automatic prune for one command
  YSE_DOCKER_BUILD_LOCAL=1  Use docker-compose.dev.yml (set automatically by rebuild)

MySQL data lives in VOL_DB from .env and is never removed by these commands.
Use: docker compose down -v   only if you intentionally want a fresh database.
EOF
}

cmd="${1:-up}"
shift || true

case "$cmd" in
  up)
    "${COMPOSE[@]}" up -d "$@"
    run_prune light
    warn_if_static_incomplete
    ;;
  pull)
    docker pull ghcr.io/davecoulter/yse_pz:latest
    run_prune aggressive
    ;;
  rebuild)
    export YSE_DOCKER_BUILD_LOCAL=1
    COMPOSE=(docker compose -f docker-compose.yml -f docker-compose.dev.yml)
    "${COMPOSE[@]}" build "$@"
    "${COMPOSE[@]}" up -d
    run_prune aggressive
    ;;
  prune)
    aggressive="${1:-light}"
    run_prune "$aggressive"
    ;;
  down)
    "${COMPOSE[@]}" down "$@"
    ;;
  collectstatic)
    run_collectstatic "$@"
    ;;
  -h|--help|help)
    usage
    ;;
  *)
    echo "Unknown command: $cmd" >&2
    usage >&2
    exit 1
    ;;
esac

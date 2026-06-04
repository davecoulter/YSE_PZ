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

# Docker Desktop credential helper (macOS); avoids pull failures when /opt/local/bin/docker is first on PATH.
if [[ -d /Applications/Docker.app/Contents/Resources/bin ]]; then
  PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH"
  export PATH
fi

YSE_GHCR_IMAGE="${YSE_GHCR_IMAGE:-ghcr.io/young-supernova-experiment/yse_pz:latest}"

COMPOSE=(docker compose -f docker-compose.yml)
if [[ "${YSE_DOCKER_BUILD_LOCAL:-0}" == "1" ]]; then
  COMPOSE+=( -f docker-compose.dev.yml )
fi

# Fail fast when Docker Desktop / daemon is stuck (otherwise compose/prune hang with no output).
require_docker_daemon() {
  local timeout_sec="${YSE_DOCKER_DAEMON_TIMEOUT:-15}"
  echo "==> Checking Docker daemon (${timeout_sec}s timeout)..."
  if command -v timeout >/dev/null 2>&1; then
    if timeout "$timeout_sec" docker info >/dev/null 2>&1; then
      return 0
    fi
  else
    docker info >/dev/null 2>&1 &
    local pid=$!
    local waited=0
    while kill -0 "$pid" 2>/dev/null && [[ "$waited" -lt "$timeout_sec" ]]; do
      sleep 1
      waited=$((waited + 1))
    done
    if kill -0 "$pid" 2>/dev/null; then
      kill "$pid" 2>/dev/null || true
      wait "$pid" 2>/dev/null || true
    else
      wait "$pid" && return 0
    fi
  fi
  echo "ERROR: Docker daemon did not respond within ${timeout_sec}s." >&2
  echo "  - Start or restart Docker Desktop, then wait until it shows Running." >&2
  echo "  - Verify: docker info   (must return quickly, not hang)" >&2
  echo "  - This machine uses: $(command -v docker 2>/dev/null || echo 'docker not in PATH')" >&2
  echo "  - Context: $(docker context show 2>/dev/null || echo 'unknown')" >&2
  exit 1
}

run_prune() {
  local mode="${1:-light}"
  if [[ "${YSE_DOCKER_PRUNE:-1}" == "0" ]]; then
    echo "==> Skipping prune (YSE_DOCKER_PRUNE=0)"
    return 0
  fi
  bash "$SCRIPT_DIR/prune-yse-docker.sh" "$mode"
}

ensure_env_secrets() {
  if [[ ! -f "$DOCKER_DIR/.env.secrets" ]]; then
    if [[ -f "$DOCKER_DIR/.env.secrets.example" ]]; then
      cp "$DOCKER_DIR/.env.secrets.example" "$DOCKER_DIR/.env.secrets"
      echo "==> Created $DOCKER_DIR/.env.secrets — add TNS_API_KEY=... then restart the web container"
    else
      echo "# TNS_API_KEY=" >"$DOCKER_DIR/.env.secrets"
    fi
  fi
}

load_dotenv() {
  if [[ -f "$DOCKER_DIR/.env" ]]; then
    set -a
    # shellcheck disable=SC1091
    source "$DOCKER_DIR/.env"
    set +a
  fi
  if [[ -f "$DOCKER_DIR/.env.secrets" ]]; then
    set -a
    # shellcheck disable=SC1091
    source "$DOCKER_DIR/.env.secrets"
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
  elif [[ ! -f "$static_root/YSE_App/yse-theme.css" ]]; then
    echo "==> Phase 1 theme CSS missing under $static_root"
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
  cat <<EOF
YSE Docker helper (auto-prunes superseded images after success)

  yse-docker.sh up       Start stack (docker compose up -d)
  yse-docker.sh pull     Pull published web image ($YSE_GHCR_IMAGE) and prune old copies
  yse-docker.sh rebuild  Build local dev web image, start stack, aggressive prune
  yse-docker.sh prune    Prune only (--aggressive optional second arg)
  yse-docker.sh down     Stop stack (does not delete MySQL volume)
  yse-docker.sh collectstatic  Run manage.py collectstatic in the web container

Environment:
  YSE_DOCKER_PRUNE=0     Disable automatic prune for one command
  YSE_DOCKER_BUILD_LOCAL=1  Use docker-compose.dev.yml (set automatically by rebuild)
  YSE_DOCKER_DAEMON_TIMEOUT=15  Seconds to wait for docker info before failing

MySQL data lives in VOL_DB from .env and is never removed by these commands.
Use: docker compose down -v   only if you intentionally want a fresh database.
EOF
}

cmd="${1:-up}"
shift || true

case "$cmd" in
  up)
    require_docker_daemon
    ensure_env_secrets
    load_dotenv
    echo "==> Starting stack (docker compose up -d)..."
    "${COMPOSE[@]}" up -d "$@"
    run_prune light
    warn_if_static_incomplete
    echo "==> Stack up. Open http://127.0.0.1:${LOCAL_HTTP_PORT:-8080}/login/"
    ;;
  pull)
    require_docker_daemon
    echo "==> Pulling $YSE_GHCR_IMAGE ..."
    docker pull "$YSE_GHCR_IMAGE"
    run_prune aggressive
    ;;
  rebuild)
    require_docker_daemon
    ensure_env_secrets
    export YSE_DOCKER_BUILD_LOCAL=1
    COMPOSE=(docker compose -f docker-compose.yml -f docker-compose.dev.yml)
    if ! docker image inspect "$YSE_GHCR_IMAGE" >/dev/null 2>&1; then
      if docker image inspect local/yse_pz_web:dev >/dev/null 2>&1; then
        export YSE_BASE_IMAGE=local/yse_pz_web:dev
        echo "==> Org GHCR base image not local; building from ${YSE_BASE_IMAGE}"
      fi
    fi
    echo "==> Building local web image..."
    "${COMPOSE[@]}" build --pull=false "$@"
    echo "==> Starting stack..."
    "${COMPOSE[@]}" up -d
    run_prune aggressive
    ;;
  prune)
    require_docker_daemon
    aggressive="${1:-light}"
    run_prune "$aggressive"
    ;;
  down)
    require_docker_daemon
    echo "==> Stopping stack..."
    "${COMPOSE[@]}" down "$@"
    ;;
  collectstatic)
    require_docker_daemon
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

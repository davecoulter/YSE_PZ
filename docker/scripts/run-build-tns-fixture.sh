#!/usr/bin/env bash
# Build 2026f* TNS fixture DB in the running Docker stack.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKER_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

if [[ -f "$DOCKER_DIR/.env.secrets" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$DOCKER_DIR/.env.secrets"
  set +a
fi

if [[ -z "${TNS_API_KEY:-}" ]]; then
  echo "ERROR: Set TNS_API_KEY in docker/.env.secrets (see .env.secrets.example)" >&2
  exit 1
fi

PREFIX="${1:-2026f}"
MAX="${MAX:-50}"
EXTRA=(--max "$MAX")
if [[ "${FULL_INGEST:-0}" == "1" ]]; then
  EXTRA+=(--full-ingest)
  if [[ "${WITH_PROST:-0}" == "1" ]]; then
    EXTRA+=(--with-prost)
  fi
fi

docker exec \
  -e TNS_API_KEY \
  -e YSE_DB_LOGIN="${YSE_DB_LOGIN:-ci_admin}" \
  -e YSE_DB_PASSWORD="${YSE_DB_PASSWORD:-ci_password}" \
  ysepz_web_container \
  python3 manage.py build_tns_fixture --prefix "$PREFIX" "${EXTRA[@]}"

"$SCRIPT_DIR/build-test-fixture-db.sh" export

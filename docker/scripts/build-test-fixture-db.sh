#!/usr/bin/env bash
# Export/import the YSE 2026f* test fixture MySQL dump.
#
#   ./docker/scripts/build-test-fixture-db.sh export   # after build_tns_fixture ingest
#   ./docker/scripts/build-test-fixture-db.sh import   # into running yse_db (empty YSE schema)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKER_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
FIXTURE_DIR="$(cd "$DOCKER_DIR/db_fixtures" && pwd)"
DUMP_FILE="${FIXTURE_DIR}/yse_2026f_fixture.sql.gz"
DB_CONTAINER="${YSE_DB_CONTAINER:-ysepz_db_container}"

load_dotenv() {
  if [[ -f "$DOCKER_DIR/.env" ]]; then
    set -a
    # shellcheck disable=SC1091
    source "$DOCKER_DIR/.env"
    set +a
  fi
}

db_password() {
  load_dotenv
  echo "${DB_PWD:-password}"
}

cmd="${1:-}"
case "$cmd" in
  export)
    if ! docker ps --format '{{.Names}}' | grep -qx "$DB_CONTAINER"; then
      echo "ERROR: $DB_CONTAINER is not running. Start stack first." >&2
      exit 1
    fi
    pwd="$(db_password)"
    echo "==> Dumping YSE database to $DUMP_FILE"
    docker exec "$DB_CONTAINER" mysqldump -uroot -p"$pwd" \
      --single-transaction --routines --triggers YSE \
      | gzip -c >"$DUMP_FILE"
    echo "==> Done. Size: $(du -h "$DUMP_FILE" | cut -f1)"
    ;;
  import)
    if [[ ! -f "$DUMP_FILE" ]]; then
      echo "ERROR: Missing $DUMP_FILE — run export after build_tns_fixture first." >&2
      exit 1
    fi
    if ! docker ps --format '{{.Names}}' | grep -qx "$DB_CONTAINER"; then
      echo "ERROR: $DB_CONTAINER is not running." >&2
      exit 1
    fi
    pwd="$(db_password)"
    echo "==> Importing $DUMP_FILE into YSE"
    gunzip -c "$DUMP_FILE" | docker exec -i "$DB_CONTAINER" mysql -uroot -p"$pwd" YSE
    echo "==> Import complete."
    ;;
  *)
    echo "Usage: $0 export|import" >&2
    exit 1
    ;;
esac

#!/usr/bin/env bash
set -euo pipefail
REPO="astrofoley/YSE_PZ"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
MAP_FILE="$ROOT/docs/ui-workflow-roadmap.md"
ISSUE_LOG="$ROOT/docs/ui-workflow-issues.log"
: > "$ISSUE_LOG"
ensure_label() { gh label create "$1" --repo "$REPO" --color "$2" --description "$3" 2>/dev/null || true; }
create_issue() {
  local catalog_id="$1" title="$2" body="$3" labels="$4"
  local url num
  url=$(gh issue create --repo "$REPO" --title "$title" --body "$body" --label "$labels")
  num="${url##*/}"
  echo "$catalog_id|$num|$url" >> "$ISSUE_LOG"
  echo "Created $catalog_id -> #$num"
}
ensure_label "phase-0" "0E8A16" "UI roadmap phase 0"
ensure_label "phase-1" "1D76DB" "UI roadmap phase 1"
ensure_label "phase-2" "5319E7" "UI roadmap phase 2"
ensure_label "phase-3" "FBCA04" "UI roadmap phase 3"
ensure_label "phase-4" "D93F0B" "UI roadmap phase 4"
ensure_label "phase-5" "B60205" "UI roadmap phase 5"
ensure_label "phase-6" "E99695" "UI roadmap phase 6"
ensure_label "phase-7" "C5DEF5" "UI roadmap phase 7"
ensure_label "testing" "FEF2C0" "Tests and diagnostics"
ensure_label "ui" "D4C5F9" "UI and workflow"
ensure_label "bug" "D73A4A" "Bug fix"
ensure_label "feature" "A2EEEF" "New feature"
ensure_label "migrated-from-upstream" "C2E0C6" "Migrated from davecoulter/YSE_PZ"

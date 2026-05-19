#!/usr/bin/env bash
# Remove superseded YSE Docker images and build cache after a successful pull/build.
# Does NOT remove volumes (MySQL data in VOL_DB is preserved).
set -euo pipefail

AGGRESSIVE=0
if [[ "${1:-}" == "--aggressive" || "${1:-}" == "aggressive" ]]; then
  AGGRESSIVE=1
fi

echo "==> Pruning dangling images..."
docker image prune -f >/dev/null 2>&1 || true

echo "==> Pruning build cache..."
if [[ "$AGGRESSIVE" -eq 1 ]]; then
  docker builder prune -af >/dev/null 2>&1 || docker builder prune -f >/dev/null 2>&1 || true
else
  docker builder prune -f >/dev/null 2>&1 || true
fi

echo "==> Removing unused YSE web images (keeping images used by ysepz_* containers)..."
YSE_REPOS=(
  "ghcr.io/davecoulter/yse_pz"
  "local/yse_pz_web"
)

images_in_use() {
  local ids=""
  local cid
  while IFS= read -r cid; do
    [[ -z "$cid" ]] && continue
    ids+="$(docker inspect -f '{{.Image}}' "$cid" 2>/dev/null || true)"$'\n'
  done < <(docker ps -a -q 2>/dev/null || true)
  echo "$ids" | sort -u | grep -v '^$' || true
}

IN_USE="$(images_in_use)"

image_in_use() {
  local img_id="$1"
  grep -qx "$img_id" <<<"$IN_USE"
}

for repo in "${YSE_REPOS[@]}"; do
  while IFS= read -r img_id; do
    [[ -z "$img_id" ]] && continue
    if image_in_use "$img_id"; then
      continue
    fi
    if docker rmi "$img_id" >/dev/null 2>&1; then
      echo "    removed unused $repo image $img_id"
    fi
  done < <(docker images "$repo" --format '{{.ID}}' 2>/dev/null | sort -u || true)
done

echo "==> Docker disk usage:"
docker system df 2>/dev/null || echo "    (docker system df unavailable)"

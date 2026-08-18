#!/usr/bin/env bash
# Fetch nuScenes keyframe camera images into $NUSCENES_ROOT.
#
# Streams the keyframe tarballs from the AWS Open Data mirror and extracts only
# samples/CAM_*, so sweeps, lidar and radar are discarded without ever touching
# disk. Blobs 01-03 cover every frame the GoldenView benchmark references.
#
#   bash scripts/fetch_nuscenes.sh            # blobs 01 02 03
#   bash scripts/fetch_nuscenes.sh 04         # one specific blob
#
# nuScenes Terms of Use apply. Images are never committed to this repo.
set -euo pipefail

BASE="https://motional-nuscenes.s3.ap-northeast-1.amazonaws.com/public/v1.0"
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

ROOT="${NUSCENES_ROOT:-}"
if [ -z "$ROOT" ]; then
  ROOT="$(cd "$REPO" && python3 -c \
    "import sys; sys.path.insert(0, 'src'); from goldenview import nuscenes_root; print(nuscenes_root())")"
fi

BLOBS=("$@")
if [ ${#BLOBS[@]} -eq 0 ]; then BLOBS=(01 02 03); fi

mkdir -p "$ROOT"
avail=$(df -BG --output=avail "$ROOT" | tail -1 | tr -dc '0-9')
need=$(( ${#BLOBS[@]} * 3 + 1 ))
if [ "$avail" -lt "$need" ]; then
  echo "error: need ~${need}G free at $ROOT, have ${avail}G" >&2
  exit 1
fi

echo "root:  $ROOT"
echo "blobs: ${BLOBS[*]}"
echo "(~4 GB transferred per blob, ~3 GB kept)"

for n in "${BLOBS[@]}"; do
  url="$BASE/v1.0-trainval${n}_keyframes.tgz"
  for attempt in 1 2 3; do
    echo "==> blob $n (attempt $attempt)"
    # pipefail makes a truncated download fail the whole pipeline, so a partial
    # stream is retried rather than silently leaving gaps.
    if curl -fL --connect-timeout 30 "$url" \
         | tar -xz -C "$ROOT" --wildcards 'samples/CAM_*'; then
      echo "==> blob $n done"
      break
    fi
    if [ "$attempt" = 3 ]; then
      echo "error: blob $n failed after 3 attempts" >&2
      exit 1
    fi
    echo "    retrying in 10s..." >&2
    sleep 10
  done
done

echo
echo "Verify coverage:"
echo "  python3 scripts/check_images.py"

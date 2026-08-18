#!/usr/bin/env python3
"""Copy the images the benchmark actually references into a local cache.

The full nuScenes camera set is ~9 GB and normally lives on external storage.
GoldenView only references 438 unique frames (~50 MB), so mirroring just those
onto local disk makes day-to-day work independent of the external drive.

    python3 scripts/materialize_cache.py

Relative paths are preserved, so the cache is itself a valid nuScenes root:
NUSCENES_ROOT=data/image_cache works for anything read-only.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from goldenview import VIEWS, load_split, nuscenes_root  # noqa: E402

SPLITS = ("eval", "eval_inputs", "test")


def referenced_paths() -> set[str]:
    """Every nuScenes-relative image path across all splits."""
    paths: set[str] = set()
    for split in SPLITS:
        for record in load_split(split):
            paths.update(record.views[view] for view in VIEWS)
    return paths


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=None, help="source nuScenes root")
    parser.add_argument("--dest", type=Path, default=REPO / "data" / "image_cache")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    root = args.root or nuscenes_root()
    paths = sorted(referenced_paths())
    print(f"source: {root}")
    print(f"cache:  {args.dest}")
    print(f"referenced images: {len(paths)}")

    copied = skipped = 0
    missing: list[str] = []
    for rel in paths:
        src, dst = root / rel, args.dest / rel
        if not src.exists():
            missing.append(rel)
            continue
        if dst.exists() and dst.stat().st_size == src.stat().st_size:
            skipped += 1
            continue
        if not args.dry_run:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        copied += 1

    print(f"\ncopied {copied}, already present {skipped}, missing at source {len(missing)}")
    if missing:
        print("Source is incomplete. Fetch the remaining blobs:")
        print("  bash scripts/fetch_nuscenes.sh")
        for rel in missing[:5]:
            print(f"    {rel}")
        if len(missing) > 5:
            print(f"    ... and {len(missing) - 5} more")
        return 1
    if not args.dry_run:
        size = sum(f.stat().st_size for f in args.dest.rglob("*.jpg"))
        print(f"cache size: {size / 1024 / 1024:.1f} MB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

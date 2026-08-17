#!/usr/bin/env python3
"""Report how many GoldenViewVQA records have all six views on disk."""

import argparse
import collections
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from goldenview import VIEWS, load_split, nuscenes_root, resolve_views  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=None, help="nuScenes root")
    parser.add_argument("--splits", nargs="+", default=["eval", "test"])
    args = parser.parse_args()

    root = args.root or nuscenes_root()
    print(f"nuScenes root: {root}")
    if not root.exists():
        print("  WARNING: root does not exist")

    all_missing = set()
    for split in args.splits:
        records = load_split(split)
        complete = 0
        missing_by_scene = collections.Counter()
        for record in records:
            gone = [v for v, p in resolve_views(record, root).items() if not p.exists()]
            if gone:
                missing_by_scene[record.scene_name] += len(gone)
                all_missing.update(record.views[v] for v in gone)
            else:
                complete += 1
        print(f"\n{split}: {complete}/{len(records)} records fully resolvable")
        if missing_by_scene:
            print(f"  scenes with gaps: {len(missing_by_scene)}")
            top = ", ".join(s for s, _ in missing_by_scene.most_common(5))
            print(f"  worst: {top}")

    print(f"\nunique images missing across splits: {len(all_missing)}")
    if all_missing:
        print("Download the remaining nuScenes v1.0-trainval blobs, then extract:")
        print("  tar -xzf v1.0-trainvalNN_blobs.tgz --wildcards 'samples/CAM_*'")
    return 1 if all_missing else 0


if __name__ == "__main__":
    raise SystemExit(main())

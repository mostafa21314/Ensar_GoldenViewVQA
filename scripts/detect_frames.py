#!/usr/bin/env python3
"""Run the fine-tuned nuScenes detector over every image the benchmark uses.

Plain detection, no tracker: the task input is a single timestamp, so temporal
association buys nothing here. Confidence is deliberately low, because a missed
object is unrecoverable in the serialised text while a false positive can still
be discounted by a downstream model that sees pixels.

Requires Ultralytics and a fine-tuned detector checkpoint:
  python3 scripts/detect_frames.py --weights /path/to/best.pt
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from goldenview import VIEWS, image_paths, load_split  # noqa: E402

CLASS_NAMES = ["car", "truck", "bus", "trailer", "motorcycle", "bicycle", "pedestrian"]
SPLITS = ("eval", "test")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--weights",
        type=Path,
        default=Path(os.environ["GOLDENVIEW_DETECTOR_WEIGHTS"])
        if os.environ.get("GOLDENVIEW_DETECTOR_WEIGHTS")
        else None,
        help="fine-tuned YOLOv8 checkpoint (or set GOLDENVIEW_DETECTOR_WEIGHTS)",
    )
    parser.add_argument("--conf", type=float, default=0.15)
    parser.add_argument("--iou", type=float, default=0.7)
    parser.add_argument("--batch", type=int, default=12)
    parser.add_argument("--device", default="0")
    parser.add_argument("--out", type=Path, default=REPO / "data" / "detections.json")
    args = parser.parse_args()

    if args.weights is None:
        parser.error("--weights is required (or set GOLDENVIEW_DETECTOR_WEIGHTS)")
    if not args.weights.is_file():
        parser.error(f"detector checkpoint does not exist: {args.weights}")

    from ultralytics import YOLO

    # One entry per (sample_token, camera); tokens repeat across questions so the
    # unique set is much smaller than the record count.
    jobs: dict[tuple[str, str], Path] = {}
    for split in SPLITS:
        for record in load_split(split):
            paths = image_paths(record)
            for view in VIEWS:
                jobs[(record.sample_token, view)] = paths[view]
    print(f"unique (frame, camera) pairs: {len(jobs)}")

    model = YOLO(str(args.weights))
    keys = sorted(jobs)
    out: dict[str, dict[str, list]] = {}

    for start in range(0, len(keys), args.batch):
        chunk = keys[start : start + args.batch]
        results = model.predict(
            [str(jobs[k]) for k in chunk],
            conf=args.conf, iou=args.iou, device=args.device, verbose=False,
        )
        for (token, camera), res in zip(chunk, results):
            dets = []
            boxes = res.boxes
            if boxes is not None:
                for i in range(len(boxes)):
                    x1, y1, x2, y2 = (float(v) for v in boxes.xyxy[i].tolist())
                    cls_id = int(boxes.cls[i])
                    dets.append({
                        "class_id": cls_id,
                        "class_name": CLASS_NAMES[cls_id] if cls_id < len(CLASS_NAMES) else "unknown",
                        "confidence": float(boxes.conf[i]),
                        "bbox_xyxy": [round(x1, 2), round(y1, 2), round(x2, 2), round(y2, 2)],
                        "cx_px": round((x1 + x2) / 2, 2),
                    })
            out.setdefault(token, {})[camera] = dets
        print(f"  {min(start + args.batch, len(keys))}/{len(keys)}", flush=True)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out))
    total = sum(len(d) for cams in out.values() for d in cams.values())
    print(f"\nframes {len(out)}  detections {total}  "
          f"mean {total / max(len(out), 1):.1f} per frame (6 cameras)")
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

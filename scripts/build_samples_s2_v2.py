#!/usr/bin/env python3
"""Emit gold-free System 2 v2 prompts with stricter association and guidance."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from goldenview import image_paths, load_split  # noqa: E402
from goldenview.bev import associate  # noqa: E402
from goldenview.serialize import full_render_v2  # noqa: E402

CAMERA_ORDER = (
    "CAM_FRONT_LEFT", "CAM_FRONT", "CAM_FRONT_RIGHT",
    "CAM_BACK_LEFT", "CAM_BACK", "CAM_BACK_RIGHT",
)

INSTRUCTIONS = """You are given six synchronized camera images from a vehicle,
an approximate object-detector summary, a question, and four answer options.

CAMERA LAYOUT
Front row: CAM_FRONT_LEFT | CAM_FRONT | CAM_FRONT_RIGHT
Rear row:  CAM_BACK_LEFT  | CAM_BACK  | CAM_BACK_RIGHT
Adjacent cameras overlap. Select the camera showing the decisive evidence most
directly and centrally, not merely another camera containing a partial overlap.

The detector recognizes only car, truck, bus, trailer, motorcycle, bicycle, and
pedestrian. It misses signs, signals, markings, barriers, brake lights, gestures,
and other appearance details. Its counts, bearings, range bands, confidence bands,
and cross-view associations are approximate. Trust clearly visible pixels whenever
they disagree with the detector summary.

DECISION PROCEDURE
1. Determine which visible evidence would distinguish the four options.
2. Inspect all six labelled images; do not default to CAM_FRONT.
3. Select the answer supported by the visible evidence.
4. Select the single camera showing that decisive evidence most directly.
5. Select NONE_OF_THE_ABOVE when no individual camera provides sufficient evidence.

For intent or future-manoeuvre questions, do not infer commitment from ordinary
lane position alone. Require a visible commitment cue such as established lateral
displacement, a visible signal, wheel orientation, an occupied turn lane, or scene
geometry that makes the manoeuvre unambiguous. Otherwise choose the
insufficient-evidence option when one is available.

Return JSON only with predicted_view and predicted_answer_id. predicted_view must
be CAM_FRONT, CAM_FRONT_LEFT, CAM_FRONT_RIGHT, CAM_BACK, CAM_BACK_LEFT,
CAM_BACK_RIGHT, or NONE_OF_THE_ABOVE. predicted_answer_id must be A, B, C, or D."""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--detections", type=Path, default=REPO / "data" / "detections.json")
    parser.add_argument("--splits", nargs="+", default=["eval"])
    parser.add_argument("--outdir", type=Path, default=REPO / "data")
    args = parser.parse_args()

    detections = json.loads(args.detections.read_text())
    objects_by_token = {
        token: associate(
            cameras,
            prevent_same_camera_merge=True,
            restrict_to_overlapping_cameras=True,
        )
        for token, cameras in detections.items()
    }

    for split in args.splits:
        rows = []
        for record in load_split(split):
            paths = image_paths(record)
            options = "\n".join(f"{key}. {record.options[key]}" for key in sorted(record.options))
            rows.append({
                "question_id": record.question_id,
                "instructions": INSTRUCTIONS,
                "question": record.question,
                "options_text": options,
                "scene_text": full_render_v2(objects_by_token.get(record.sample_token, [])),
                "images": [
                    {"camera": camera, "path": str(paths[camera])}
                    for camera in CAMERA_ORDER
                ],
            })

        output = args.outdir / f"prompts_{split}_s2_v2.jsonl"
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(f"{split}: {len(rows)} rows -> {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

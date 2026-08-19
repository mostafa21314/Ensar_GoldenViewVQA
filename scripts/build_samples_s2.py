#!/usr/bin/env python3
"""Emit System 2 inputs: scene text plus the six image paths, no labels.

System 2 supplies the symbolic scene description *and* the pixels. The text goes
first so the model can bind sections to images, and every image is labelled with
its camera name.

    python3 scripts/build_samples_s2.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from goldenview import VIEWS, image_paths, load_split  # noqa: E402
from goldenview.bev import associate  # noqa: E402
from goldenview.serialize import full_render  # noqa: E402

INSTRUCTIONS = """You are given six camera images from a vehicle plus a structured \
description of what an object detector found in them, then a multiple-choice question.

The detector sees only 7 agent classes (car, truck, bus, trailer, motorcycle, \
bicycle, pedestrian). It cannot see traffic lights, signs, cones, road markings, \
lane geometry, barriers or brake lights. The images show everything; the text adds \
precise counts, metric bearings, and cross-view identity that images alone do not \
give. Where text and pixels disagree, trust the pixels.

Answer two things:
1. predicted_view - which single camera provides the most direct visual evidence \
for answering the question. Exactly one of: CAM_FRONT, CAM_FRONT_LEFT, \
CAM_FRONT_RIGHT, CAM_BACK, CAM_BACK_LEFT, CAM_BACK_RIGHT, or NONE_OF_THE_ABOVE if \
no single camera suffices.
2. predicted_answer_id - the correct option, exactly one of A, B, C, D."""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--detections", type=Path, default=REPO / "data" / "detections.json")
    parser.add_argument("--splits", nargs="+", default=["eval", "test"])
    parser.add_argument("--outdir", type=Path, default=REPO / "data")
    args = parser.parse_args()

    detections = json.loads(args.detections.read_text())
    objects_by_token = {tok: associate(cams) for tok, cams in detections.items()}

    for split in args.splits:
        rows = []
        for record in load_split(split):
            objs = objects_by_token.get(record.sample_token, [])
            paths = image_paths(record)
            opts = "\n".join(f"{k}. {record.options[k]}" for k in sorted(record.options))
            rows.append({
                "question_id": record.question_id,
                "instructions": INSTRUCTIONS,
                "scene_text": full_render(objs),
                "question": record.question,
                "options_text": opts,
                # Ordered so the reader sees front row then rear row.
                "images": [{"camera": v, "path": str(paths[v])} for v in (
                    "CAM_FRONT_LEFT", "CAM_FRONT", "CAM_FRONT_RIGHT",
                    "CAM_BACK_LEFT", "CAM_BACK", "CAM_BACK_RIGHT")],
            })
        out = args.outdir / f"prompts_{split}_s2.jsonl"
        with out.open("w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(f"{split}: {len(rows)} rows -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

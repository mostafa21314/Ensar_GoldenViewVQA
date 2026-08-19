#!/usr/bin/env python3
"""Assemble model-ready samples: image paths, BEV objects, and serialised text.

Reads data/detections.json, projects every detection to the ground plane,
associates across cameras into objects carrying a view-set, and renders the text.
Emits one self-contained JSON per split so any model can be run against it
without rebuilding the perception stack.

    python3 scripts/build_samples.py
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from goldenview import VIEWS, image_paths, load_split  # noqa: E402
from goldenview.bev import associate  # noqa: E402
from goldenview.rig import CAMERAS  # noqa: E402
from goldenview.serialize import full_render, isolated_render  # noqa: E402

INSTRUCTIONS = """You are given a description of a driving scene captured by six \
cameras mounted on a vehicle, followed by a multiple-choice question.

Answer two things:
1. predicted_view - which single camera provides the most direct visual evidence \
for answering the question. Must be exactly one of: CAM_FRONT, CAM_FRONT_LEFT, \
CAM_FRONT_RIGHT, CAM_BACK, CAM_BACK_LEFT, CAM_BACK_RIGHT, or NONE_OF_THE_ABOVE \
if no single camera is sufficient.
2. predicted_answer_id - the correct option, exactly one of A, B, C, D.

Reply with JSON only: {"predicted_view": "...", "predicted_answer_id": "..."}"""


def build_prompt(scene_text: str, question: str, options: dict) -> str:
    opts = "\n".join(f"{k}. {options[k]}" for k in sorted(options))
    return f"{INSTRUCTIONS}\n\n{scene_text}\nQUESTION: {question}\n\nOPTIONS:\n{opts}\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--detections", type=Path, default=REPO / "data" / "detections.json")
    parser.add_argument("--splits", nargs="+", default=["eval", "test"])
    parser.add_argument("--outdir", type=Path, default=REPO / "data")
    parser.add_argument("--isolated", action="store_true",
                        help="also emit per-camera isolated renders (System 3)")
    args = parser.parse_args()

    detections = json.loads(args.detections.read_text())
    # One frame is shared by several questions, so associate once per token.
    objects_by_token = {tok: associate(cams) for tok, cams in detections.items()}

    for split in args.splits:
        records = load_split(split)
        samples = []
        for record in records:
            objs = objects_by_token.get(record.sample_token, [])
            scene_text = full_render(objs)
            paths = image_paths(record)
            sample = {
                "question_id": record.question_id,
                "question_group": record.question_group,
                "question": record.question,
                "options": record.options,
                "scene_name": record.scene_name,
                "sample_token": record.sample_token,
                "frame_idx": record.frame_idx,
                "time_s": record.time_s,
                "image_paths": {v: str(paths[v]) for v in VIEWS},
                "views_relative": record.views,
                "objects": [o.as_dict() for o in objs],
                "scene_text": scene_text,
                "prompt": build_prompt(scene_text, record.question, record.options),
            }
            if args.isolated:
                sample["isolated_text"] = {c: isolated_render(objs, c) for c in CAMERAS}
            if record.labeled:
                sample["gold"] = {
                    "golden_view": record.golden_view,
                    "gold_answer_id": record.gold_answer_id,
                }
            samples.append(sample)

        out = args.outdir / f"samples_{split}.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(samples, indent=2, ensure_ascii=False))

        # Label-free companion: one line per question, ready to feed any model.
        # Kept separate so a model run against it cannot see gold fields.
        prompts = args.outdir / f"prompts_{split}.jsonl"
        with prompts.open("w", encoding="utf-8") as handle:
            for s in samples:
                handle.write(json.dumps({
                    "question_id": s["question_id"],
                    "prompt": s["prompt"],
                }, ensure_ascii=False) + "\n")

        nobj = [len(s["objects"]) for s in samples]
        multi = [sum(1 for o in s["objects"] if len(o["views"]) > 1) for s in samples]
        empty = sum(1 for s in samples if not s["objects"])
        print(f"{split}: {len(samples)} samples -> {out}")
        print(f"  objects/frame  median {statistics.median(nobj):.0f}  "
              f"mean {statistics.mean(nobj):.1f}  min {min(nobj)}  max {max(nobj)}")
        print(f"  multi-view objects/frame  mean {statistics.mean(multi):.1f}")
        print(f"  frames with zero objects: {empty}")
        print(f"  prompt chars  median {statistics.median(len(s['prompt']) for s in samples):.0f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

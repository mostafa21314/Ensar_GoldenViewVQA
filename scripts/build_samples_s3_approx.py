#!/usr/bin/env python3
"""Emit gold-free inputs for agent-based per-view evidence ranking.

This is an approximation of System 3. It records ordinal evidence judgments from
an agent; it does not claim to expose model logits or compute KL divergence.

    python3 scripts/build_samples_s3_approx.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from goldenview import image_paths, load_split  # noqa: E402
from goldenview.bev import associate  # noqa: E402
from goldenview.rig import CAMERAS  # noqa: E402
from goldenview.serialize import isolated_render  # noqa: E402

CAMERA_ORDER = (
    "CAM_FRONT_LEFT",
    "CAM_FRONT",
    "CAM_FRONT_RIGHT",
    "CAM_BACK_LEFT",
    "CAM_BACK",
    "CAM_BACK_RIGHT",
)

METHOD = """This is agent-based per-view evidence ranking, an approximation of
view-marginal information gain. It does not use logits and is not KL divergence.

First answer the question from only its wording and options to establish a prior
answer. Then evaluate each camera independently. For a camera judgment, use only
that camera's image and isolated detector text; do not import visual evidence from
another camera.

For each camera return an answer_id and integer evidence_strength:
0 = no relevant visual evidence
1 = weak context, insufficient to answer
2 = relevant but indirect or ambiguous evidence
3 = direct, useful evidence
4 = decisive direct evidence

Select the camera with the strongest direct answer-disambiguating evidence. Break
ties by choosing the camera whose evidence most directly distinguishes the answer
options. Select NONE_OF_THE_ABOVE only when every camera scores 0 or 1. The final
answer is the selected camera's answer; for NONE_OF_THE_ABOVE use the prior answer.
Evidence strength is an ordinal agent judgment, not a calibrated probability."""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--detections", type=Path, default=REPO / "data" / "detections.json")
    parser.add_argument("--splits", nargs="+", default=["eval", "test"])
    parser.add_argument("--outdir", type=Path, default=REPO / "data")
    args = parser.parse_args()

    detections = json.loads(args.detections.read_text())
    objects_by_token = {token: associate(cameras) for token, cameras in detections.items()}

    for split in args.splits:
        rows = []
        for record in load_split(split):
            objects = objects_by_token.get(record.sample_token, [])
            paths = image_paths(record)
            rows.append(
                {
                    "question_id": record.question_id,
                    "method": METHOD,
                    "question": record.question,
                    "options": {key: record.options[key] for key in sorted(record.options)},
                    "views": [
                        {
                            "camera": camera,
                            "image_path": str(paths[camera]),
                            "isolated_text": isolated_render(objects, camera),
                        }
                        for camera in CAMERA_ORDER
                    ],
                }
            )

        output = args.outdir / f"prompts_{split}_s3_approx.jsonl"
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(f"{split}: {len(rows)} rows -> {output}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

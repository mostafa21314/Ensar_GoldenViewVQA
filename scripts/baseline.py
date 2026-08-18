#!/usr/bin/env python3
"""Write a label-only baseline prediction file.

    python3 scripts/baseline.py --strategy constant --split eval
    python3 scripts/baseline.py --strategy prior_random --split eval --seed 3

These read no images. They exist to establish the floor a real system must beat.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from goldenview import load_split  # noqa: E402
from goldenview.baselines import STRATEGIES  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strategy", choices=sorted(STRATEGIES), default="constant")
    parser.add_argument("--split", default="eval")
    parser.add_argument("--view", default="CAM_FRONT", help="constant strategy only")
    parser.add_argument("--answer", default="A", help="constant strategy only")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    records = load_split(args.split)
    fn = STRATEGIES[args.strategy]
    if args.strategy == "constant":
        preds = fn(records, view=args.view, answer=args.answer)
    elif args.strategy == "majority":
        preds = fn(records, reference=load_split("eval"))
    elif args.strategy == "prior_random":
        preds = fn(records, reference=load_split("eval"), seed=args.seed)
    else:
        preds = fn(records, seed=args.seed)

    out = args.out or REPO / "predictions" / f"{args.split}_{args.strategy}.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as handle:
        for pred in preds:
            handle.write(json.dumps(pred, ensure_ascii=False) + "\n")
    print(f"wrote {len(preds)} predictions to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

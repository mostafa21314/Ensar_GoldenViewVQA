#!/usr/bin/env python3
"""Merge sharded prediction files into one submission and check integrity.

    python3 scripts/merge_shards.py --pattern 'predictions/s2_shards/eval_s2_*.jsonl' \
        --split eval --out predictions/eval_system2_opus.jsonl
"""

from __future__ import annotations

import argparse
import glob
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from goldenview import ANSWER_IDS, VIEW_LABELS, load_split  # noqa: E402

FIELDS = {"question_id", "predicted_view", "predicted_answer_id"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pattern", required=True)
    parser.add_argument("--split", default="eval")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    files = sorted(glob.glob(args.pattern))
    if not files:
        print(f"no files matched {args.pattern}", file=sys.stderr)
        return 1

    rows: dict[str, dict] = {}
    problems: list[str] = []
    for path in files:
        n = 0
        for line in Path(path).read_text().splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            n += 1
            qid = row.get("question_id")
            if set(row) != FIELDS:
                problems.append(f"{path}: {qid} has fields {sorted(row)}")
            if row.get("predicted_view") not in VIEW_LABELS:
                problems.append(f"{path}: {qid} bad view {row.get('predicted_view')!r}")
            if row.get("predicted_answer_id") not in ANSWER_IDS:
                problems.append(f"{path}: {qid} bad answer {row.get('predicted_answer_id')!r}")
            if qid in rows:
                problems.append(f"duplicate question_id across shards: {qid}")
            rows[qid] = {k: row[k] for k in FIELDS if k in row}
        print(f"  {path}: {n} rows")

    expected = [r.question_id for r in load_split(args.split)]
    missing = [q for q in expected if q not in rows]
    extra = [q for q in rows if q not in expected]
    if missing:
        problems.append(f"missing {len(missing)}: {missing[:5]}")
    if extra:
        problems.append(f"unexpected {len(extra)}: {extra[:5]}")

    if problems:
        print("\nPROBLEMS:")
        for p in problems:
            print(f"  {p}")
        return 1

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as handle:
        for qid in expected:                      # canonical input order
            handle.write(json.dumps(rows[qid], ensure_ascii=False) + "\n")
    print(f"\nmerged {len(expected)} predictions -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

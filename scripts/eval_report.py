#!/usr/bin/env python3
"""Evaluate a prediction file and report where the score actually comes from.

    python3 scripts/eval_report.py --pred predictions/eval_constant.jsonl

The headline numbers come from the organizers' own evaluate.py, imported rather
than reimplemented, so they cannot drift. Everything else here is diagnostics
layered on top: per-question-group scores, a view confusion matrix, and
bootstrap intervals.

The intervals are the point. With 55 dev records and two view classes holding a
single example each, a macro-accuracy difference smaller than the interval width
is noise, not progress.
"""

from __future__ import annotations

import argparse
import collections
import json
import random
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "external" / "goldenview" / "scripts"))

from evaluate import evaluate  # noqa: E402  (organizers' metric, not ours)
from submission_validation import read_jsonl  # noqa: E402

from goldenview import VIEW_LABELS, dataset_dir  # noqa: E402

HEADLINE = ("view_accuracy", "view_macro_accuracy", "answer_accuracy", "joint_accuracy")


def bootstrap(gold: list[dict], pred: list[dict], rounds: int, seed: int) -> dict[str, tuple]:
    """Percentile intervals by resampling questions with replacement.

    Resampling duplicates question_ids, which the organizers' validator rejects,
    so each draw is re-keyed with a unique suffix. Per-item correctness and the
    class mix are unchanged, which is all the metrics depend on.
    """
    rng = random.Random(seed)
    pred_by_id = {p["question_id"]: p for p in pred}
    draws: dict[str, list[float]] = {k: [] for k in HEADLINE}
    n = len(gold)
    for _ in range(rounds):
        picks = [rng.randrange(n) for _ in range(n)]
        g_draw, p_draw = [], []
        for slot, idx in enumerate(picks):
            g = dict(gold[idx])
            key = f"{g['question_id']}__b{slot}"
            p = dict(pred_by_id[g["question_id"]])
            g["question_id"] = p["question_id"] = key
            g_draw.append(g)
            p_draw.append(p)
        m = evaluate(g_draw, p_draw)
        for k in HEADLINE:
            draws[k].append(m[k])
    out = {}
    for k, values in draws.items():
        values.sort()
        lo = values[int(0.025 * len(values))]
        hi = values[min(int(0.975 * len(values)), len(values) - 1)]
        out[k] = (lo, hi, statistics.mean(values))
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pred", required=True, type=Path)
    parser.add_argument("--gold", type=Path, default=None)
    parser.add_argument("--bootstrap", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--json", action="store_true", help="emit machine-readable output")
    args = parser.parse_args()

    gold_path = args.gold or dataset_dir() / "data" / "eval.jsonl"
    gold = read_jsonl(gold_path)
    pred = read_jsonl(args.pred)
    metrics = evaluate(gold, pred)

    if args.json:
        print(json.dumps(metrics, indent=2))
        return 0

    print(f"pred: {args.pred}")
    print(f"gold: {gold_path}  (n={metrics['total']})")

    print("\nofficial metrics")
    for k in HEADLINE:
        print(f"  {k:22s} {metrics[k]:.4f}")

    if args.bootstrap:
        print(f"\n95% bootstrap intervals ({args.bootstrap} resamples)")
        for k, (lo, hi, mean) in bootstrap(gold, pred, args.bootstrap, args.seed).items():
            print(f"  {k:22s} [{lo:.3f}, {hi:.3f}]  width {hi - lo:.3f}")

    print("\nper view class (gold count, recall)")
    counts = collections.Counter(g["golden_view"] for g in gold)
    for label in VIEW_LABELS:
        if label in counts:
            recall = metrics["view_recall_by_class"].get(label, 0.0)
            print(f"  {label:22s} n={counts[label]:<3d} recall={recall:.3f}")

    print("\nper question group")
    by_group = collections.defaultdict(list)
    for g in gold:
        by_group[g["question_group"]].append(g)
    pred_by_id = {p["question_id"]: p for p in pred}
    for group, rows in sorted(by_group.items()):
        sub_pred = [pred_by_id[r["question_id"]] for r in rows]
        m = evaluate(rows, sub_pred)
        print(
            f"  {group:20s} n={m['total']:<3d} "
            f"view={m['view_accuracy']:.3f} macro={m['view_macro_accuracy']:.3f} "
            f"answer={m['answer_accuracy']:.3f} joint={m['joint_accuracy']:.3f}"
        )

    print("\nview confusion (gold -> predicted, errors only)")
    gold_by_id = {g["question_id"]: g for g in gold}
    confusion = collections.Counter(
        (g["golden_view"], pred_by_id[qid]["predicted_view"])
        for qid, g in gold_by_id.items()
        if pred_by_id[qid]["predicted_view"] != g["golden_view"]
    )
    if not confusion:
        print("  none")
    for (want, got), count in confusion.most_common(10):
        print(f"  {want:22s} -> {got:22s} {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

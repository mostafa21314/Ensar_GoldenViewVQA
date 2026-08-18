"""Label-only baselines that establish the floor any real system must clear.

None of these look at an image. They exist so a model's score can be read as
"better than guessing" rather than in isolation, which matters here because the
view labels are severely imbalanced.
"""

from __future__ import annotations

import collections
import random
from typing import Callable, Iterable

from .data import ANSWER_IDS, VIEW_LABELS, Record

Prediction = dict[str, str]


def _emit(record: Record, view: str, answer: str) -> Prediction:
    return {
        "question_id": record.question_id,
        "predicted_view": view,
        "predicted_answer_id": answer,
    }


def constant(records: Iterable[Record], view: str = "CAM_FRONT", answer: str = "A") -> list[Prediction]:
    """Always the same pair. The 'always CAM_FRONT' reference point."""
    return [_emit(r, view, answer) for r in records]


def uniform_random(records: Iterable[Record], seed: int = 0) -> list[Prediction]:
    """Uniform over all seven view labels and four answer letters."""
    rng = random.Random(seed)
    return [
        _emit(r, rng.choice(VIEW_LABELS), rng.choice(ANSWER_IDS))
        for r in records
    ]


def prior_random(records: Iterable[Record], reference: list[Record], seed: int = 0) -> list[Prediction]:
    """Sample from the label distribution observed in a labeled reference split.

    Scores like the majority baseline on micro accuracy but, unlike `constant`,
    puts non-zero mass on rare views, so it is the fairer macro-accuracy floor.
    """
    rng = random.Random(seed)
    labeled = [r for r in reference if r.labeled]
    views = [r.golden_view for r in labeled]
    answers = [r.gold_answer_id for r in labeled]
    if not views:
        raise ValueError("reference split carries no labels")
    return [_emit(r, rng.choice(views), rng.choice(answers)) for r in records]


def majority(records: Iterable[Record], reference: list[Record]) -> list[Prediction]:
    """The single most frequent view and answer in a labeled reference split."""
    labeled = [r for r in reference if r.labeled]
    if not labeled:
        raise ValueError("reference split carries no labels")
    view = collections.Counter(r.golden_view for r in labeled).most_common(1)[0][0]
    answer = collections.Counter(r.gold_answer_id for r in labeled).most_common(1)[0][0]
    return [_emit(r, view, answer) for r in records]


STRATEGIES: dict[str, Callable] = {
    "constant": constant,
    "uniform_random": uniform_random,
    "prior_random": prior_random,
    "majority": majority,
}

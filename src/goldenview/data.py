"""Loading GoldenViewVQA records and resolving their nuScenes images."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from .config import dataset_dir, image_cache, nuscenes_root

VIEWS = (
    "CAM_FRONT",
    "CAM_FRONT_LEFT",
    "CAM_FRONT_RIGHT",
    "CAM_BACK",
    "CAM_BACK_LEFT",
    "CAM_BACK_RIGHT",
)

# A seventh view label, valid in gold and in submissions, but never an input image.
NONE_OF_THE_ABOVE = "NONE_OF_THE_ABOVE"
VIEW_LABELS = VIEWS + (NONE_OF_THE_ABOVE,)

ANSWER_IDS = ("A", "B", "C", "D")

SPLIT_FILES = {
    "eval": "data/eval.jsonl",
    "eval_inputs": "data/eval_inputs.jsonl",
    "test": "data/test_inputs.jsonl",
}


@dataclass(frozen=True)
class Record:
    question_id: str
    question: str
    question_group: str
    options: dict
    views: dict
    scene_name: str
    sample_token: str
    frame_idx: int
    time_s: float
    golden_view: str | None = None
    gold_answer_id: str | None = None
    gold_answer_text: str | None = None

    @property
    def labeled(self) -> bool:
        return self.golden_view is not None


def load_split(split: str, directory: Path | None = None) -> list[Record]:
    """Read one split into Record objects. Test records carry no labels."""
    if split not in SPLIT_FILES:
        raise KeyError(f"unknown split {split!r}, expected one of {sorted(SPLIT_FILES)}")
    path = (directory or dataset_dir()) / SPLIT_FILES[split]
    if not path.exists():
        raise FileNotFoundError(
            f"{path} missing. Clone the dataset: "
            "git clone https://huggingface.co/datasets/GoldenViewVQA/GoldenViewVQA external/goldenview"
        )
    fields = Record.__dataclass_fields__
    with path.open() as handle:
        return [
            Record(**{k: v for k, v in json.loads(line).items() if k in fields})
            for line in handle
            if line.strip()
        ]


def resolve_views(record: Record, root: Path | None = None) -> dict[str, Path]:
    """Map each camera to its path under the full nuScenes root, present or not.

    Deliberately ignores the local cache: this is what verifies the root itself
    is complete.
    """
    base = Path(root) if root is not None else nuscenes_root()
    return {view: base / record.views[view] for view in VIEWS}


def image_paths(record: Record, root: Path | None = None) -> dict[str, Path]:
    """Map each camera to a readable image path, preferring the local cache.

    The cache holds only the frames the benchmark references, so it is small
    enough to sit on fast local disk while the full root may not be.
    """
    cache = image_cache()
    base = Path(root) if root is not None else nuscenes_root()
    resolved = {}
    for view in VIEWS:
        rel = record.views[view]
        cached = cache / rel if cache else None
        resolved[view] = cached if cached and cached.exists() else base / rel
    return resolved


def missing_views(record: Record, root: Path | None = None) -> list[str]:
    """Camera names whose image is not on disk under the full root."""
    return [v for v, p in resolve_views(record, root).items() if not p.exists()]


def iter_complete(records: list[Record], root: Path | None = None) -> Iterator[Record]:
    """Yield only records whose six views all resolve on disk."""
    for record in records:
        if not missing_views(record, root):
            yield record

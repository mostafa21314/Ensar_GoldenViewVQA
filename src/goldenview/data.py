"""Loading GoldenViewVQA records and resolving their nuScenes images."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

VIEWS = (
    "CAM_FRONT",
    "CAM_FRONT_LEFT",
    "CAM_FRONT_RIGHT",
    "CAM_BACK",
    "CAM_BACK_LEFT",
    "CAM_BACK_RIGHT",
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DATASET_DIR = REPO_ROOT / "external" / "goldenview"

SPLIT_FILES = {
    "eval": "data/eval.jsonl",
    "eval_inputs": "data/eval_inputs.jsonl",
    "test": "data/test_inputs.jsonl",
}


def nuscenes_root() -> Path:
    """Local nuScenes root holding samples/CAM_*.

    NUSCENES_ROOT wins; otherwise fall back to configs/default.yaml.
    """
    env = os.environ.get("NUSCENES_ROOT")
    if env:
        return Path(env)
    config = REPO_ROOT / "configs" / "default.yaml"
    if config.exists():
        for line in config.read_text().splitlines():
            if line.startswith("nuscenes_root:"):
                return Path(line.split(":", 1)[1].strip())
    raise RuntimeError("set NUSCENES_ROOT or nuscenes_root in configs/default.yaml")


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


def load_split(split: str, dataset_dir: Path | None = None) -> list[Record]:
    """Read one split into Record objects. Test records carry no labels."""
    if split not in SPLIT_FILES:
        raise KeyError(f"unknown split {split!r}, expected one of {sorted(SPLIT_FILES)}")
    path = (dataset_dir or DATASET_DIR) / SPLIT_FILES[split]
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
    """Map each camera name to its absolute image path, present or not."""
    base = Path(root) if root is not None else nuscenes_root()
    return {view: base / record.views[view] for view in VIEWS}


def missing_views(record: Record, root: Path | None = None) -> list[str]:
    """Camera names whose image is not on disk."""
    return [v for v, p in resolve_views(record, root).items() if not p.exists()]


def iter_complete(records: list[Record], root: Path | None = None) -> Iterator[Record]:
    """Yield only records whose six views all resolve on disk."""
    for record in records:
        if not missing_views(record, root):
            yield record

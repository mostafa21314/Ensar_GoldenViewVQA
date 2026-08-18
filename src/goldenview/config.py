"""Repo paths and settings, resolved from configs/default.yaml and the env."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPO_ROOT / "configs" / "default.yaml"


@lru_cache(maxsize=1)
def load_config(path: Path | None = None) -> dict:
    """Parse configs/default.yaml. Missing file yields an empty config."""
    target = path or CONFIG_PATH
    if not target.exists():
        return {}
    return yaml.safe_load(target.read_text()) or {}


def _as_path(value: str | None) -> Path | None:
    """Absolute paths pass through; relative ones resolve against the repo."""
    if not value:
        return None
    path = Path(value).expanduser()
    return path if path.is_absolute() else REPO_ROOT / path


def nuscenes_root() -> Path:
    """Full nuScenes root holding samples/CAM_*. NUSCENES_ROOT wins."""
    root = _as_path(os.environ.get("NUSCENES_ROOT")) or _as_path(
        load_config().get("nuscenes_root")
    )
    if root is None:
        raise RuntimeError("set NUSCENES_ROOT or nuscenes_root in configs/default.yaml")
    return root


def image_cache() -> Path | None:
    """Local mirror of only the frames the benchmark references, if configured."""
    return _as_path(load_config().get("image_cache"))


def dataset_dir() -> Path:
    """The GoldenViewVQA checkout holding data/, schema/ and scripts/."""
    return _as_path(load_config().get("dataset_dir")) or REPO_ROOT / "external" / "goldenview"

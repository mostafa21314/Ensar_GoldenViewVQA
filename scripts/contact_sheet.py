#!/usr/bin/env python3
"""Render one record's six views to a single image, for eyeballing.

    python3 scripts/contact_sheet.py --split eval --index 0

Layout matches the physical camera arrangement, front row on top, so the
spatial relationship between views is readable at a glance.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from goldenview import image_paths, load_split  # noqa: E402

# Physical arrangement, not alphabetical: front row on top, rear row below.
GRID = (
    ("CAM_FRONT_LEFT", "CAM_FRONT", "CAM_FRONT_RIGHT"),
    ("CAM_BACK_LEFT", "CAM_BACK", "CAM_BACK_RIGHT"),
)
TILE_W = 480
LABEL_H = 22


def build(record, width: int = TILE_W) -> Image.Image:
    paths = image_paths(record)
    tiles: dict[str, Image.Image] = {}
    height = 0
    for row in GRID:
        for view in row:
            src = paths[view]
            if not src.exists():
                raise FileNotFoundError(f"{view}: {src}")
            img = Image.open(src).convert("RGB")
            img = img.resize((width, round(img.height * width / img.width)))
            tiles[view] = img
            height = max(height, img.height)

    sheet = Image.new("RGB", (width * 3, (height + LABEL_H) * 2), "black")
    draw = ImageDraw.Draw(sheet)
    for r, row in enumerate(GRID):
        for c, view in enumerate(row):
            x, y = c * width, r * (height + LABEL_H)
            draw.text((x + 6, y + 5), view, fill="white")
            sheet.paste(tiles[view], (x, y + LABEL_H))
    return sheet


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--split", default="eval")
    parser.add_argument("--index", type=int, default=0)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    records = load_split(args.split)
    record = records[args.index]
    out = args.out or REPO / "predictions" / f"contact_{record.question_id}.jpg"
    out.parent.mkdir(parents=True, exist_ok=True)
    build(record).save(out, quality=88)

    print(f"question_id : {record.question_id}")
    print(f"group       : {record.question_group}")
    print(f"question    : {record.question}")
    for key, text in sorted(record.options.items()):
        print(f"   {key}. {text}")
    if record.labeled:
        print(f"gold view   : {record.golden_view}")
        print(f"gold answer : {record.gold_answer_id}")
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

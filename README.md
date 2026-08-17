# GoldenViewVQA — shared task work

Code for the EMNLP GoldenView VQA shared task: given six synchronized nuScenes
camera views and a question, identify the supporting view and pick the answer.

## Layout

```
src/goldenview/     loaders and shared code
scripts/            entry points (check_images.py, ...)
configs/            paths and run settings
external/goldenview dataset checkout (gitignored)
```

## Setup

Dataset (annotations only, ~600 KB, no images):

```bash
git clone https://huggingface.co/datasets/GoldenViewVQA/GoldenViewVQA external/goldenview
```

Pinned at commit `c9402cd4116a3d1142237dffd332803e9c843e20` (see `external/.goldenview-commit`).

nuScenes images are not redistributed. Download `v1.0-trainval` camera data from
the official nuScenes site and extract keyframe images only:

```bash
tar -xzf v1.0-trainvalNN_blobs.tgz --wildcards 'samples/CAM_*'
```

Point the code at it:

```bash
export NUSCENES_ROOT=/path/to/nuscenes   # dir containing samples/CAM_*
python3 scripts/check_images.py
```

## Data notes

- No training split exists. 55 labeled dev records, 59 input-only test records.
- The benchmark spans nuScenes trainval blobs 01-03 only.
- Submissions carry exactly three fields: `question_id`, `predicted_view`,
  `predicted_answer_id`. No free-form answer text.

## Evaluating

Use the organizers' scripts against the dev split:

```bash
python3 external/goldenview/scripts/evaluate.py \
  --gold external/goldenview/data/eval.jsonl \
  --pred predictions/dev.jsonl
```

Watch `view_macro_accuracy`, not `view_accuracy`. Always predicting `CAM_FRONT`
scores 0.69 micro but 0.14 macro.

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

nuScenes images are not redistributed and must be obtained under the nuScenes
Terms of Use. Only blobs 01-03 are needed, and only the keyframe (`samples/`)
tarballs, which excludes sweeps and cuts the download from ~86 GB to ~12 GB:

```bash
B=https://motional-nuscenes.s3.ap-northeast-1.amazonaws.com/public/v1.0
mkdir -p "$NUSCENES_ROOT" && cd "$NUSCENES_ROOT"
for n in 01 02 03; do
  curl -L "$B/v1.0-trainval${n}_keyframes.tgz" | tar -xz --wildcards 'samples/CAM_*'
done
```

Streaming through `tar` keeps only the camera JPEGs (~9 GB) and never writes a
tarball to disk. The bucket is the AWS Open Data mirror: anonymous HTTPS, no
signed URLs. Total requirement is 438 unique images across all splits.

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

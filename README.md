# GoldenViewVQA — shared task work

Code for the EMNLP GoldenView VQA shared task: given six synchronized nuScenes
camera views and a question, identify the supporting view and pick the answer.

## Layout

```
src/goldenview/       loaders and shared code
scripts/              entry points (fetch_nuscenes.sh, check_images.py, ...)
configs/default.yaml  paths and run settings
data/image_cache/     the 438 referenced JPEGs, on local disk (gitignored)
predictions/          model output and submissions (gitignored)
external/goldenview/  dataset checkout (gitignored)
DATASET_COMMIT        pinned dataset revision (tracked)
```

## Setup

Dataset (annotations only, ~600 KB, no images):

```bash
git clone https://huggingface.co/datasets/GoldenViewVQA/GoldenViewVQA external/goldenview
```

Pinned at the revision in `DATASET_COMMIT`. `external/` is gitignored, so the
pin lives in a tracked file at the repo root:

```bash
git -C external/goldenview checkout "$(cat DATASET_COMMIT)"
```

nuScenes images are not redistributed and must be obtained under the nuScenes
Terms of Use. Only blobs 01-03 are needed, and only the keyframe (`samples/`)
tarballs, which excludes sweeps and cuts the download from ~86 GB to ~12 GB:

```bash
export NUSCENES_ROOT="/media/g6/My Passport1/nuscenes"   # dir that will hold samples/CAM_*
B=https://motional-nuscenes.s3.ap-northeast-1.amazonaws.com/public/v1.0
mkdir -p "$NUSCENES_ROOT" && cd "$NUSCENES_ROOT"
for n in 01 02 03; do
  curl -L "$B/v1.0-trainval${n}_keyframes.tgz" | tar -xz --wildcards 'samples/CAM_*'
done
```

Streaming through `tar` keeps only the camera JPEGs (~9 GB) and never writes a
tarball to disk. The bucket is the AWS Open Data mirror: anonymous HTTPS, no
signed URLs. Total requirement is 438 unique images across all splits.

Then verify coverage and populate the local cache:

```bash
python3 scripts/check_images.py          # must report 438/438
python3 scripts/materialize_cache.py     # copies the 438 JPEGs to data/image_cache
```

`nuscenes_root` in `configs/default.yaml` is the persistent setting; the
`NUSCENES_ROOT` env var overrides it. Once the cache is populated, day-to-day
work reads from `data/image_cache` and does not need the external drive.

## Data notes

- No training split exists. 55 labeled dev records, 59 input-only test records.
- The benchmark spans nuScenes trainval blobs 01-03. This is derived by mapping
  the 66 referenced scenes onto blob boundaries, not stated by the organizers.
  The last referenced scene (`scene-0318`) sits ~198 keyframes inside blob 03,
  so if the real split differs slightly, blob 04 may also be needed. The
  438/438 check in `check_images.py` is the authoritative gate.
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

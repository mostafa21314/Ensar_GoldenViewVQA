# GoldenViewVQA — GroundLM 2026 shared task system

Code for the GroundLM 2026 GoldenViewVQA shared task: given six synchronized
nuScenes camera views and a question, identify the supporting view and select
the multiple-choice answer.

The primary system combines a fine-tuned YOLOv8m detector, calibration-based
ground-plane projection and cross-camera association, a structured text
serialization, and a vision-language model that receives the text plus all six
camera images.

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
export NUSCENES_ROOT=/path/to/nuscenes   # directory holding samples/CAM_*
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

## Perception and prompt generation

Install the project and the perception dependency in an isolated environment:

```bash
python3 -m pip install -e ".[perception]"
```

Run the fine-tuned detector over the benchmark frames, then build the model
manifests:

```bash
export GOLDENVIEW_DETECTOR_WEIGHTS=/path/to/yolov8m-nuscenes-best.pt
python3 scripts/detect_frames.py
python3 scripts/build_samples.py --isolated
python3 scripts/build_samples_s2.py
python3 scripts/build_samples_s3_approx.py
```

Generated detections, prompts, samples, images, predictions, and checkpoints are
gitignored. They may contain licensed data, machine-specific absolute paths, or
large binary artifacts and must not be committed.

## Evaluating

Use the organizers' scripts against the development split:

```bash
python3 external/goldenview/scripts/evaluate.py \
  --gold external/goldenview/data/eval.jsonl \
  --pred predictions/dev.jsonl
```

The evaluator reports view accuracy, view macro accuracy, answer accuracy, and
joint accuracy. The shared task uses **joint accuracy as the primary metric**;
macro view accuracy remains important for diagnosing the imbalanced view labels.

## Submission

The official submission is a JSONL file with exactly one row per test question:

```json
{"question_id":"sfall_0001_causality","predicted_view":"CAM_FRONT","predicted_answer_id":"A"}
```

Validate the file before upload:

```bash
python3 external/goldenview/scripts/submission_validation.py \
  --input external/goldenview/data/test_inputs.jsonl \
  --pred predictions/test_gpt_5_6_sol_ultra_s2.jsonl
```

Upload the validated test JSONL to the official evaluator task named
`goldenviewvqa`. Register one immutable team name and use that exact name on the
evaluator, in the system-paper title/results, and in OpenReview. The evaluator
allows up to five submissions per task per account per server day; malformed
files rejected by sanity checks do not count toward that limit.

The evaluator upload does **not** include source code, images, or model
checkpoints. For the system paper, disclose the external dataset, detector
checkpoint, hosted VLM, tools, and generated prompt data used by the method.

## Checkpoints and reproducibility

Inference requires one local checkpoint:

- A YOLOv8m checkpoint fine-tuned on the seven nuScenes agent classes: car,
  truck, bus, trailer, motorcycle, bicycle, and pedestrian. Pass its path with
  `--weights` or `GOLDENVIEW_DETECTOR_WEIGHTS`.

The GPT-5.6 Sol VLM is hosted and has no local checkpoint to commit or upload.
Record its exact model name, reasoning setting, access date, prompt version, and
generated predictions in the experiment log. Do not commit either the detector
binary or licensed nuScenes images; publish checkpoint provenance and a download
location separately if redistribution rights permit it. See
[`MODEL_PROVENANCE.md`](MODEL_PROVENANCE.md) for the submitted-system details.

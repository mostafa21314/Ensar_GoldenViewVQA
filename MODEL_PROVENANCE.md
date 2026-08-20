# Model provenance

This file identifies the external models used for the submitted systems. It
intentionally does not contain model binaries or licensed nuScenes images.

Two hosted reasoning models were run over the same serialised inputs. The
**primary submitted system is Claude Opus 5**, which produced our best official
test result (joint accuracy 0.7797). GPT-5.6 Sol produced a second submitted run
(joint accuracy 0.7627) and the System 3 variant. Both are documented below.

## Perception checkpoint

- Architecture: Ultralytics YOLOv8m object detector
- Initialization: pretrained `yolov8m.pt`
- Task: 2D detection
- Classes: car, truck, bus, trailer, motorcycle, bicycle, pedestrian
- Fine-tuning data: locally prepared nuScenes v1.0-mini camera dataset
- Benchmark overlap: the v1.0-mini scenes include `scene-0061` and
  `scene-0103`, which also occur in GoldenViewVQA. This affects 2 of 114
  records (`sfall_0103_causality` in dev, `sfall_0061_intent_prediction` in
  test).
- Prepared split size: 1,938 training images and 486 validation images
- Training: 50 epochs, image size 640, batch size 16, seed 0, deterministic mode,
  cosine learning rate, first five layers frozen
- Training software: Ultralytics 8.4.34, PyTorch 2.11.0+cu130
- Inference settings: confidence 0.15, IoU 0.70
- Checkpoint filename: `best.pt`
- Checkpoint size: 52,013,266 bytes
- SHA-256: `1ac0e978ddcb3578b698088e0dcc2fe59c4fce187c4687c2069ef0561544de7b`

The fine-tuned `best.pt` checkpoint is the only local model checkpoint required
to reproduce the submitted detector output. The base `yolov8m.pt` checkpoint is
not required for inference because the fine-tuned checkpoint contains the model
weights and architecture; it is relevant only for reproducing training.

The binary is excluded from Git. If checkpoint redistribution is permitted,
publish it separately and verify the SHA-256 above after download. Otherwise,
provide the training configuration and generation code to the organizers and
state the redistribution restriction.

## Vision-language models

Neither model has a local checkpoint; both were accessed through a hosted
interface, and no provider API key was used for either.

### Primary: Claude Opus 5

- Model: Claude Opus 5 (`claude-opus-5`)
- Reasoning setting: extended thinking enabled
- Modality: structured detector text only (System 1); six labelled images plus
  structured detector text (System 2)
- Access mechanism: hosted Claude Code agent
- Access date for the submitted predictions: 2026-08-20
- Submitted runs: System 1 and System 2 on both splits
- Official test result (System 2): view 0.830508, macro 0.652174,
  answer 0.915254, joint 0.779661 — our best submission

### Secondary: GPT-5.6 Sol

- Model: GPT-5.6 Sol (`gpt-5.6-sol`)
- Agent reasoning setting: `ultra`
- Modality: six labelled images plus structured detector text
- Access mechanism: hosted Codex/ChatGPT agent
- Access date for the submitted predictions: 2026-08-20
- Submitted runs: System 1, System 2, System 2 v2, and the System 3
  approximation
- Official test result (System 2): view 0.779661, macro 0.561594,
  answer 0.932203, joint 0.762712

### Reproducibility limitations

Neither hosted interface exposed an immutable model snapshot identifier, a
sampling seed, token log probabilities, or a downloadable checkpoint. Exact
outputs are therefore not guaranteed to be reproducible, and a hosted model may
be updated or withdrawn.

Preserve the generated prompt manifests and prediction JSONL files as experiment
artifacts, but do not commit them: they contain local absolute image paths.

## Data and generated artifacts

- Benchmark annotations: GoldenViewVQA, revision pinned in `DATASET_COMMIT`
- Images: nuScenes, obtained separately under the nuScenes terms of use
- Generated detector output: `data/detections.json` (gitignored)
- Generated System 2 manifests: `data/prompts_*_s2.jsonl` (gitignored)
- Generated predictions: `predictions/*.jsonl` (gitignored)

The official evaluator submission contains only `question_id`, `predicted_view`,
and `predicted_answer_id`; it does not contain images, prompts, or checkpoints.

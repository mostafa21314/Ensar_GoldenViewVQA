# Model provenance

This file identifies the external models used for the primary submitted system.
It intentionally does not contain model binaries or licensed nuScenes images.

## Perception checkpoint

- Architecture: Ultralytics YOLOv8m object detector
- Initialization: pretrained `yolov8m.pt`
- Task: 2D detection
- Classes: car, truck, bus, trailer, motorcycle, bicycle, pedestrian
- Fine-tuning data: locally prepared nuScenes v1.0-mini camera dataset
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

## Vision-language model

- Model: GPT-5.6 Sol (`gpt-5.6-sol`)
- Agent reasoning setting: `ultra`
- Modality: six labelled images plus structured detector text
- Access date for the submitted predictions: 2026-08-20
- Access mechanism: hosted Codex/ChatGPT agent; no OpenAI API key was used
- Local checkpoint: none

The hosted agent interface did not expose an immutable model snapshot identifier,
sampling seed, token log probabilities, or downloadable checkpoint. This is a
reproducibility limitation and should be disclosed in the system paper. Preserve
the generated prompt manifests and prediction JSONL files as experiment artifacts,
but do not commit them when they contain local absolute image paths.

## Data and generated artifacts

- Benchmark annotations: GoldenViewVQA, revision pinned in `DATASET_COMMIT`
- Images: nuScenes, obtained separately under the nuScenes terms of use
- Generated detector output: `data/detections.json` (gitignored)
- Generated System 2 manifests: `data/prompts_*_s2.jsonl` (gitignored)
- Generated predictions: `predictions/*.jsonl` (gitignored)

The official evaluator submission contains only `question_id`, `predicted_view`,
and `predicted_answer_id`; it does not contain images, prompts, or checkpoints.

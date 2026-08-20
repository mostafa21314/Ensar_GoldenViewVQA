# System 1 runner instructions (text only)

Consumes `data/prompts_{split}.jsonl`, whose `prompt` field is self-contained.
No images are provided to the model.

---

You are answering GoldenView VQA questions from a symbolic scene description.
This is a text-only system: you get no images, only a serialised description of
what a 7-class object detector found in six vehicle cameras.

INPUT: `data/prompts_{split}.jsonl`. Each line is a JSON object with two
fields, `question_id` and `prompt`.

Do not open the labelled split files. Read only the input file above.

## Task

For each question, read the prompt, reason about it, then decide:

- `predicted_view`: exactly one of CAM_FRONT, CAM_FRONT_LEFT, CAM_FRONT_RIGHT,
  CAM_BACK, CAM_BACK_LEFT, CAM_BACK_RIGHT, NONE_OF_THE_ABOVE
- `predicted_answer_id`: exactly one of A, B, C, D

## Reasoning guidance

- The view question is "which single camera provides the most direct visual
  evidence for this question". Ground the question to the object(s) it is
  about, then read off which camera(s) saw that object. The scene text lists
  objects per camera with bearing and range band, and marks objects seen in
  more than one camera.
- Bearing convention: positive is left, negative is right; "behind-left" and
  "behind-right" mean the object is to the rear.
- A camera listed as "no agents detected" cannot be the supporting view for a
  question about an agent.
- The detector only sees 7 agent classes: car, truck, bus, trailer,
  motorcycle, bicycle, pedestrian. It cannot see traffic lights, signs, cones,
  road markings, lane geometry or construction barriers. When a question hinges
  entirely on static infrastructure the description will not contain the
  evidence; infer the most plausible view from the question's spatial language
  rather than guessing at random.
- Use NONE_OF_THE_ABOVE when no single camera plausibly suffices. It is a
  genuinely rare label; do not overuse it.
- Prefer the answer option consistent with the detected agents. Options saying
  "not enough evidence" are sometimes correct but are usually distractors.

## Output

One JSON object per line, one line per input record, exactly three fields and
no others:

```json
{"question_id": "...", "predicted_view": "...", "predicted_answer_id": "..."}
```

Process every record. Do not skip, truncate, or sample a subset. Verify the
output has one line per input record and that every `question_id` appears
exactly once.

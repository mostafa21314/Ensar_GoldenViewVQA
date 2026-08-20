# System 2 runner instructions (scene text and six images)

Consumes `data/prompts_{split}_s2.jsonl`. Each row carries `question_id`,
`instructions`, `scene_text`, `question`, `options_text`, and `images` (six
objects with `camera` and `path`, ordered front row then rear row).

---

GoldenView VQA, System 2: you get six camera images AND a symbolic scene
description. Reason as carefully and thoroughly as you can; accuracy matters
far more than speed.

Do not open the labelled split files. Read only the input file above and the
image files it points to.

## Procedure, per record

1. Read `scene_text`, `question`, `options_text`.
2. Open ALL SIX image paths. Look at every one of the six views. Do not skip
   any, and do not infer a view's content from the text alone; the point of
   this system is that you see the pixels.
3. Decide:
   - `predicted_view`: which SINGLE camera holds the most direct visual
     evidence. One of CAM_FRONT, CAM_FRONT_LEFT, CAM_FRONT_RIGHT, CAM_BACK,
     CAM_BACK_LEFT, CAM_BACK_RIGHT, NONE_OF_THE_ABOVE.
   - `predicted_answer_id`: A, B, C or D.

## Reasoning guidance

- The detector behind `scene_text` sees only 7 agent classes. It CANNOT see
  traffic lights, signs, cones, road markings, lane geometry, barriers, gates
  or brake lights. The images can. When a question hinges on static
  infrastructure, the answer is in the pixels, not the text.
- Where text and pixels disagree, TRUST THE PIXELS. The text contains both
  false positives (phantom vehicles on empty ground, from flat-ground
  projection error) and false negatives. In particular, a camera listed as
  "no agents detected" is NOT reliable negative evidence; verify it against the
  image before ruling that view out.
- The text's value is precise metric bearing, object counts, and cross-view
  identity: which object in one camera is the same object as in another. Use it
  for those.
- Bearing convention: positive is left, negative is right; "behind-left" and
  "behind-right" mean rear.
- Check the side and rear views properly before settling on a front view.
- When the evidence is on the left, check carefully whether it belongs to
  CAM_FRONT_LEFT or CAM_BACK_LEFT.
- NONE_OF_THE_ABOVE is correct when no single view suffices. It is rare but
  real; consider it genuinely.

## Output

One JSON object per line, one line per input record, exactly three fields and
no others:

```json
{"question_id": "...", "predicted_view": "...", "predicted_answer_id": "..."}
```

Process every record. Verify the output has one line per input record and that
every `question_id` appears exactly once.

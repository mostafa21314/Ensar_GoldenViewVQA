# Prompts

Prompting happens in two layers. Both are needed to reproduce a run.

**Layer 1 — per-record prompt (generated).** Built by
`scripts/build_samples.py` (System 1) and `scripts/build_samples_s2.py`
(System 2) from the serialised scene and the record's question and options. The
instruction preamble lives in the `INSTRUCTIONS` constant of each script, and
the fully assembled text is written to `data/prompts_{split}.jsonl` (System 1,
self-contained in the `prompt` field) and `data/prompts_{split}_s2.jsonl`
(System 2, which additionally carries the six image paths).

**Layer 2 — runner instructions (this directory).** The task given to the model
that consumes layer 1: how to work through records, how to weigh text against
pixels, and the required output format. These are the files here.

| File | System |
|---|---|
| `system1_text_only.md` | System 1, no images |
| `system2_text_and_images.md` | System 2, scene text plus six images |

## A note on what these files contain

The System 2 runner instructions used during our first development run also
contained two sentences quoting System 1's per-class error counts on the
development split. Those were development-label-derived and should not have
been there, since System 2 is scored on that same split. They are **not**
present in the file published here.

The reported System 2 results were reproduced with the prompt as published,
without those sentences, so the numbers in the paper correspond to this text.
The guidance that remains describes properties of our own perception pipeline
(the detector's seven-class vocabulary, that it emits false positives from
flat-ground projection, and that an empty camera is not reliable negative
evidence). Those are facts about our code, knowable without looking at any
label.

## Reproducing

```bash
python3 scripts/detect_frames.py          # needs a GPU + the detector weights
python3 scripts/build_samples.py          # System 1 inputs
python3 scripts/build_samples_s2.py       # System 2 inputs
```

Then run the model of your choice against `data/prompts_*.jsonl` using the
matching runner instructions, and merge with `scripts/merge_shards.py` if you
shard the work. Model and decoding settings used for the submitted runs are
reported in the paper.

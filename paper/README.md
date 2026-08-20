# System description paper

GroundLM 2026 shared task, GoldenViewVQA. Official ACL two-column style.

## Files

| File | Origin |
|---|---|
| `main.tex` | ours, the paper |
| `refs.bib` | ours, bibliography |
| `acl.sty` | upstream, **unmodified** |
| `acl_natbib.bst` | upstream, **unmodified** |

Style files come from [acl-org/acl-style-files](https://github.com/acl-org/acl-style-files).
Do not edit them, and do not override margins, spacing, fonts or page
dimensions from `main.tex` — the organizers check for this.

## Building

No LaTeX toolchain is installed on this machine. Either:

**Overleaf (no install).** New Project, Upload Project, add these four files,
set `main.tex` as the main document. Compiler pdfLaTeX.

**Locally.** Install a toolchain first, then:

```bash
pdflatex main && bibtex main && pdflatex main && pdflatex main
```

Two `pdflatex` passes after `bibtex` are needed for citations to resolve.

## Before submitting

- Set `\teamname` in `main.tex`. It must be byte-identical to the evaluator
  Space registration and the OpenReview `teamname` field, and it is immutable
  once registered.
- 4-8 pages of main content. `Limitations` and `Ethics Statement` are
  unnumbered and excluded from that count; references may run over.
- Author names, affiliations and contact information are required.
- Disclose every external dataset, pretrained model, tool, API, and any
  generated or synthetic data.
- Report the official test numbers from the evaluator, not locally computed
  ones.
- Open the final PDF and check tables, figures and links render.

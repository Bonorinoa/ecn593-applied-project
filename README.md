# ECN 593 applied project

Not-ruled-out images of a named policy contrast, in a village agent-based model calibrated by history matching.

This repository is the study packet. It is not a lab notebook. Lecture drafts, amendment memos, and agent files are not here.

## Read in this order

1. `writeup/main.pdf` — the formal write-up. Draft for review, 24 September 2026.
2. `src/poc_abm/config.py` — every frozen constant. If a number is not here, it is not a parameter of the run.
3. `tests/test_kernel_hand_examples.py` — one module's arithmetic, stated in the docstring. The other tests in `tests/` are the same kind of check.
4. `results/poc_results.json` — the planted run the PDF cites. `results/poc_results_wb_F-EMPTY.json` is the external-anchor attempt that ruled out the whole box. `results/appendix_cut_0.50.json` is the declared exposure-cut recomputation.

`SPECIFICATION.md` is the freeze the write-up defers to. If the PDF and that file disagree, the specification wins and the sentence is a bug. If either disagrees with the JSON, the JSON is what ran.

## What this packet does not claim

The OLS intervals are not a failed estimate of the headline policy contrast. They answer a different question. The not-ruled-out image is not a posterior and not a Manski identified set. Empty NROY against the World Bank anchors is a finding about that pair. The threshold was not loosened.

The exposure cut at 0.50 has been run. The E2 sticker does not flip. The low-exposure cell merges in every sampled world, so the no-flip result is about the merged functional, not about unchanged strata. See the write-up section "Declared cut at 0.5". The headline image endpoints still do not carry per-survivor Monte Carlo bars.

## Reproduce the checks

```bash
uv venv .venv --python 3.11
source .venv/bin/activate
uv pip install -r requirements.txt -r requirements-dev.txt
pytest tests/ -q
```

The tests put `src/` on the path themselves. Re-running the full waves is `python -m poc_abm.pipeline` with `PYTHONPATH=src`. That re-draws noise. The committed JSON is the run the PDF cites; do not overwrite it to "refresh" a number.

Compile the write-up from `writeup/` with `xelatex main.tex`.

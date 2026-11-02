# E4 (engineer, Codex gpt-5.6-sol): A2.1, the descriptive variance split

Read `docs/cards/common_rules.md` (below), amendment A2 and its addendum **A2.1** at the bottom of
`docs/preregistration-v2.md`, and `reviews/a2-code.md` item 3b (V3's probe, under
`reviews/probes/V3/`). A2.1 is the spec.

**Acceptance:**
1. `scripts/a2_variance_split.py` implements A2.1: at each point, for A1, A2 and Foil 2's
   delta_spill, the one-panel split of the reported variance (positive-joint-probability term,
   Young-bound term, Young share) and the fixed-noise design redraw (R_design = 400; noise at
   `FOIL_PANEL_OFFSET`; assignments on stream offsets 3,000,000 + r, reusing the pattern of
   `scripts/check_foil2_coverage.py::_design_panel`). Put R_design and the offset base in
   `config/design.toml` `[interference]`. Reuse the estimand functions; if the split needs the
   covariance in two parts, add an optional return of the parts to the existing function with the
   default behaviour unchanged (prove with a test that existing outputs are identical).
2. **Built-in check:** at c_star, A1's design-redraw numbers must agree with V3's probe
   (`reviews/probes/V3/`) up to Monte Carlo noise from the different seeds; report both side by side.
   Do not match seeds to V3's.
3. Output `results/interference/variance_split.json` (with `git_commit`, `ran_at`); progress lines.
4. `scripts/replicate.py` runs it after `interference_tradeoff.py` (skipped with `--quick`); add it
   to `RESULT_FILES`. `scripts/write_numbers.py` emits macros for every cell, and **must** include
   exactly these names, which the paper already uses: `\YoungShareAOneStar`,
   `\YoungShareATwoStar`, `\YoungShareSpillStar`, `\DesignRedrawsAOneStar`,
   `\DesignMainTermRatioAOneStar`, `\DesignFullRatioAOneStar` (same scheme for the other points and
   analysts). Both `writeup/numbers.tex` and `thesis/numbers.tex` regenerate.
5. Tests (new files): the split sums to the reported variance exactly; the optional-parts return
   leaves existing outputs identical; a tiny-design smoke test. Full suite passes.
6. Locks: every existing result file unchanged apart from stamps; rerun once for determinism.
7. Docs: one paragraph each in `README.md` and `SPECIFICATION.md` ("Addendum A2.1"), Simple English.
   Do not touch `thesis/` except the generated `numbers.tex`, nor `writeup/` except `numbers.tex`.

**Artifact:** commits; the split table at all three points; the side-by-side with V3's probe; tests;
determinism. Do **not** run the full `replicate.py` (the PM runs it at integration). Progress file:
`docs/cards/progress/E4.md`.

**Fence:** paths above only. Never change an A2 estimator, interval or result.

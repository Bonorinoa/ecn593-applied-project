# E2 (engineer): the delta sensitivity menu (pre-registration amendment A1)

**Acceptance:**
1. `scripts/delta_menu.py` implements amendment A1 of `docs/preregistration-v2.md` exactly. Reuse
   the pipeline's own functions (`run_waves`, `sample_nroy_index`, `evaluate_thetas`,
   `evaluate_spill`, `interval_image`, the `nroy_param_spread` code and `classify_interval`). Pass
   delta per entry through a parameter, never by editing `config/design.toml`. If a function reads
   `config.DELTA` directly, add an optional `delta` argument whose default keeps the current
   behavior, and leave every existing call unchanged.
2. **Built-in check:** the delta_level = 0.02 entry reproduces `results/planted/poc_results.json`'s
   Theta_hm, Theta_exp, n_nroy, wave_kept and nroy_param_spread exactly. The script asserts this and
   exits non-zero on a mismatch.
3. **Output:** `results/sensitivity/delta_menu.json`. For each entry: delta vector, tau, `finding_hm`,
   `wave_kept`, `n_nroy`, both images, spread ratios, the alpha–kappa correlation, and the c*
   Foil 1 / Foil 2 intervals' classification against that entry's images (read the c* intervals from
   `results/planted/poc_results.json`; do not recompute the foils). Print progress lines like
   the pipeline's.
4. `scripts/replicate.py` runs it as its own step after the Foil 2 check and before the figures. It
   is skipped with `--quick`, like the Foil 2 check. Add the file to `RESULT_FILES`, and renumber the
   steps and the docstring.
5. `scripts/write_numbers.py` emits macros for the menu: per entry `n_nroy`, both image endpoints,
   the spread ratios for alpha, kappa and gamma, and the c* classifications. Use names like
   `\MenuDeltaHalfThetaHmLo`; choose a clear, documented scheme. Existing macros are unchanged.
6. **Tests:**
   - a test that the delta argument defaults reproduce the old behavior;
   - a fast test of the menu logic on a tiny design (few points; does not need the real run).

   The full suite passes.
7. Run the menu in background mode (it takes about 3 x 4 min), commit the code, the JSON,
   `numbers.tex` and the docs. Update `README.md` (replication steps and runtimes) and
   `SPECIFICATION.md` (a short section "Amendment A1: the delta menu"), in Simple English. Do not
   edit `writeup/main.tex`, `writeup/cover.tex` or the pre-registration.
8. **Determinism:** rerun `scripts/delta_menu.py` once after the commit. `git diff results/sensitivity`
   must be empty except for run stamps, if any.

**Artifact:**
- the commits;
- the handoff with the menu table (all entries: n_nroy, wave_kept, finding, both images, spread
  ratios for alpha, kappa and gamma, and the c* classifications), the test count, the runtimes and
  the determinism evidence.

The progress file is `docs/cards/progress/E2.md`.

**Fence:**
- Write only inside the repo. Do not touch the paper, the pre-registration or the spine.
- Never change the main design (delta in `design.toml`, tau, C, the moments, the seeds) and never pick
  a delta from the menu.

**Note:** a read-only reviewer card (G1, Grok) is reading the repo at the same time. Commit only
your own files, by explicit path.

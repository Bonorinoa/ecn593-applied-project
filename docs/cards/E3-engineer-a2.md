# E3 (engineer, Codex gpt-5.6-sol): amendment A2, the price of allowing interference

Read `docs/cards/common_rules.md` (appended below) and amendment A2 at the bottom of
`docs/preregistration-v2.md` first. A2 is the spec. This card implements it, runs it and commits.

**Acceptance:**
1. **A general Hajek linear contrast.** In `src/poc_abm/estimand.py`, add a function that takes a
   random-arm panel (Y, D), a list of cells (each = an exposure stratum, optionally restricted to a
   fixed node set) and a coefficient per cell, and returns the estimate sum_k a_k mu_k and its
   linearized Aronow-Samii SE: Var = sum_k sum_l a_k a_l Cov(mu_k, mu_l), using the existing
   `ht_cov`, exact first-order probabilities (`_exposure_probs_cached`) and the cached simulated
   joint probabilities (`_exposure_mc_cached`), with each cell's probabilities zeroed outside its
   node set. Same per-panel merge rule as `hajek_contrasts`. Do not change `hajek_contrasts`.
   **Built-in identity test:** with cells (S0c, S0a) and coefficients (+1, -1) the new function
   returns exactly `hajek_contrasts`' `delta_spill` and `se_spill` on the same panel.
2. **The three analysts** of A2 at one point and one panel: A0 = the existing Foil 1 interval
   (reuse, do not reimplement); A1 and A2 as A2 defines them, with w from the strata of the degree
   vector `assign(world, "degree", ...)` (deterministic). A2's bins: H = the 80 people the degree
   arm seeds, L = the rest. An empty needed cell makes A2 undefined for that panel (NaN interval,
   counted), never imputed.
3. **`scripts/interference_tradeoff.py`:** at `min_I`, `median_I`, `c_star` (read the points and
   theta2 truths from `results/planted/poc_results.json`; do not rerun the waves):
   - one panel at `FOIL_PANEL_OFFSET`: each analyst's interval, `covers_truth`,
     `covers_planted_truth`, `classify_interval` vs Theta_hm;
   - R = 200 panels on offsets 2,000,000 + r: per analyst mean, bias, SD, RMSE, mean SE, SE/SD,
     coverage with an exact Clopper-Pearson 95% interval, mean width, width / width(Theta_hm), and
     the undefined count. Put R and the offset base in `config/design.toml` under a new
     `[interference]` section (exogenous, as A2 fixes them) and load them in `config.py`.
   - write `results/interference/tradeoff.json` (with `git_commit` and `ran_at` like the other
     results); print progress lines like the pipeline's.
4. **Figure:** `figures/planted/tradeoff.png` drawn from the saved JSON through one function in
   `src/poc_abm/figures.py` (A2's readout: |bias| against mean width, a marker per analyst per
   point, Theta_hm's width as a reference line, coverage beside each marker). Add it to
   `scripts/draw_figures.py`. Shared axes; legible at 6.5 in width.
5. **Wiring:** `scripts/replicate.py` runs it as its own step after the delta menu and before the
   figures; skipped with `--quick`; add the JSON to `RESULT_FILES`. `scripts/write_numbers.py`
   emits macros for every A2 table cell (choose a documented scheme, for example
   `\TradeoffStarAOneBias`); existing macros are unchanged.
6. **The thesis folder:** a new Overleaf project `thesis/` is being built by other cards. Make
   `scripts/write_numbers.py` also write a byte-identical `thesis/numbers.tex`, and
   `scripts/sync_writeup_figures.py` also copy every figure the writeup uses plus `tradeoff.png`
   into `thesis/figures/` (create the folders if missing). These generated files are yours to
   commit; nothing else under `thesis/` is.
7. **Tests** (new files only; the full suite passes): the identity test of item 1; a hand example of
   A1 on a tiny graph where the exposure map holds exactly (outcomes y = b + e_s by stratum), so A1
   equals the exact policy contrast; A2's undefined rule on a panel with an empty cell; and a fast
   smoke test of the script logic on a tiny design.
8. **Locks:** `results/planted/poc_results.json`, `results/checks/foil2_coverage.json` and
   `results/sensitivity/delta_menu.json` must not change (except run stamps). Rerun
   `scripts/interference_tradeoff.py` once after the commit: `git diff results/interference` must
   be empty apart from stamps.
9. **Docs:** `README.md` (replication steps, runtimes, a short "Amendment A2" paragraph) and
   `SPECIFICATION.md` (a section "Amendment A2: three analysts for theta2"), in Simple English. Do
   not edit `writeup/main.tex`, `writeup/cover.tex`, the pre-registration or anything under
   `thesis/` except item 6's generated files.
10. Then run the full `scripts/replicate.py` once in background mode and report its verdict line
    and runtime.

**Artifact:** the commits; a handoff with the A2 table at all three points (every readout), the
check of A2's five written expectations (a)–(e), one line each, "met" / "not met" with the
numbers' source key, the test count, runtimes, the determinism evidence and the replicate verdict.
Progress file: `docs/cards/progress/E3.md`.

**Fence:** write only the paths named above. Never change the main design, A1, the bins, the cut,
R, the offsets or the confidence level after seeing an A2 number. If an A2 number looks wrong,
report it; do not tune.

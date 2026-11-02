PASS-WITH-WORDING

Independent check of amendment A2 as committed at `df41c240dc16e9600c1ce7d1b26d440ed744c379`. Producer route, from the engineer agent log for session `local-b42f7cfa19ebf1ddbce2158221faaa4fedec2888ef78120f6c433c13345857ce`: 110 API calls, all `model=gpt-5.6-sol provider=openai-codex`. This review: `model=grok-4.7 provider=xai-oauth` (verifier log, session `local-c1314e46530ca1c4195e1bea1fb82fc7eab87f4aeafcce1abf81d024512116ef`).

The code implements A2. The one-panel point estimates match. The inflated A1/A2 standard errors are the Young bound in the specified Aronow–Samii covariance, not a sign, double-count, missing-cross-term, or normalization bug. Do not retune the variance after this finding. The paper must not read coverage 1 as calibration. Required wording is in item 7; W3 carries that block verbatim.

## 1. Implementation against A2

Stated-vs-implemented, from `docs/preregistration-v2.md` lines 156–183 and the code. No design choice moved after an A2 number: `git diff --stat 1f8a8c5 8ed5eb0 -- src scripts config tests` is empty, and `config/design.toml` lines 44–47 are the same at `1f8a8c5` and at HEAD (`repetitions = 200`, `offset_base = 2_000_000`).

| A2 rule | Where | Result |
|---|---|---|
| A0 reuses Foil 1, degree-arm panel, `(k/N)` times OLS-HC1 | `scripts/interference_tradeoff.py:98-113` | Matches. Own OLS point at `c*` equals the JSON. |
| A1: `sum_{s ≠ S0a} w_s (μ_s − μ_S0a)`, `w_s = n_s(d2)/N`, merge follows the panel | `scripts/interference_tradeoff.py:44-63` | Matches. At the `c*` panel the degree shares are S1 0.1, S0a 0.24875, S0b 0.385, S0c 0.26625, and the panel is not merged (`reviews/probes/V3/probe_a2.log`). |
| A2: H = the 80 people `d2` seeds, L = the rest; no merge across bins; `(80/N)(μ_{S1,H} − μ_{S0a,H})` plus the L terms | `scripts/interference_tradeoff.py:66-95`; degree arm ignores the RNG at `src/poc_abm/kernel.py:85-89` | Matches. `high_n = 80`. S1 on L has weight 0, so that cell is omitted, as a zero term. |
| Empty needed cell → undefined, never imputed | `src/poc_abm/estimand.py:368-374`; test `tests/test_interference_tradeoff.py:68-76` | Matches. The suite's empty-cell test passed. On the committed run every repeated cell has `undefined_count` 0. |
| Variance = linearized `ht_cov` summed with the coefficients; node mask zeros probability outside the bin | `src/poc_abm/estimand.py:376-400` | Matches the written generalization. See item 3. |
| One panel at `FOIL_PANEL_OFFSET`; R = 200 at offsets `2_000_000 + r` | `config/design.toml:44-47`; `scripts/interference_tradeoff.py:186-191`; JSON `repetitions`, `offset_base`, `foil_panel_offset` | Match. The block does not meet the foil panel (0), the image reps (0–199), the recheck (100000), or the Foil 2 gate (1000000). |
| Clopper–Pearson 95% | `scripts/interference_tradeoff.py:117-123` | Exact. All 9 repeated cells match a fresh beta quantile (`probe_a2.log`, `cp ... match=True`). |
| Truth is `theta2(c)` from `evaluate_thetas`; both containment flags; `classify_interval` | `scripts/interference_tradeoff.py:158-168, 185` | Flags match the intervals at all three points (`probe_a2_split.log`). |

Non-blocking. `hajek_linear_contrast` also returns undefined when `n_hat <= 0` or the mean is not finite (`estimand.py:369-370`). That is a superset of the empty-cell rule, not a different rule.

## 2. Point estimates at `c*`, own code

Own Hájek means and the A2 linear combination, from `simulate_panel`, the stratum map, and `exposure_probs`. Not from `analyst_a1` / `analyst_a2`.

Command: `env -u PYTHONPATH .venv/bin/python -u reviews/probes/V3/probe_a2.py` (log `reviews/probes/V3/probe_a2.log`). Exit 0.

- Dynamics copy equals `simulate_panel` on the paired streams (`dynamics_copy_matches_simulate_panel True`, `random_panel_copy_matches True`).
- A1 estimate equals `results/interference/tradeoff.json` `points.c_star.one_panel.A1.estimate` exactly (`A1_absdiff 0.0`).
- A2 shipped estimate equals that JSON exactly (`probe_a2_split.log`: `A2_shipped_equals_json True`). Own sum differs by `1.39e-17`, one rounding ulp from summation order (`A2_own_minus_shipped`). That is floating precision, not a different estimator.
- A0 own OLS share equals the JSON exactly.

## 3. Variance

The general contrast is the right generalization of the existing linearization, in the sense A2 wrote: `Var = Σ_k Σ_l a_k a_l Cov(μ_k, μ_l)` with the existing `ht_cov`. It is not a sharp standard error.

Pins, from the same probe:

- Identity: cells (S0c, S0a), coefficients (+1, −1), estimate and SE equal `hajek_contrasts` exactly (`identity_estimate True`, `identity_se True`; test `tests/test_interference_tradeoff.py:36-48`).
- The identity test does pin the cross term. Dropping it moves the spill SE from 0.004858 to 0.004400 (`cross_changes_se True`). It does not pin node masks or a contrast with more than two cells. Those were checked separately: an own quadratic form matches the shipped A1 SE and the shipped A2 SE exactly (`A1_repro_se_absdiff 0.0`, `A2 se_repro_absdiff 0.0`).
- Scaling: `0.1 * (μ_S1 − μ_S0a)` has SE equal to `0.1 * se_dir` within `1e-19` (`scale_se_absdiff`). Not a normalization bug.
- Node crop is active. On the H bin, S1,H with S0a,H has 232 joint zeros, not the structural zeros of the other 720 people (`probe_a2_split.log`). Cropping those structural zeros before Young (`estimand.py:383-388`) is the right domain. Leaving them in would treat "not in this fixed bin" as a design impossibility.

Young share of the spill contrast, the case Foil 2 already calibrated, is 0.127. Young share of A1 on the `c*` panel is 0.886. Young share of A2 on that panel is 0.828. The extra width is the bound, and it is much larger here because A1/A2 include S0b. Foil 2's spill contrast does not.

Same-sign pairs (S1 with S0b, S0b with S0c) get a Young term that reduces the variance estimate. That direction is not a guaranteed upper bound for a general contrast. On this contrast the opposite-sign terms are larger, so the net is still conservative. See 3b. That is a property of this coefficient vector, not a reason to change the signs after seeing the result.

## 3b. PM focus: conservative bound, not a covariance bug

Question: repeated-sample SE/SD is about 1.0 for A0 and about 2.3–3.1 for A1 and A2, with coverage 1.0. Is that (i) the Young bound, or (ii) a bug in the general covariance?

Answer: (i). Evidence:

1. Own quadratic form equals the shipped SE exactly (item 3). A sign error, a double count, or a missing cross term in the combination would have shown up as a difference.
2. Fixed-noise design redraw of A1 at `c*`, noise offset 0, R = 400, assignment seeds `20261101 + r`. Own estimates match the shipped estimates within `9e-17`. Design SD = 0.002311. Mean reported SE = 0.006010. Mean(SE²) / design variance = 6.78. Mean(main-term SE²) / design variance = 0.685 (`probe_a2.log`, `DESIGN`).
3. So the π>0 linearization is slightly small (about 0.83 times the design SD). The Young terms take the reported SE to about 2.6 times the design SD. That is the same inflation as the committed SE/SD, not a second bug in the repeated-sample SD.
4. On the `c*` panel the Young mass is not mainly "a treated person and an S0a neighbour", though that pair is real (S1:S0a scaled Young `3.66e-6`, 7,268 zeros). The bulk is S0b, the largest degree-policy share (0.385). S0b:S0a scaled Young is `2.99e-5` with 50,338 zeros; S0b:S0b is `1.64e-5` with 95,356 zeros (`probe_a2_split.log`). A2's largest term is the same pair inside L.

What this means for the tradeoff. The rise in SD from A0 to A1 is a real rise in sampling dispersion (A1 design SD 0.002311 against A0's repeated-sample SD near its SE, and A0's SE/SD is about 1). The further rise in mean width, and the coverage of 1, are the bound. Mean width is not the sampling dispersion. Coverage 1 is conservative repeated-sample containment, not a calibrated 95% interval.

Do not "fix" this by dropping the Young term or rescaling the SE. The main term alone would sit below the design variance. A sharper variance would be a new design, written before the rerun, not a correction of this one.

Not re-run: a design redraw at min-I, median-I, or for A2. A2's one-panel Young share (0.828) and its SE/SD (about 2.3–2.6 at all three points) are the same pattern.

## 4. Truth, units, sign

`theta2_true` in the tradeoff file is the findings field, which is `evaluate_thetas` (`src/poc_abm/pipeline.py:200`, `src/poc_abm/estimand.py:17-21, 59-62`): mean outcome under the degree arm minus mean outcome under control. At `c*` that field equals `theta_star.theta2`. A one-rep degree-minus-control contrast is positive and the same order (`probe_a2.log`). That rep is a sign check, not a replacement for the locked Monte Carlo truth.

Like for like, as a comparison of intervals aimed at that same theta2: yes, in units and in sign.

- A0 is `(k/N)` times the OLS coefficient (`src/poc_abm/diagnostic.py:91-109`). After the share scaling it is a per-person policy contrast, the same unit as theta2. It equals theta2 only under SUTVA, which this kernel does not have.
- A1 and A2 are per-person averages of exposure contrasts. The S0a share drops out because those people contribute a zero contrast. Same unit, same sign (seeding against no campaign).
- Bias is mean estimate minus that theta2. Negative at every point for every analyst. The comparison is not flipped.

Not like for like as three identified estimators of one functional. Say that. Do not say A0 estimates the same object as A1.

## 5. Locks, determinism, tests

Locks. Stamp-free SHA-256 of the JSON (keys `ran_at` and `git_commit` removed) matches `0db57c7` for all three:

- `results/planted/poc_results.json` `a81173437fd0`
- `results/checks/foil2_coverage.json` `2b864e32b9c5`
- `results/sensitivity/delta_menu.json` `e176fc647dee`

`git diff HEAD` on those files was empty at review time. Foil 2 was not in the dirty set.

Tests. `env -u PYTHONPATH .venv/bin/python -m pytest tests -q -p no:warnings` from the repo root. `72 passed in 7.84s`. Exit 0.

Determinism. The one panel is a pure function of `stream_seed`: two calls match exactly (`one_panel_repeat_identical True`). The exposure Monte Carlo seed is the fixed `exposure_mc_seed`. I did not regenerate the R = 200 file. That script writes `results/interference/tradeoff.json`, which is outside this fence, and E3's full `replicate.py` claim was not re-run here.

## 6. Expectations (a)–(e)

E3's met / not-met reading is right, including the tie on (c). Checked from `results/interference/tradeoff.json` in `probe_a2.log`, not from the handoff table.

- (a) met at all three points. Absolute bias falls strictly A0 > A1 > A2.
- (b) met at all three points. SD rises strictly, and mean width rises strictly, A0 < A1 < A2. These are different facts. SD is sampling dispersion. Width is the conservative interval. Do not collapse them.
- (c) met only as a tie. A0 coverage is 0, which is far below 0.95. A1 and A2 are both 1, so both are closest, and both sit 0.05 above nominal. "A2 is the closest" is true only if the tie is stated. It is not "A2 is calibrated".
- (d) met at all three points. A1 and A2 bias are negative. The amendment's reason (two-hop spillover lifts the S0a control) was not re-derived here. The sign was.
- (e) met at all three points. Every `width_over_theta_hm` is below 1.

E3's one-panel table matches the JSON, including median-I A1/A2 containing the point truth and not the planted truth.

## 7. Wording

W3 (`t_988fb05b`) carries the following block verbatim and does not soften it.

### Must not say

- A1 or A2 is unbiased for theta2, or that transport removes the bias.
- The pilot identifies theta2, or A1/A2 is an identified estimator of theta2. Theta_hm is not an identified set.
- A0, A1, and A2 estimate the same functional. They are three intervals aimed at theta2 under different assumptions. A0 equals theta2 only under SUTVA.
- The one-panel `covers_truth` or `covers_planted_truth` flag is coverage. Those are containment on one draw.
- A1 or A2 attains, achieves, or is calibrated to nominal 95% coverage. The repeated-sampling rate is 1 at every point, tied between A1 and A2. The reported SE is about 2.3 to 3.1 times the sampling SD. That is conservative repeated-sample containment under the Young bound, not calibration.
- A2 is uniquely the closest to nominal. It is tied with A1.
- The reported SE is the standard deviation of the sampling distribution, or that mean interval width is the sampling dispersion. The sampling dispersion is the reported SD. Mean width is the conservative interval.
- F-OVERCONF means the interval misses the truth. On the one panel every analyst is F-OVERCONF at all three points, including A1 and A2, whose intervals contain theta2.
- "No pilot ever realizes the policy", or "positivity fails". The degree vector has probability 1/C(800, 80), positive and negligible (erratum at `2824976`).
- Foil 2 is an interval for theta2, or a comparison of Foil 2 with Theta_hm.

### May say

- A0 assumes SUTVA. A1 assumes an exposure map and transport from the random pilot, with weights taken from the degree vector. A2 adds fixed bins H and L and does not borrow a control mean across those bins. All three are scored against theta2(c).
- Absolute bias falls from A0 to A1 to A2 at every point, and the sampling SD rises from A0 to A1 to A2 at every point.
- The A1 and A2 intervals are conservative relative to their sampling distributions. On the c-star panel, about nine tenths of A1's reported variance, and about five sixths of A2's, is the Young bound on pairs with a zero simulated joint exposure probability. The largest piece is the S0b–S0a pair, not the S1–S0a pair. The π>0 term alone is slightly smaller than the design variance of the A1 estimate (fixed noise, 400 assignment redraws, mean main-term SE² over design variance 0.685; full mean SE² over design variance 6.78).
- Expectation (c) is met as a tie at coverage 1. Report the tie and the SE/SD. Do not paraphrase it as calibration.
- A1 and A2 are biased downward at every point. The amendment's proposed reason is two-hop spillover in the S0a control; this review checked the sign only.
- Every repeated-sample mean width is narrower than Theta_hm. That is interval geometry. It is not evidence that the interval is honest, and it is not a coverage claim.
- The figure's percentage labels (`src/poc_abm/figures.py:203`) are the repeated-sampling rates A2 asked to print. The caption must say so, and must not call them calibrated coverage.

## What I did not verify

- A fresh R = 200 run of `scripts/interference_tradeoff.py`, or `scripts/replicate.py`. Both write result files outside this fence.
- A fixed-noise design redraw at min-I, median-I, or for A2. Item 3b is A1 at `c*`, one noise path, R = 400, plus the one-panel Young split for A2.
- The analytical claim that the Young plug-in is an upper bound for every coefficient vector. For this vector the net is conservative; some same-sign pairs pull the other way.
- The thesis prose. It is not written yet. Item 7 is the constraint, not a reading of a draft.

## Commands

- `env -u PYTHONPATH .venv/bin/python -m pytest tests -q -p no:warnings` — exit 0, 72 passed in 7.84s.
- Stamp-free lock digest against `0db57c7` — exit 0, three files MATCH.
- `env -u PYTHONPATH .venv/bin/python -u reviews/probes/V3/probe_a2.py` — exit 0. Log: `reviews/probes/V3/probe_a2.log`.
- `env -u PYTHONPATH .venv/bin/python -u reviews/probes/V3/probe_a2_split.py` — exit 0. Log: `reviews/probes/V3/probe_a2_split.log`.

Premise. The card says write only `reviews/a2-code.md` and `reviews/probes/V3/`. The common-rules line about `docs/cards/progress/` would edit another card's tree. The card fence wins; this file is the progress record.

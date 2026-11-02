# Pre-registration v2: observable moments and two analysts

Status: **frozen before any v2 run.** Approved by Augusto on 2026-10-26 (PLAN item 20).
The commit that adds this file is the timestamp. Nothing below may change after a v2
result exists, except by a new dated amendment at the bottom that says what was already
known when it was written.

The previous design (three moments named after World Bank indicators, and the World Bank
run) is tagged `v1-worldbank-moments` (commit `3ffbb4d`). It still replicates from that tag.

## 1. Why the change

1. The v1 targets used outcomes under two seeding policies (degree and random) that no
   researcher observes together. Their difference was exactly the targeting premium
   theta2 - theta1 (common random numbers), so the targets contained the policy answer.
2. The v1 moments did not restrict the peer effect gamma or the persistence beta: the
   spread of both over the sampled NROY points equalled their spread under a uniform draw
   from the box.
3. The World Bank labels (`level_imm`, `gradient_edu`, `level_internet`) misdescribe the
   planted run and confuse readers.

v2 targets what a researcher could observe: **the village in the status quo, plus one
randomized pilot**. The policy to predict, hub (degree) seeding, is never a target.

## 2. Moments (order frozen)

`moments.simulate_moments(world, c, reps=REPS_MOMENT)` with `REPS_MOMENT = 30` paired reps.
Rep r of the control arm and of the random arm use `seed_offset = r` (same state stream).
The degree arm is not simulated here.

| # | Name | Definition | Arm |
|---|---|---|---|
| 1 | `sq_level` | mean over people of Y_T | control |
| 2 | `sq_corr_x1` | corr over people of (Y_T, x1), x1 = `world.X[:, 0]` | control |
| 3 | `sq_peer_corr` | corr over people of (Y_T,i, (W Y_T)_i), W = A / degree (the kernel's row-normalized adjacency, `adjacency @ y / degrees`) | control |
| 4 | `pilot_level` | mean over people of Y_T | random |

- The Monte Carlo variance of each moment is the sample variance over reps (ddof = 1) divided
  by the number of finite values. Non-finite correlations are dropped. Fewer than two finite
  values gives an infinite variance, so I rejects the point (as in v1).
- Disclosure: with paired reps, `pilot_level - sq_level` at c* equals theta1(c*) exactly. This is
  intended: a randomized pilot identifies theta1. The question is whether the model can
  extrapolate from it to theta2.

## 3. Threshold, discrepancy, targets

- delta = (0.02, 0.05, 0.05, 0.02) in the moment order above: 0.02 for levels and 0.05 for
  correlations, the v1 rule unchanged.
- V = diag(sampling variance of z + Monte Carlo variance at c + delta^2), as in v1.
- tau = chi2 quantile at 0.95 with df = 4 (number of moments) = 9.4877.
- Planted targets: z = M-hat(c*) with `REPS_Z = 200`, c* = the center of C (unchanged).
  `data/planted.json` is rewritten with the new `moment_names`; the legacy `amendment` key is
  replaced by `"design": "preregistration-v2"`. `scripts/plant_z.py` must regenerate it byte for byte.

## 4. Unchanged

Kernel, World, graph and covariate seeds, box C, eta, k/N, horizon, all stream offsets, the
waves (3 x 1000 Latin-hypercube points, box inflation 0.20, clipping to C), the images
(Theta_hm of theta2, Theta_exp of delta_spill, 400 sampled NROY points), the endpoint
recheck, both foil estimators, `classify_interval`, and the Foil 2 calibration check (gate rule
and every parameter in `[foil2_check]`).

## 5. Evaluation: two analysts

Diagnostic points:
- `min_I` and `median_I` (selected by I only, never by theta): **the calibrator**, who fits the
  model and works at one best-fitting point.
- `c_star`: **the field experimenter**, who has one panel from the real village.

At every point, both foils run on the one panel at `FOIL_PANEL_OFFSET`, and the run records:
- `foil1_covers_truth`, `foil2_covers_truth`: containment of the point's own truth
  (theta2(c), delta_spill(c)). Layer (a): is the estimator right about its own world?
- `foil1_covers_planted_truth`, `foil2_covers_planted_truth`: containment of the real
  village's truth (theta2(c*), delta_spill(c*)). Layer (b): is the report right about the village?
  At `c_star` the two coincide.
- `foil1_vs_Theta_hm`, `foil2_vs_Theta_exp`: the interval-geometry verdicts, unchanged.
- `foil1_gap_decomposition` at every point, unchanged.

All of these are descriptive containment indicators for one realized panel, not
repeated-sampling coverage. The Foil 2 calibration check stays the only coverage evidence; its
points are `c_star`, `min_I` and `median_I` of the v2 run.

## 6. Pre-declared descriptive readout (not a gate)

`nroy_param_spread`: for each parameter, the standard deviation over the sampled NROY points
divided by the standard deviation of a uniform draw over C on that axis (span / sqrt(12)),
plus the correlation matrix of the parameters over the sampled points. A ratio near 1 means the
moments do not restrict that parameter. Expectations written now, to be checked, not tuned:
the pilot moment restricts the alpha-kappa trade-off more than v1, and `sq_peer_corr` gives a
gamma ratio below 1. Either may fail; a failure is reported as found.

## 7. Stop rules

- F-EMPTY or F-SINGLETON are findings. Never loosen tau or delta, widen C, or change a moment
  after seeing a v2 result.
- If a test or a check fails, fix the code, not the rule, and say so in the commit message.

## 8. World Bank removal

Removed from the code, the replication script, the results, the figures, the locks, the data
(`data/anchors.json`), the tests, the docs and the paper. It remains reproducible from the tag
`v1-worldbank-moments`.

## Amendments

### A1 (2026-10-30, written AFTER the v2 results were known): a delta sensitivity menu

What was already known when A1 was written:
- the v2 results at `cc01779`: Theta_hm = [0.00577, 0.07369], with spread ratios
  alpha 0.26, beta 0.97, gamma 0.99, kappa 0.96, sigma 0.84;
- the PM's reading that delta_level = 0.02 allows each level a miss of about
  sqrt(9.49 x 0.0004) = 0.062, which is more than theta1(c*) = 0.036.

A1 therefore does not test a hypothesis. It reports how the image depends on the one assumption
that appears to bind, in the spirit of Tamer (2010): a menu of answers indexed by assumptions. The
main design and every headline result stay at delta_level = 0.02. Nothing in sections 2–8 changes.

- **Menu:** delta for the two level moments (`sq_level`, `pilot_level`) in {0.02, 0.01, 0.005}. The
  two correlation moments keep delta = 0.05. tau, C, the moments, the targets z, every seed and
  REPS_MOMENT are unchanged.
- **Per menu entry**, rerun only what delta affects: the waves (`run_waves` with the same seed),
  NROY, the 400-point image sample (`SEED_THETA_SAMPLE`), Theta_hm and Theta_exp, and
  `nroy_param_spread`. Then report `finding_hm`, `wave_kept`, `n_nroy`, both images, the spread
  ratios, and the alpha-kappa correlation.
- **Foils against the menu:** the field experimenter's intervals at c* do not depend on delta.
  Classify both of them (`classify_interval`) against each entry's images. The calibrator's points
  (min-I, median-I) move with delta; do not rerun the foils at the new points (that would be a new
  design). Report only the c* classification.
- F-EMPTY or F-SINGLETON at any entry is reported as found. The menu is never used to pick a delta.
- **Output:** `results/sensitivity/delta_menu.json`, written by `scripts/delta_menu.py` and run by
  `scripts/replicate.py` as its own step. The entry at delta = 0.02 must reproduce the main run's
  images and spread exactly (a built-in consistency check).

### A2 (2026-11-01, written AFTER the v2 and A1 results were known): the price of allowing interference

Approved by Augusto on 2026-11-01. This file's commit that adds A2 is its timestamp. No A2 code
existed and no A2 number had been computed when it was written.

What was already known when A2 was written:
- every v2 and A1 result at `0db57c7` (images, foil intervals, flags, the delta menu);
- Foil 1's gap decomposition: about 90% of the gap between theta2 and (k/N) x beta-hat is the
  effect on unseeded people, at all three points;
- Foil 2 targets delta_spill on the random arm, not theta2, and its repeated-sampling coverage is a
  little under 95% (the Foil 2 check).

**Question.** What does an analyst gain and lose by allowing for interference when the target is
theta2, the effect of seeding the 80 highest-degree people against no campaign?

**Why theta2 needs more than a randomized pilot.** theta2 compares two whole assignment vectors:
the degree vector d2 and the zero vector. Under the pilot design (80 of 800 seeded at random), d2
has probability 1 / C(800, 80), so no pilot ever realizes the policy. Any estimate of theta2 from
the pilot needs (i) an exposure map (a person's outcome depends on the assignment only through a
low-dimensional exposure) and (ii) transport (the exposure-specific outcomes measured on the pilot's
people apply to the people who would hold those exposures under d2).

**Analysts (a ladder of decreasing assumption strength), all reporting an interval for theta2 at
level `HM_CONFIDENCE` (two-sided normal quantile, as both foils):**
- **A0 (SUTVA)** = Foil 1, unchanged: (k/N) x the OLS-HC1 interval on the degree-arm panel.
- **A1 (exposure transport).** On the random-arm panel, the Foil 2 strata (S1, S0a, S0b, S0c, with
  the same cut 0.25 and the same per-panel merge rule) and the Hajek means mu_s with exact
  first-order probabilities. Let w_s = n_s(d2) / N, the share of people in stratum s under the
  degree vector d2 (the analyst knows the graph, so w is a known constant; under a merged panel the
  shares use the merged strata). The estimate is
  theta2_A1 = sum over s != S0a of w_s (mu_s - mu_S0a).
  It is a fixed linear combination of Hajek means. Its variance is the existing linearized
  Aronow-Samii covariance (`ht_cov` with joint probabilities from the same simulated assignments),
  summed over all pairs of strata with the combination's coefficients.
- **A2 (degree-binned transport).** As A1, with every stratum split into two bins fixed by the
  graph: H = the 80 people d2 seeds, L = everyone else. Under d2 every person in H is in S1, so
  theta2_A2 = (80/N)(mu_{S1,H} - mu_{S0a,H}) + sum over s != S0a of (n_{s,L}(d2)/N)(mu_{s,L} - mu_{S0a,L}).
  Same variance machinery, with each cell's indicators restricted to its bin. No merging across
  bins. If a cell the formula needs is empty in a panel, A2 is undefined for that panel; that is
  counted and reported, never imputed.

**Truth and evaluation.** The truth is theta2(c) from `evaluate_thetas` (unchanged). At each of the
three diagnostic points (`min_I`, `median_I`, `c_star`):
1. **One panel** (offset `FOIL_PANEL_OFFSET`): each analyst's interval, `covers_truth`,
   `covers_planted_truth`, and `classify_interval` against Theta_hm. Descriptive, as before.
2. **Repeated sampling:** R = 200 panels on a fresh block of stream offsets 2,000,000 + r
   (disjoint from every existing block). Each panel redraws the noise and, for A1 and A2, the
   random assignment. Report per analyst: mean estimate, bias (mean - truth), SD, RMSE, mean
   reported SE, SE/SD, coverage of the truth with an exact Clopper-Pearson 95% interval, mean
   interval width, width relative to the width of Theta_hm, and the undefined count (A2).

**Readouts.** A table per point, and one figure: |bias| against mean interval width, one marker
per analyst per point, with the width of Theta_hm as a reference line and coverage printed beside
each marker.

**Expectations written now, to be checked, not tuned.** At every point:
(a) |bias| falls from A0 to A1 to A2; (b) SD and width rise from A0 to A1 to A2;
(c) A0 coverage is far below nominal; A2 coverage is the closest to nominal of the three;
(d) A1 and A2 stay biased downward, because two-hop spillover raises the S0a people above the
true control level; (e) every interval is narrower than Theta_hm. Any of these may fail; a failure
is reported as found.

**Locks.** Nothing in sections 2–8 or A1 changes. The main run's results and the delta menu must
reproduce byte for byte (apart from run stamps). The exposure cut, merge rule, Monte Carlo draws,
the confidence level and the bins H/L are fixed above and are never chosen after an A2 result.
**Output:** `results/interference/tradeoff.json`, written by `scripts/interference_tradeoff.py`,
run by `scripts/replicate.py` as its own step (skipped with `--quick`).

**Erratum to A2 (2026-11-01 16:40, wording only; no design element changes).** "So no pilot ever
realizes the policy" overstates: the event has probability 1 / C(800, 80) > 0. Read instead: "So a
pilot realizes the policy with negligible probability; in practice it never does, and positivity
holds for the policy vector only in this negligible sense." Found by verifier card VV
(`reviews/video-script.md`, item 3).

**A2.1 (2026-11-01 18:20, written AFTER the A2 results and V3's review): a descriptive variance
split.** V3 (`reviews/a2-code.md`, item 3b) found that A1's and A2's reported SE is about 2.3–3.1
times the sampling SD because of the Young bound on pairs with zero joint exposure probability, and
checked this with a probe for A1 at c_star only. A2.1 turns that probe into a committed, descriptive
readout so the paper can cite it. It changes no A2 estimator, interval, flag or verdict, and no
number in `results/interference/tradeoff.json`.
- **Per point** (`min_I`, `median_I`, `c_star`) and per analyst (A1, A2, and Foil 2's delta_spill
  for comparison): on the one panel at `FOIL_PANEL_OFFSET`, the reported variance split into the
  term over pairs with positive joint probability and the Young-bound term, and the Young share.
- **Fixed-noise design redraw:** noise path at `FOIL_PANEL_OFFSET`; R_design = 400 assignment
  redraws on a fresh assignment block (3,000,000 + r); report the design SD, the mean main-term SE^2
  over the design variance, and the mean full SE^2 over the design variance.
- **Output:** `results/interference/variance_split.json`, written by
  `scripts/a2_variance_split.py`, run by `scripts/replicate.py` (skipped with `--quick`).
- No expectation is written: the readout is descriptive and was designed after its answer was seen
  at one point.

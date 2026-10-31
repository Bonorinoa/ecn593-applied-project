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

# Specification

This document describes the code in this repo, on the branch `code-is-law`. If the document and the code disagree, the code is what ran, and the document has an error. The code is law. Main-pipeline constants are in `src/poc_abm/config.py`. The Foil 2 check defines its check-specific constants in `scripts/check_foil2_coverage.py`. Run outputs below come from the committed results in `results/`. Run constants come from the cited code. Paths are relative to the repo root. Code identifiers appear in code font.

Sections 1 to 5 cover the model, the targets, the images and foils, the non-claims, and the World Bank run. Section 6 lists the outputs of each script and the environment.

## 1. The model

### 1.1 The world

The world is the graph plus the covariates. It is the class `kernel.World`. It is drawn once, and every simulation shares it.

- The number of people is $N = 800$ (`N_AGENTS`).
- The edge rule draws $A_{ij} \sim \text{Bernoulli}(p)$ with $p = 4/N$ (`EDGE_P`) for every ordered pair. Then the graph is symmetrized, $A \mid A^\top$, and the diagonal is set to zero. There are no self-loops.
- So $P(\text{edge}) = 1 - (1-p)^2 \approx 8/N$. The value 4 in $p = 4/N$ is the rate per ordered pair. The mean degree is about 8: 7.97 in theory and 8.085 measured on this world.
- The degree is $k_i = \max(\text{row sum}, 1)$. It is stored in `World.degrees`. An isolated person has $k_i = 1$.
- The covariates are $X \sim U[0,1]^3$ (`N_COVARIATES`). Column x1 is education or literacy, x2 is resources, and x3 is baseline propensity.
- The graph uses the seed `SEED_GRAPH` = 20260812. The covariates use `SEED_X` = 20260813.
- `World.from_arrays` builds a hand-made world for tests. It does not use these seeds.

### 1.2 The kernel

The kernel is the function `kernel.simulate_panel(world, c, rule, seed_offset)`. It is a logit linear-in-means update: a linear-in-means index passed through a logistic link. One call returns one panel, the pair $(Y_T, D)$.

For $t = 0, \dots, T-1$ with $T = 20$ (`HORIZON`) and $t^* = 0$ (`INTERVENTION_TIME`):

$$Y_i(t+1) = \Lambda\Big(\alpha + \beta\, Y_i(t) + \gamma\, \frac{(A\,Y(t))_i}{k_i} + \eta \cdot X_i + \kappa\, D_i\, \mathbf{1}\{t \ge t^*\} + \sigma_\varepsilon\, \varepsilon_i(t)\Big)$$

$$\Lambda(z) = \frac{1}{1 + e^{-z}}, \qquad \varepsilon_i(t) \sim N(0,1), \qquad Y_i(0) \sim U[0,1]$$

- $\Lambda$ is the function `kernel.logistic`. It clips its argument to $[-60, 60]$.
- $\eta = (0.05, 0.10, 0.02)$ is fixed (`ETA_FIXED`). It is not a free parameter.
- Because $t^* = 0$, the treatment term acts at every step.
- The update rule is chosen, not derived. Its lineage: Manski (1993) for linear-in-means, Bramoullé, Djebbari and Fortin (2009) for the row-normalized peer mean, and Brock and Durlauf (2001) for the logistic link.

The parameters are $c = (\alpha, \beta, \gamma, \kappa, \sigma_\varepsilon)$. A parameter point is a Python dict with these keys. The box C is the dict `PARAM_BOX`:

| Parameter | Interval |
|---|---|
| $\alpha$ (`alpha`) | $[-2.5, -0.5]$ |
| $\beta$ (`beta`) | $[0.05, 0.60]$ |
| $\gamma$ (`gamma`) | $[0.05, 0.80]$ |
| $\kappa$ (`kappa`) | $[0.25, 2.50]$ |
| $\sigma_\varepsilon$ (`sigma_eps`) | $[0.01, 0.40]$ |

The value $\gamma = 0$ is outside the box on purpose. Peer influence is always present. The planted point $c^*$ is the center of C (`C_STAR`): $(-1.5, 0.325, 0.425, 1.375, 0.205)$.

### 1.3 The arms

The function `kernel.assign(world, rule, rng)` returns the treatment vector $D$. The number of seeded people is $k = \lceil 0.10 \cdot N \rceil = 80$ (`n_treated`, `SEED_FRACTION`).

- The control arm $\pi_0$ (`"control"`) seeds no one.
- The random arm $\pi_1$ (`"random"`) seeds 80 people sampled without replacement.
- The degree arm $\pi_2$ (`"degree"`) seeds the 80 people with the highest degree. Ties go to the lower index (`np.lexsort`). The arm is deterministic given the graph.

On this world the lowest degree among the seeded people is 12. 36 people have degree 12, and 35 of them are seeded.

### 1.4 Streams and seeds

The function `kernel.stream_seed(label, offset)` returns the crc32 of the key `"{len(label)}:{label}:{offset}"`. The code never uses Python `hash()`, because CPython salts string hashes in each process.

- Each panel uses two streams. The state stream `stream_seed("state", r)` draws $Y(0)$ first and then the shocks $\varepsilon(t)$. The assignment stream `stream_seed("assign:" + rule, r)` draws the random arm.
- Rep $r$ of every arm shares the state stream. The reps are paired, so arm contrasts have low noise.
- The whole pipeline is deterministic. A rerun reproduces every number.

| Stream or seed | Value | Use |
|---|---|---|
| `SEED_GRAPH` | 20260812 | the graph |
| `SEED_X` | 20260813 | the covariates |
| `SEED_HM` | 20260814 | one Generator for the history-matching designs of all waves |
| `SEED_THETA_SAMPLE` | 20260815 | the 400 sampled NROY points |
| `SEED_FOIL2_MC` | 20260817 | the simulated assignments for joint exposure probabilities |
| offsets 0 to 29 | `REPS_MOMENT` = 30 | the moments M(c) |
| offsets 0 to 199 | `REPS_ESTIMAND` = 200 | the estimands, the targets z, the gap decomposition |
| offset 0 | `FOIL_PANEL_OFFSET` | the one panel each foil sees |
| offsets 100000 to 100199 | `RECHECK_OFFSET` | the endpoint recheck |
| seeds 1,000,000 and up | `GATE_SEED` | the assignments of the Foil 2 calibration check |
| seeds 10,000 and up | in `check_foil2_coverage.py` | the assignment-only redraws of the check |
| seed 20261020 | `BOOT_SEED` | the bootstrap of the check |

### 1.5 The estimands

The function `estimand.evaluate_thetas(world, c, reps=200, offset0=0)` runs $R = 200$ paired reps of the three arms. It returns the JSON keys `theta1`, `theta2`, `premium`, `se_theta1` and `se_theta2`. Let $\bar Y_T$ be the mean of $Y_T$ over people.

$$\theta_1(c) = E[\bar Y_T \mid \pi_1] - E[\bar Y_T \mid \pi_0]$$
$$\theta_2(c) = E[\bar Y_T \mid \pi_2] - E[\bar Y_T \mid \pi_0] \qquad \text{(the headline)}$$
$$\psi(c) = \theta_2(c) - \theta_1(c) \qquad \text{(the premium)}$$

- The expectation is over simulation noise, and over the random assignment in $\pi_1$.
- The code replaces each expectation with the mean over the 200 reps (`thetas_from_means`).
- `se_theta2` is the pointwise Monte Carlo SE at a fixed $c$: the standard deviation of $y_2 - y_0$ over reps, divided by $\sqrt{R}$.

The exposure strata come from the exposure share $s_i = (A D)_i / k_i$ (`exposure_share`). The function `stratum_labels` assigns four strata:

| Stratum | Definition |
|---|---|
| S1 | $D_i = 1$ |
| S0a | $D_i = 0$ and $s_i = 0$ |
| S0b | $D_i = 0$ and $0 < s_i < 0.25$ |
| S0c | $D_i = 0$ and $s_i \ge 0.25$ |

The split at 0.25 is `EXPOSURE_SHARE_CUT`. The function `maybe_merge_s0b` applies the merge rule. If any of the four strata has fewer than `STRATUM_MIN_N` = 20 people in that panel, S0b merges into S0c for that panel. This is the "thin cell" rule.

The spillover truth is `estimand.evaluate_spill(world, c, reps=200)`. It runs 200 random-arm reps on the true $Y$. In each panel, `true_spill_from_panel` computes the realized contrasts. The merge rule applies to each panel on its own. A panel with an empty stratum gives nan, and `evaluate_spill` drops it from the mean.

$$\delta_{\text{spill}}(c) = \text{mean over reps of } \big[\overline{Y}_{S0c} - \overline{Y}_{S0a}\big], \qquad \delta_{\text{dir}}(c) = \text{mean over reps of } \big[\overline{Y}_{S1} - \overline{Y}_{S0a}\big]$$

The JSON keys are `delta_spill`, `delta_dir`, `se_spill` and `merged_s0b`.

## 2. Targets and history matching

History matching is calibration, not estimation. There are five free parameters and three moments. The model is underidentified on purpose. The question is which policy effects remain possible, not which $c$ is true.

### 2.1 The planted targets

- The planted point is $c^* = $ the center of C (`C_STAR`, JSON key `c_star`).
- The targets are $z = \hat M(c^*)$, the moments at $c^*$ over 200 reps (`REPS_Z`). They are stored in `data/planted.json`.
- The function `moments.plant_and_freeze(world, path)` writes the file. The loader is `moments.load_frozen_z`.
- The file has the keys `c_star`, `z`, `sampling_variances`, `reps_z` and `moment_names`. The key `sampling_variances` holds the Monte Carlo variances of the 200-rep mean, one per moment. The key `amendment` is a legacy label. It stays so that the file reproduces byte for byte.
- `scripts/plant_z.py` regenerates the file. By default it only checks. The regenerated copy reproduces `data/planted.json` byte for byte.

### 2.2 The moments

The function `moments.simulate_moments(world, c, reps=30)` returns the moments $M(c)$ and their Monte Carlo variances $\sigma^2_{MC}$. It uses $R_m = 30$ paired reps (`REPS_MOMENT`). Two arms run, not three. The control arm is not simulated here.

| Slot (`MOMENT_NAMES`) | Definition |
|---|---|
| `level_imm` | mean $\bar Y_T$ in the degree arm |
| `gradient_edu` | corr($Y_T$, x1) in the degree arm |
| `level_internet` | mean $\bar Y_T$ in the random arm |

The slot names are legacy names from the World Bank version of the project. They stay in the code so that the saved files keep their keys. They do not describe immunization or internet use in the planted run.

The variance $\sigma^2_{MC}$ is the sample variance of the per-rep values (ddof = 1) divided by $R_m$. The code drops non-finite correlations. If fewer than two values remain, the variance is infinite, and $I$ rejects the point.

### 2.3 Implausibility

The function `moments.implausibility(z, m_hat, v_diag)` computes

$$I(c) = (z - \hat M)^\top V^{-1} (z - \hat M), \qquad V = \text{diag}\big(\sigma^2_z + \sigma^2_{MC}(c) + \delta^2\big)$$

- $\sigma^2_z$ is `sampling_variances` from `data/planted.json`.
- $\delta = (0.02, 0.05, 0.02)$ is the discrepancy (`DELTA`, `discrepancy()`).
- The function `v_diag_of(sampling, mc)` builds the diagonal of $V$.
- The threshold is $\tau = \chi^2_{0.95}(3) = 7.8147$ (`history_matching.tau_threshold`, `HM_CONFIDENCE`, `N_MOMENTS`). The code keeps a point if $I \le \tau$.
- The same `HM_CONFIDENCE` sets the 95% level of both foils.

### 2.4 The waves

The function `history_matching.run_waves(world, z, sampling)` runs 3 waves (`WAVES`) of 1000 Latin-hypercube points (`WAVE_POINTS`). The sampler is the scipy `LatinHypercube`. One numpy Generator, seeded with `SEED_HM`, serves all waves. There is no emulator. The code simulates every point.

1. In wave 1 the box is C.
2. In each wave, evaluate $I$ at every point. Keep the points with $I \le \tau$.
3. The next box is the bounding box of the points kept in that wave (the helper `survivor_bbox`, a legacy name). Its span widens by 20% (`BOX_INFLATION`), which is 10% on each side. Then `clip_box` clips it to C.
4. NROY is the union of the kept points over all waves.

The JSON keys are `wave_kept`, `wave_I_stats` (min, median, max of $I$ in each wave), `n_nroy` and `closest`. The key `closest` holds the lowest $I$ over all evaluated points, with its moments.

The code sets two flags in the key `finding_hm`:

- F-EMPTY if NROY is empty. The code never loosens $\tau$ or $\delta$. If a wave keeps no point, the loop stops, and NROY keeps the points of earlier waves.
- F-SINGLETON if every axis span of NROY is less than 5% of the box span (`SINGLETON_SPAN_FRACTION`).

F-SINGLETON is only a flag. The code does not widen anything. In the committed planted run `finding_hm` is `null`. The kept counts are 202, 416 and 373, and NROY has 991 points.

## 3. Images and the two foils

### 3.1 The images

The function `pipeline.run_poc("planted")` samples 400 NROY points uniformly without replacement (`THETA_SAMPLE`, `sample_nroy_index`, seed `SEED_THETA_SAMPLE`). At each point it evaluates theta2 and delta_spill with 200 reps. The image is the range over the sample (`interval_image`):

- Theta_hm = [min, max] of theta2. It is $[0.00587, 0.07325]$.
- Theta_exp = [min, max] of delta_spill. It is $[-0.000571, 0.026893]$.

The file `results/planted/image_points.json` stores every point. Each record has `nroy_index`, `I`, `c`, `theta2`, `se_theta2`, `delta_spill` and `se_spill`. The image is not a posterior.

### 3.2 The endpoint recheck

The function `pipeline.recheck_extremizers` evaluates each point that sets an endpoint again. It uses 200 fresh reps on the stream offsets 100000 to 100199 (`RECHECK_OFFSET`). The result is the JSON key `endpoint_recheck`. Each candidate has `pilot_value`, `pilot_pointwise_se`, `fresh_value` and `fresh_pointwise_se`.

| Endpoint | NROY index | Pilot (SE) | Fresh (SE) |
|---|---|---|---|
| Theta_hm lower | 877 | +0.005870 (0.000004) | +0.005871 (0.000003) |
| Theta_hm upper | 802 | +0.073250 (0.000006) | +0.073255 (0.000006) |
| Theta_exp lower | 944 | −0.000571 (0.000502) | +0.000201 (0.000491) |
| Theta_exp upper | 904 | +0.026893 (0.000259) | +0.027274 (0.000263) |

Required wording (verifier `t_1f00fc3b`):

> Each bar in `image_points.json` is a pointwise Monte Carlo SE conditional on a fixed parameter point c. The displayed image endpoints are extrema selected from 400 noisy estimates. So the SE attached to the extremizing point is not an SE for the endpoint. It does not include extremum-selection uncertainty. Fresh independent re-evaluation of the pilot-selected extremizers removes reuse-of-noise bias for those candidates. It is not simultaneous inference for the true extrema.

### 3.3 The diagnostic points

The function `estimand.diagnostic_worlds(nroy, I)` sorts NROY by $I$ with a stable sort. The min-I point is the first. The median-I point is the one at position `len(I) // 2`. Both depend on $I$ only, never on theta2. We write $c_0$ for either point.

- The min-I point has NROY index 121 and $I = 0.0017$. Its parameters are $\alpha = -1.4871$, $\beta = 0.399$, $\gamma = 0.3301$, $\kappa = 1.3446$ and $\sigma_\varepsilon = 0.1984$.
- The median-I point has NROY index 418 and $I = 2.0208$. Its parameters are $\alpha = -1.5108$, $\beta = 0.4454$, $\gamma = 0.2426$, $\kappa = 2.4654$ and $\sigma_\varepsilon = 0.1764$.

### 3.4 Foil 1: the SUTVA analyst

Foil 1 uses the degree arm and one panel (offset 0). The functions are `diagnostic.foil1_policy` and `diagnostic.ols_ate_hc1`.

1. Fit OLS of Y on $[1, D, X]$. The coefficient on $D$ is the OLS coefficient beta-hat. The interval is beta-hat $\pm$ 1.96 SE, with an HC1 standard error: the sandwich times $n/(n-5)$.
2. Read the share $k/N$ from the panel. It is 0.1.
3. The SUTVA analyst's policy estimate is $(k/N) \cdot \hat\beta$. The interval is the HC1 interval scaled the same way.
4. Compare the scaled interval with Theta_hm.

The scaling by a known positive constant keeps the analyst's own coverage statement. It does not repair the analyst's assumptions. The JSON keys are `foil1_estimator`, `foil1_beta`, `foil1_ci_beta`, `foil1_share`, `foil1_ci`, `foil1_vs_Theta_hm`, `foil1_covers_truth` and `foil1_gap_decomposition`. The truth is `theta2_true`.

Five statements must stay with every report of Foil 1 (verifiers `t_2b7a8d8c` and `t_1f00fc3b`):

1. Foil 1 is not an identified estimator of the simulator's θ2 under the actual interference model. It is the whole-village policy estimate implied by a SUTVA analyst, (k/N)·beta-hat, with k/N = 0.1.
2. That interpretation assumes consistency/SUTVA, conditional exchangeability and positivity given X, a correctly specified additive constant-effect outcome model, and a sampling/asymptotic basis for HC1. The deterministic top-degree assignment does not establish those assumptions.
3. After scaling, the Foil 1 intervals are strictly inside Theta_hm and exclude θ2(c0) at both diagnostic points. So F-OVERCONF is an assumption-contingent interval-geometry finding. It is not a coverage claim for θ2 under interference.
4. Across 200 paired panels, about 90% of the gap between θ2 and (k/N) times the 200-panel mean OLS coefficient is the policy effect on unseeded people. For the displayed replication-0 point estimate, the corresponding shares are about 96% at min-I and 92% at median-I.
5. The rescaling was adopted after the frozen numbers were inspected. Its justification is the SUTVA aggregation identity. The post hoc design correction is disclosed.

### 3.5 The gap decomposition

The function `diagnostic.policy_gap_decomposition(world, c, displayed_beta=...)` explains why $(k/N)\hat\beta$ differs from theta2. It uses the paired control and degree panels for reps 0 to 199. The two panels share $Y(0)$ and every shock, so $y_2 - y_0$ is each person's policy effect in that rep. Let $S$ be the seeded set.

$$\theta_2 = \underbrace{\tfrac{1}{N}\textstyle\sum_{i \in S}(y_2 - y_0)}_{\text{the seeded part}} + \underbrace{\tfrac{1}{N}\textstyle\sum_{i \notin S}(y_2 - y_0)}_{\text{the unseeded part}}$$

The split is exact with paired streams. The unseeded part is zero under SUTVA. The JSON keys are `seeded_part` and `unseeded_part`.

- The seeded policy contrast is the mean of $y_2 - y_0$ over $S$ (`selected_policy_contrast`). Under interference it is the policy contrast of the seeded people. It is not the SUTVA effect of own treatment.
- `mean_beta` is the mean of beta-hat over the same 200 reps.
- The gap for the mean beta is `gap_mean_beta` = theta2 − (k/N)·`mean_beta`. It splits into the unseeded part and `ols_error_part_mean_beta` = (k/N)(seeded policy contrast − `mean_beta`). The key `unseeded_share_of_gap_mean_beta` is the unseeded part divided by the gap.
- The gap for the displayed beta is `gap_displayed` = theta2 − (k/N)·`displayed_beta`. Here `displayed_beta` is the beta-hat of the Foil 1 panel. The key `unseeded_share_of_gap_displayed` is the unseeded part divided by this gap.
- Keep the two gaps apart. The first averages over 200 panels. The second uses the one displayed panel.
- The key `baseline_gap_seeded_minus_unseeded` is the mean of $y_0$ over $S$ minus the mean over people not in $S$. It is the difference under no campaign.

| | min-I point | median-I point |
|---|---|---|
| theta2 | 0.03708 | 0.06346 |
| seeded part | 0.03374 | 0.05925 |
| unseeded part | 0.00333 | 0.00421 |
| seeded policy contrast | 0.3374 | 0.5925 |
| mean beta | 0.3339 | 0.5880 |
| gap for the mean beta | 0.00369 | 0.00466 |
| unseeded share (mean beta) | 0.9034 | 0.9027 |
| OLS-error part (mean beta) | 0.00036 | 0.00045 |
| gap for the displayed beta | 0.00346 | 0.00456 |
| unseeded share (displayed beta) | 0.9642 | 0.9236 |
| baseline gap | 0.0007 | 0.0007 |

Why there is no third foil (decision D3). In the degree arm, treatment is a deterministic function of degree and the index tie-break. Conditioning on degree leaves severe practical positivity failure: no treated people appear below degree 12, no untreated people appear above degree 12, and only one untreated person appears at degree 12. Omitting degree leaves the assignment variable unadjusted. A forest can differ numerically from OLS, but it retains the same SUTVA blind spot and does not identify $\theta_2$ from this panel. A design-based third foil needs randomization across villages (Hudgens and Halloran 2008, Baird et al. 2018).

### 3.6 Foil 2: Hájek on the random arm

Foil 2 uses the random arm and one panel (offset 0). The function is `estimand.hajek_contrasts(world, Y, D)`.

1. Compute the exposure share $s_i$ and the strata S1, S0a, S0b and S0c, as in section 1.5.
2. If any stratum has fewer than 20 people in this panel, merge S0b into S0c for this panel. The S0b probability mass joins S0c in the same way.
3. Compute exact first-order exposure probabilities with `exposure_probs`. Under the random arm, $P(S1) = k/N$. For a person of degree $d$ the number of treated neighbors is hypergeometric: $K \mid D_i = 0 \sim \text{Hypergeom}(N-1, k, d)$.
4. Compute Hájek means (`hajek_mean`), which weight each person by 1 / P(exposure).
5. Estimate joint exposure probabilities with `exposure_mc`. It simulates 10,000 random-arm assignments (`EXPOSURE_MC_DRAWS`) with a Generator seeded `SEED_FOIL2_MC`. The helper `joint_probs` turns them into first- and second-order probabilities. The code caches the result by a hash of the adjacency matrix.
6. Estimate the variance with `ht_cov`, the Aronow–Samii (2017) estimator. The code linearizes each Hájek mean with $e_i = y_i - \hat\mu_{\text{exposure}}$. Pairs that are never seen together get Young's bound. In the code the first-order probability replaces the diagonal of the joint matrix.
7. The variance of the contrast is $V(S0c) + V(S0a) - 2\,\text{Cov}(S0c, S0a)$. The interval is the estimate $\pm$ 1.96 SE.
8. Compare the interval for delta_spill = S0c − S0a with Theta_exp. The truth is `spill_true`.

The JSON keys are `foil2_estimate`, `foil2_se`, `foil2_merged_s0b`, `foil2_ci`, `foil2_vs_Theta_exp` and `foil2_covers_truth`. The function also returns delta_dir and its interval (`ci_dir`). An earlier version (commit `ebed7ce`) used a first-order variance that dropped the covariance between the strata. Commit `36ed3e6` replaced it.

### 3.7 Verdicts and covers_truth

The function `diagnostic.classify_interval(interval, image)` compares an interval $[lo, hi]$ with its own image $[L, U]$.

- F-HONEST if the interval covers the image: $lo \le L$ and $hi \ge U$.
- F-OVERCONF if the interval lies strictly inside the image: $lo > L$ and $hi < U$.
- Otherwise there is no verdict (`None`). The same holds if any end is not finite.

Each foil is judged against its own image. Foil 1 goes against Theta_hm. Foil 2 goes against Theta_exp.

The function `diagnostic.covers_truth(ci, truth)` is true if the truth lies inside the interval. Required wording:

> At each diagnostic point, covers_truth reports whether the displayed interval contains the simulator truth. It is a descriptive containment indicator for that realized panel, not an estimate of repeated-sampling coverage and not a validity gate. Foil 2 is checked separately by the pre-declared repeated-assignment calibration in scripts/check_foil2_coverage.py.

The committed results:

| | min-I point | median-I point |
|---|---|---|
| Foil 1 interval | [0.03259, 0.03465] | [0.05832, 0.05949] |
| Foil 1 verdict | F-OVERCONF | F-OVERCONF |
| Foil 1 contains the truth | no | no |
| Foil 2 estimate (SE) | 0.00619 (0.00470) | 0.00826 (0.00416) |
| Foil 2 merged S0b | no | no |
| Foil 2 interval | [−0.003022, 0.015410] | [0.000112, 0.016406] |
| Foil 2 verdict | no verdict | F-OVERCONF |
| Foil 2 contains the truth | yes | yes |

### 3.8 The median-I Foil 2 paragraph

Required wording (verifier `t_7afcff9b`):

> Against the saved 200-rep pilot image, Theta_exp = [−0.000571, 0.026893], the median-I Foil 2 interval [0.000112, 0.016406] is strictly interior and is therefore classified F-OVERCONF. That classification is not robust to endpoint Monte Carlo noise. An independent 200-rep recheck of the pilot-selected lower-end candidate is 0.000201 (pointwise MC SE 0.000491). This value is above the lower end of the interval. The recheck evaluates selected candidates. It neither identifies nor bounds the true extrema over all 400 sampled NROY points. We therefore claim no robust Foil 2 verdict at either diagnostic point.

### 3.9 The Foil 2 calibration check

The script `scripts/check_foil2_coverage.py` is a required freeze check. Its output is `results/checks/foil2_coverage.json`. The script has two parts.

The gate asks whether the implemented variance understates on average.

- The outcomes obey the exposure map exactly: $y_i = b_i + 0.05 \cdot \mathbf{1}\{S1\} + 0.03 \cdot \mathbf{1}\{S0c\}$. The base $b$ is the control panel at $c^*$ (offset 0). So the true spillover is exactly 0.03.
- The gate draws 10,000 random-arm assignments (`R_GATE`), with seeds `GATE_SEED` + a for a = 0, 1, and so on. The bootstrap uses 1,000 resamples (`BOOT_REPS`).
- The rule was written before the run. The gate fails if $\text{ratio} + 1.645 \cdot \text{boot SE} < 1$. Here ratio is mean($SE^2$) / Var(estimate).
- The gate reports the coverage of the nominal 95% interval with an exact Clopper–Pearson interval. It does not gate on coverage.
- The committed result: the mean estimate is 0.03006, the ratio is 1.034 (bootstrap SE 0.0154), and the gate passes (`pass` is true). The coverage is 0.9343, with an exact 95% interval of [0.9293, 0.9391].

The kernel result is reported, not gated. For each point ($c^*$, min-I, median-I) the script runs 200 kernel panels (`R`) and measures the coverage of the target `evaluate_spill`. Then it holds the noise path fixed (state offset 0) and redraws only the assignment 300 times (`R_DESIGN`).

| Point | Kernel coverage (R = 200) | Design-only coverage |
|---|---|---|
| $c^*$ | 0.920 | 0.930 |
| min-I | 0.930 | 0.930 |
| median-I | 0.925 | 0.9267 |

The kernel does not obey the exposure map exactly, because the spillover also travels two steps. So kernel coverage below 95% is a finding about Foil 2. The script exits with code 1 if the gate fails. It stops at once if `results/planted/poc_results.json` does not exist.

Required wording:

> In a fixed-world repeated-assignment check whose outcomes obey the exposure map exactly, the nominal 95% Foil 2 Wald interval covered 93.4% of assignments (exact 95% binomial interval 92.9%–93.9%). The average estimated variance was 1.034 times the empirical design variance, so the shortfall is not explained by average variance underestimation. It reflects the finite-sample behavior of this studentized normal interval, with the implemented Hájek linearization and simulated joint exposure probabilities.

The check is implementation-specific. It does not test the theorem of Aronow and Samii. Their exact result is for Horvitz–Thompson totals with exact joint probabilities. The code uses Hájek means, a first-order linearization, and one simulated table of joint probabilities.

## 4. What the project does not claim

- Theta_hm is not a posterior. It is not a Manski/Tamer identified set. It comes from a thresholded discrepancy. Sampling noise is folded into V. The kernel is taken as true. The image shares the reporting logic of a set, so do not collapse it to a point.
- The closest NROY point ($I = 0.0017$) does not recover $c^*$. Fit does not pick the truth.
- F-OVERCONF for Foil 1 is about interval geometry under the analyst's assumptions. It is not a coverage claim.
- The project has one planted world, one graph, and one set of targets. It claims no external validity.

## 5. The World Bank run

The command `python scripts/run_poc.py worldbank` reproduces the 2026-08 attempt with real World Bank anchors. It is a historical sensitivity run. The code is `scripts/fetch_anchors.py`, `data_worldbank.build_anchors` and `moments.load_worldbank_z`. The stored input is `data/anchors.json`.

- The indicators are `SH.IMM.IDPT`, `SE.SEC.CMPT.LO.ZS` and `IT.NET.USER.ZS` (`WB_INDICATORS`). The API call uses the most recent non-empty value per country.
- The targets are $z = (0.8621, 0.6054, 0.6864)$. The two levels are cross-entity means divided by 100. The gradient is the cross-entity correlation of immunization with secondary completion.
- The diagonal weights are $(6.49 \times 10^{-5}, 1.85 \times 10^{-3}, 3.23 \times 10^{-4})$. The JSON key `sampling_variances` holds them, and `variance_label` names them.
- The run ends in F-EMPTY. In wave 1, no point is kept. The best $I$ is 204.35, the median is 1093.22 and the maximum is 1818.34, against $\tau = 7.8147$.
- The closest moments are $M = (0.6188, 0.0545, 0.6133)$ at $c = (-0.5427, 0.5700, 0.7211, 2.2932, 0.2184)$. In the 1,000 sampled wave-1 points, none passed the threshold. The closest sampled education correlation was 0.05, against a target of 0.61.
- The run draws no images and no foils. It draws `waves.png` and `empty.png`.

`scripts/fetch_anchors.py` fetches the data and compares it with `data/anchors.json`. It writes nothing unless you pass `--write`. The API serves the latest values, so a new fetch differs from the stored file.

Required note:

> The World Bank sensitivity run reproduces a historical F-EMPTY calculation. Its diagonal weights are legacy heuristic cross-entity dispersion terms, not design-based sampling variances or village-level measurement-error variances. The source includes overlapping regional/income aggregates, uses ddof=0 for level dispersion, and uses an asymptotic n-2 correlation convention.

## 6. Outputs per script, and the environment

| Command | Reads | Writes |
|---|---|---|
| `python scripts/plant_z.py` | `data/planted.json` | `results/checks/planted_regenerated.json` (a scratch copy). Exit 0 if the bytes match, exit 1 if not. With `--write` it overwrites `data/planted.json`. |
| `python scripts/run_poc.py planted` | `data/planted.json` | `results/planted/poc_results.json`, `results/planted/image_points.json`, `figures/planted/waves.png`, `figures/planted/image_points.png`, `figures/planted/overlay.png`, `locks/freeze-planted.txt` |
| `python scripts/run_poc.py worldbank` | the stored World Bank file in `data/` | `results/worldbank/poc_results.json`, `figures/worldbank/waves.png`, `figures/worldbank/empty.png`, `locks/freeze-worldbank.txt` |
| `python scripts/check_foil2_coverage.py` | `results/planted/poc_results.json` | `results/checks/foil2_coverage.json` |
| `python scripts/draw_figures.py planted` | `results/planted/poc_results.json`, `results/planted/image_points.json` | the figures of that run. It runs no simulation. |

The file `poc_results.json` has these keys: `git_commit`, `ran_at`, `z_source`, `z`, `z_names`, `sampling_variances`, `delta`, `tau`, `finding_hm`, `wave_kept`, `wave_I_stats`, `closest`, `n_nroy`, `param_names`, `c_star`, `theta_star`, `spill_star`, `notes` and `figures`. The planted run adds `Theta_hm`, `Theta_exp`, `n_theta_sample`, `endpoint_recheck` and `findings` (the keys `min_I` and `median_I`). The World Bank run adds `variance_label`. The key `git_commit` is the HEAD hash of the code, with `+dirty` if `src/`, `scripts/`, `data/` or the requirements files differ from it.

The planted run also stores `theta_star` and `spill_star`, the truth at $c^*$: theta1 = 0.03631, theta2 = 0.03826, premium = 0.00195, and delta_spill = 0.00792.

The pins are Python 3.11, numpy 2.4.6, scipy 1.15.3, matplotlib 3.10.3 and pytest 8.4.2. The pipeline calls `uv pip freeze` to write `locks/freeze-*.txt`, so `uv` must be on the path. The tests are in `tests/`. There are 51 of them.

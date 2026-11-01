# Specification

This document describes the code in this repo, on the branch `main`. If the document and the code disagree, the code is what ran, and the document has an error. The code is law. Every exogenous parameter is in `config/world.toml` (the simulated village and the policy question) or `config/design.toml` (the analyst's choices, including the Foil 2 check in section `[foil2_check]`). `src/poc_abm/config.py` loads them and states two derived rules: `EDGE_P` = `edge_rate` / N, and c* = the center of C. Endogenous quantities are never in config. Run outputs below come from the committed results in `results/`. Run constants come from the cited code. Paths are relative to the repo root. Code identifiers appear in code font.

The design is frozen in `docs/preregistration-v2.md`. The code implements it. The earlier design is the git tag `v1-worldbank-moments`.

Sections 1 to 5 cover the model, targets, images, foils, non-claims, and `nroy_param_spread`. Section 6 lists outputs and the environment. Sections 7 and 8 describe amendments A1 and A2.

## 1. The model

### 1.1 The world

The world is the graph plus the covariates. It is the class `kernel.World`. It is drawn once, and every simulation shares it.

- The number of people is $N = 800$ (`N_AGENTS`).
- The edge rule draws $A_{ij} \sim \text{Bernoulli}(p)$ with $p = 4/N$ (`EDGE_P`) for every ordered pair. Then the graph is symmetrized, $A \mid A^\top$, and the diagonal is set to zero. There are no self-loops.
- So $P(\text{edge}) = 1 - (1-p)^2 \approx 8/N$. The value 4 in $p = 4/N$ is the rate per ordered pair. The mean degree is about 8: 7.97 in theory and 8.085 measured on this world.
- The global clustering coefficient of this graph is 0.0096: 3 × triangles / connected triples, with 83 triangles and 25,918 connected triples. A random graph has the edge probability, 0.0100, in expectation. The graph is locally tree-like. `scripts/write_numbers.py:graph_facts` computes both numbers.
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
| offsets 0 to 29 | `REPS_MOMENT` = 30 | the moments M(c), on the control and random arms |
| offsets 0 to 199 | `REPS_ESTIMAND` = 200 | the estimands, the targets z, the gap decomposition |
| offset 0 | `FOIL_PANEL_OFFSET` | the one panel each foil sees |
| offsets 100000 to 100199 | `RECHECK_OFFSET` | the endpoint recheck |
| seeds 1,000,000 and up | `GATE_SEED` | the assignments of the Foil 2 calibration check |
| seeds 10,000 and up | in `check_foil2_coverage.py` | the assignment-only redraws of the check |
| seed 20261020 | `BOOT_SEED` | the bootstrap of the check |
| offsets 2,000,000 to 2,000,199 | `INTERFERENCE_OFFSET_BASE`, `INTERFERENCE_REPETITIONS` | the A2 repeated panels |

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

History matching is calibration, not estimation. There are five free parameters and four moments. The model is underidentified on purpose. The question is which policy effects remain possible, not which $c$ is true.

### 2.1 The planted targets

- The planted point is $c^* = $ the center of C (`C_STAR`, JSON key `c_star`).
- The targets are $z = \hat M(c^*)$, the moments at $c^*$ over 200 reps (`REPS_Z`). They are stored in `data/planted.json`. They are what a researcher could observe: the village in the status quo, plus one randomized pilot. The degree arm, which is the policy to predict, is never a target.
- The function `moments.plant_and_freeze(world, path)` writes the file. The loader is `moments.load_frozen_z`.
- The file has the keys `design` (the text `preregistration-v2`), `c_star`, `z`, `sampling_variances`, `reps_z` and `moment_names`. The key `sampling_variances` holds the Monte Carlo variances of the 200-rep mean, one per moment.
- `scripts/plant_z.py` regenerates the file. By default it only checks. The regenerated copy reproduces `data/planted.json` byte for byte.

### 2.2 The moments

The function `moments.simulate_moments(world, c, reps=30)` returns the moments $M(c)$ and their Monte Carlo variances $\sigma^2_{MC}$. It uses $R_m = 30$ paired reps (`REPS_MOMENT`). Rep $r$ of the control arm and of the random arm use `seed_offset` $r$, so they share the state stream. The degree arm is not simulated here. The order of `MOMENT_NAMES` is frozen.

| # | Slot (`MOMENT_NAMES`) | Definition | Arm |
|---|---|---|---|
| 1 | `sq_level` | mean $\bar Y_T$ over people | control |
| 2 | `sq_corr_x1` | corr($Y_T$, x1) over people, x1 = `world.X[:, 0]` | control |
| 3 | `sq_peer_corr` | corr($Y_{T,i}$, $(W Y_T)_i$) over people, with $W$ = $A$ / degree | control |
| 4 | `pilot_level` | mean $\bar Y_T$ over people | random |

The function `moments.peer_correlation(world, y)` computes the third moment. It uses `adjacency @ y / degrees`, which is the peer mean of the kernel. It returns nan if $y$ or the peer mean is constant.

The target value of `sq_peer_corr` is 0.0003, close to zero, and its $\delta$ is 0.05. So this moment is a weak constraint: its entry of $V$ is dominated by $\delta^2$.

With paired reps, `pilot_level` − `sq_level` at $c^*$ equals $\theta_1(c^*)$ exactly. This is intended: a randomized pilot identifies $\theta_1$. The question is whether the model can extrapolate from it to $\theta_2$. The committed values agree: both are 0.03631. A test checks the identity (`tests/test_moments_hand_examples.py`).

The variance $\sigma^2_{MC}$ is the sample variance of the per-rep values (ddof = 1) divided by $R_m$. The code drops non-finite correlations. If fewer than two values remain, the variance is infinite, and $I$ rejects the point.

### 2.3 Implausibility

The function `moments.implausibility(z, m_hat, v_diag)` computes

$$I(c) = (z - \hat M)^\top V^{-1} (z - \hat M), \qquad V = \text{diag}\big(\sigma^2_z + \sigma^2_{MC}(c) + \delta^2\big)$$

- $\sigma^2_z$ is `sampling_variances` from `data/planted.json`.
- $\delta = (0.02, 0.05, 0.05, 0.02)$ is the discrepancy, in the order of the moments: 0.02 for levels and 0.05 for correlations (`DELTA`, `discrepancy()`). The values are in `config/design.toml`, one per moment name. The number of moments is the number of names there.
- The function `v_diag_of(sampling, mc)` builds the diagonal of $V$.
- The threshold is $\tau = \chi^2_{0.95}(4) = 9.4877$ (`history_matching.tau_threshold`, `HM_CONFIDENCE`, `N_MOMENTS`). The degrees of freedom are the number of moments. The code keeps a point if $I \le \tau$.
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

F-SINGLETON is only a flag. The code does not widen anything. In the committed run `finding_hm` is `null`. The kept counts are 181, 449 and 408, and NROY has 1,038 points.

## 3. Images and the two foils

### 3.1 The images

The function `pipeline.run_poc("planted")` samples 400 NROY points uniformly without replacement (`THETA_SAMPLE`, `sample_nroy_index`, seed `SEED_THETA_SAMPLE`). At each point it evaluates theta2 and delta_spill with 200 reps. The image is the range over the sample (`interval_image`):

- Theta_hm = [min, max] of theta2. It is $[0.00577, 0.07369]$.
- Theta_exp = [min, max] of delta_spill. It is $[-0.000578, 0.026525]$.

The file `results/planted/image_points.json` stores every point. Each record has `nroy_index`, `I`, `c`, `theta2`, `se_theta2`, `delta_spill` and `se_spill`. The image is not a posterior.

### 3.2 The endpoint recheck

The function `pipeline.recheck_extremizers` evaluates each point that sets an endpoint again. It uses 200 fresh reps on the stream offsets 100000 to 100199 (`RECHECK_OFFSET`). The result is the JSON key `endpoint_recheck`. Each candidate has `pilot_value`, `pilot_pointwise_se`, `fresh_value` and `fresh_pointwise_se`.

| Endpoint | NROY index | Pilot (SE) | Fresh (SE) |
|---|---|---|---|
| Theta_hm lower | 293 | +0.005771 (0.000008) | +0.005772 (0.000007) |
| Theta_hm upper | 832 | +0.073692 (0.000006) | +0.073697 (0.000006) |
| Theta_exp lower | 987 | −0.000578 (0.000505) | +0.000200 (0.000494) |
| Theta_exp upper | 674 | +0.026525 (0.000613) | +0.027542 (0.000601) |

Required wording (verifier `t_1f00fc3b`):

> Each bar in `image_points.json` is a pointwise Monte Carlo SE conditional on a fixed parameter point c. The displayed image endpoints are extrema selected from 400 noisy estimates. So the SE attached to the extremizing point is not an SE for the endpoint. It does not include extremum-selection uncertainty. Fresh independent re-evaluation of the pilot-selected extremizers removes reuse-of-noise bias for those candidates. It is not simultaneous inference for the true extrema.

### 3.3 The three points

The pipeline works at three points. They are the keys `min_I`, `median_I` and `c_star` of `findings`.

- The calibrator fits the model and works at one best-fitting point. The function `estimand.diagnostic_worlds(nroy, I)` sorts NROY by $I$ with a stable sort. The min-I point is the first. The median-I point is the one at position `len(I) // 2`. Both depend on $I$ only, never on theta2. We write $c_0$ for either point.
- The field experimenter has one panel from the real village. This is the planted point $c^*$. The truth at $c^*$ is `theta_star` and `spill_star`, computed once per run.

The min-I point has NROY index 812 and $I = 0.0141$. Its parameters are $\alpha = -1.5956$, $\beta = 0.4709$, $\gamma = 0.6853$, $\kappa = 1.2496$ and $\sigma_\varepsilon = 0.2150$.

The median-I point has NROY index 351 and $I = 3.3437$. Its parameters are $\alpha = -1.4491$, $\beta = 0.3428$, $\gamma = 0.5234$, $\kappa = 1.9202$ and $\sigma_\varepsilon = 0.2051$.

The $c^*$ point has no `I` and no `nroy_index` in the file. The code does not evaluate $I(c^*)$.

### 3.4 Foil 1: the SUTVA analyst

Foil 1 uses the degree arm and one panel (offset 0). The functions are `diagnostic.foil1_policy` and `diagnostic.ols_ate_hc1`.

1. Fit OLS of Y on $[1, D, X]$. The coefficient on $D$ is the OLS coefficient beta-hat. The interval is beta-hat $\pm$ 1.96 SE, with an HC1 standard error: the sandwich times $n/(n-5)$.
2. Read the share $k/N$ from the panel. It is 0.1.
3. The SUTVA analyst's policy estimate is $(k/N) \cdot \hat\beta$. The interval is the HC1 interval scaled the same way.
4. Compare the scaled interval with Theta_hm.

The scaling by a known positive constant keeps the analyst's own coverage statement. It does not repair the analyst's assumptions. The JSON keys are `foil1_estimator`, `foil1_beta`, `foil1_ci_beta`, `foil1_share`, `foil1_ci`, `foil1_vs_Theta_hm`, `foil1_covers_truth`, `foil1_covers_planted_truth` and `foil1_gap_decomposition`. The truth at the point is `theta2_true`. The planted truth is `theta_star.theta2`.

Five statements must stay with every report of Foil 1 (verifiers `t_2b7a8d8c` and `t_1f00fc3b`):

1. Foil 1 is not an identified estimator of the simulator's θ2 under the actual interference model. It is the whole-village policy estimate implied by a SUTVA analyst, (k/N)·beta-hat, with k/N = 0.1.
2. That interpretation assumes consistency/SUTVA, conditional exchangeability and positivity given X, a correctly specified additive constant-effect outcome model, and a sampling/asymptotic basis for HC1. The deterministic top-degree assignment does not establish those assumptions.
3. After scaling, the Foil 1 intervals are strictly inside Theta_hm and exclude the truth at their own point and the planted truth, at all three points. So F-OVERCONF is an assumption-contingent interval-geometry finding. It is not a coverage claim for θ2 under interference.
4. Across 200 paired panels, about 90% of the gap between θ2 and (k/N) times the 200-panel mean OLS coefficient is the policy effect on unseeded people. For the displayed replication-0 point estimate, the corresponding shares are about 93% at min-I, 92% at median-I and 95% at c*.
5. The rescaling was adopted in the v1 design, after the v1 numbers were inspected. Its justification is the SUTVA aggregation identity. The post hoc design correction is disclosed. The v2 code keeps it unchanged.

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

| | min-I point | median-I point | c* |
|---|---|---|---|
| theta2 | 0.03933 | 0.05642 | 0.03826 |
| seeded part | 0.03224 | 0.04824 | 0.03396 |
| unseeded part | 0.00709 | 0.00818 | 0.00430 |
| seeded policy contrast | 0.3224 | 0.4824 | 0.3396 |
| mean beta | 0.3146 | 0.4735 | 0.3350 |
| gap for the mean beta | 0.00787 | 0.00907 | 0.00477 |
| unseeded share (mean beta) | 0.9015 | 0.9015 | 0.9028 |
| OLS-error part (mean beta) | 0.00078 | 0.00089 | 0.00046 |
| gap for the displayed beta | 0.00762 | 0.00890 | 0.00454 |
| unseeded share (displayed beta) | 0.9308 | 0.9185 | 0.9488 |
| baseline gap | 0.0007 | 0.0008 | 0.0007 |

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
8. Compare the interval for delta_spill = S0c − S0a with Theta_exp. The truth at the point is `spill_true`. The planted truth is `spill_star.delta_spill`.

The JSON keys are `foil2_estimate`, `foil2_se`, `foil2_merged_s0b`, `foil2_ci`, `foil2_vs_Theta_exp`, `foil2_covers_truth` and `foil2_covers_planted_truth`. The function also returns delta_dir and its interval (`ci_dir`). An earlier version (commit `ebed7ce`) used a first-order variance that dropped the covariance between the strata. Commit `36ed3e6` replaced it.

### 3.7 Verdicts and covers_truth

The function `diagnostic.classify_interval(interval, image)` compares an interval $[lo, hi]$ with its own image $[L, U]$.

- F-HONEST if the interval covers the image: $lo \le L$ and $hi \ge U$.
- F-OVERCONF if the interval lies strictly inside the image: $lo > L$ and $hi < U$.
- Otherwise there is no verdict (`None`). The same holds if any end is not finite.

Each foil is judged against its own image. Foil 1 goes against Theta_hm. Foil 2 goes against Theta_exp.

The function `diagnostic.covers_truth(ci, truth)` is true if the truth lies inside the interval. The function `diagnostic.containment_flags` returns four flags for one point:

- `foil1_covers_truth` and `foil2_covers_truth`: the truth at the point itself, theta2(c) and delta_spill(c). The question is whether the estimator is right about its own world.
- `foil1_covers_planted_truth` and `foil2_covers_planted_truth`: the truth at c*, theta2(c*) and delta_spill(c*). The question is whether the report is right about the real village.
- At $c^*$ the two pairs are equal.

Required wording:

> At each of the three points, covers_truth reports whether the displayed interval contains that point's own simulator truth, and covers_planted_truth whether it contains the truth at c_star (the two coincide at c_star). Both are descriptive containment indicators for one realized panel, not estimates of repeated-sampling coverage and not validity gates. Foil 2 is checked separately by the pre-declared repeated-assignment calibration in scripts/check_foil2_coverage.py.

The committed results:

| | min-I point | median-I point | c* |
|---|---|---|---|
| Foil 1 interval | [0.03057, 0.03285] | [0.04664, 0.04840] | [0.03267, 0.03479] |
| Foil 1 verdict | F-OVERCONF | F-OVERCONF | F-OVERCONF |
| Foil 1 contains the point truth | no | no | no |
| Foil 1 contains the planted truth | no | no | no |
| Foil 2 estimate (SE) | 0.01330 (0.00526) | 0.01587 (0.00524) | 0.00812 (0.00486) |
| Foil 2 merged S0b | no | no | no |
| Foil 2 interval | [0.002988, 0.023619] | [0.005598, 0.026135] | [−0.001405, 0.017638] |
| Foil 2 verdict | F-OVERCONF | F-OVERCONF | no verdict |
| Foil 2 contains the point truth | yes | yes | yes |
| Foil 2 contains the planted truth | yes | yes | yes |

### 3.8 The Foil 2 verdicts and the endpoint recheck

Required wording (verifier `t_7afcff9b`, updated to the v2 numbers):

> Against the saved 200-rep pilot image, Theta_exp = [−0.000578, 0.026525], the min-I Foil 2 interval [0.002988, 0.023619] and the median-I Foil 2 interval [0.005598, 0.026135] are strictly interior and are therefore classified F-OVERCONF. That classification depends on endpoints that are extrema selected from 400 noisy estimates. An independent 200-rep recheck of the pilot-selected lower-end candidate is +0.000200 (pointwise MC SE 0.000494), and of the upper-end candidate is +0.027542 (pointwise MC SE 0.000601). Both intervals stay strictly inside the range between these two fresh values. The recheck evaluates selected candidates. It neither identifies nor bounds the true extrema over all 400 sampled NROY points. The Foil 2 interval at c* is not strictly inside the image, so it has no verdict.

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
| min-I | 0.925 | 0.9267 |
| median-I | 0.920 | 0.9267 |

The kernel does not obey the exposure map exactly, because the spillover also travels two steps. So kernel coverage below 95% is a finding about Foil 2. The script exits with code 1 if the gate fails. It stops at once if `results/planted/poc_results.json` does not exist.

Required wording:

> In a fixed-world repeated-assignment check whose outcomes obey the exposure map exactly, the nominal 95% Foil 2 Wald interval covered 93.4% of assignments (exact 95% binomial interval 92.9%–93.9%). The average estimated variance was 1.034 times the empirical design variance, so the shortfall is not explained by average variance underestimation. It reflects the finite-sample behavior of this studentized normal interval, with the implemented Hájek linearization and simulated joint exposure probabilities.

The check is implementation-specific. It does not test the theorem of Aronow and Samii. Their exact result is for Horvitz–Thompson totals with exact joint probabilities. The code uses Hájek means, a first-order linearization, and one simulated table of joint probabilities.

## 4. What the project does not claim

- Theta_hm is not a posterior. It is not a Manski/Tamer identified set. It comes from a thresholded discrepancy. Sampling noise is folded into V. The kernel is taken as true. The image shares the reporting logic of a set, so do not collapse it to a point.
- The closest NROY point ($I = 0.0141$) does not recover $c^*$. Fit does not pick the truth.
- F-OVERCONF for Foil 1 is about interval geometry under the analyst's assumptions. It is not a coverage claim.
- The `covers_truth` and `covers_planted_truth` flags describe one realized panel. They are not repeated-sampling coverage.
- The sampled image can understate the true NROY image. The three waves are finite.
- The threshold $\tau$ is not a test level. $V$ is diagonal, but the four moments are not independent: the control and random level moments share a state stream. And $\delta^2$, not the sampling variance, fills $V$. So $\tau$ is a heuristic tolerance, not the critical value of a test.
- The foils' panel (offset 0, rep 0) is also one of the 200 reps whose mean defines $z$. The foils see data that helped set the targets. The pipeline was not rerun without rep 0.
- Foil 2 and its truth are not the same estimand. `estimand.hajek_contrasts` targets the inverse-probability exposure contrast. `estimand.evaluate_spill` averages the unweighted realized stratum contrasts. On this run no containment flag depends on the difference. This was not tested on another kernel.
- The width of $\Theta_{hm}$ is largely the assumption $\delta$, not the count of moments. The level allowance, $\sqrt{\tau\delta_1^2}$, is larger than $\theta_1(c^*)$, so the pilot cannot pin $\kappa$. Section 7 (amendment A1) shows how the image changes with $\delta$.
- The project has one planted world, one graph, and one set of targets. It claims no external validity.

## 5. The readout nroy_param_spread

The function `pipeline.nroy_param_spread(image_points, param_names)` is a descriptive readout. It is not a gate. For each parameter it computes the standard deviation (ddof = 1) over the 400 sampled NROY points, divided by the standard deviation of a uniform draw over C on that axis, which is span / $\sqrt{12}$. It also computes the correlation matrix of the parameters over the same points. The pre-registration does not state ddof. The code uses 1. A ratio near 1 means the moments do not restrict that parameter.

The JSON key is `nroy_param_spread` in `results/planted/poc_results.json`. It has `param_names`, `n_points`, `sd_sampled_nroy`, `sd_uniform_box`, `sd_ratio` and `correlation_matrix`.

| Parameter | alpha | beta | gamma | kappa | sigma_eps |
|---|---|---|---|---|---|
| `sd_ratio` | 0.259 | 0.965 | 0.992 | 0.962 | 0.839 |

Only alpha is strongly restricted. The ratio for gamma is 0.992, so the moments do not restrict gamma. The pre-registration expected a gamma ratio below 1 from `sq_peer_corr`. That expectation was not met: a ratio of 0.992 is no restriction. The largest correlations are alpha with gamma (−0.345) and alpha with kappa (−0.305). The code reports these numbers. It does not gate on them.

## 6. Outputs per script, and the environment

| Command | Reads | Writes |
|---|---|---|
| `python scripts/plant_z.py` | `data/planted.json` | `results/checks/planted_regenerated.json` (a scratch copy). Exit 0 if the bytes match, exit 1 if not. With `--write` it overwrites `data/planted.json`. |
| `python scripts/run_poc.py planted` | `data/planted.json` | `results/planted/poc_results.json`, `results/planted/image_points.json`, `figures/planted/waves.png`, `figures/planted/image_points.png`, `figures/planted/overlay.png`, `locks/freeze-planted.txt`. If NROY is empty it draws `figures/planted/empty.png` instead of the last two. |
| `python scripts/check_foil2_coverage.py` | `results/planted/poc_results.json` | `results/checks/foil2_coverage.json` |
| `python scripts/delta_menu.py` | `data/planted.json`, `results/planted/poc_results.json` | `results/sensitivity/delta_menu.json` (amendment A1, section 7) |
| `python scripts/interference_tradeoff.py` | `results/planted/poc_results.json` | `results/interference/tradeoff.json` (amendment A2, section 8) |
| `python scripts/replicate.py [--quick]` | everything below | all outputs and a comparison with git HEAD. `--quick` skips the Foil 2 check and amendments A1/A2. |
| `python scripts/sync_writeup_figures.py` | `figures/` | figure copies in `writeup/figures/` and `thesis/figures/` |
| `python scripts/write_numbers.py` | `config/`, `results/`, the drawn graph | byte-identical `writeup/numbers.tex` and `thesis/numbers.tex` |
| `python scripts/draw_figures.py planted` | saved JSON results | all planted figures, including `tradeoff.png`. It runs no simulation. |

The file `poc_results.json` has these keys: `git_commit`, `ran_at`, `z_source`, `z`, `z_names`, `sampling_variances`, `delta`, `tau`, `finding_hm`, `wave_kept`, `wave_I_stats`, `closest`, `n_nroy`, `param_names`, `c_star`, `theta_star`, `spill_star`, `notes` and `figures`. The run adds `Theta_hm`, `Theta_exp`, `n_theta_sample`, `nroy_param_spread`, `endpoint_recheck` and `findings` (the keys `min_I`, `median_I` and `c_star`). The key `git_commit` is the HEAD hash of the code, with `+dirty` if `config/`, `src/`, `scripts/`, `data/` or the requirements files differ from it.

The run also stores `theta_star` and `spill_star`, the truth at $c^*$: theta1 = 0.03631, theta2 = 0.03826, premium = 0.00195, and delta_spill = 0.00792.

The pins are Python 3.14, numpy 2.5.4, scipy 1.18.1, matplotlib 3.11.2 and pytest 9.1.1 (before 2026-10-22: Python 3.11, numpy 2.4.6, scipy 1.15.3, matplotlib 3.10.3 and pytest 8.4.2; see the README). Every v2 result was produced on the new pins. The pipeline calls `uv pip freeze` to write `locks/freeze-*.txt`, so `uv` must be on the path. The tests are in `tests/`. There are 72 tests, and all 72 pass. `writeup/main.tex` and `writeup/cover.tex` use only the three synced figures; the paper no longer cites `empty.png`.

## 7. Amendment A1: the delta menu

Amendment A1 is at the bottom of `docs/preregistration-v2.md`. It was written after the v2 results were known, and the pre-registration says so. It does not test a hypothesis. It reports how the image depends on one assumption: the discrepancy delta of the two level moments. The main design and every headline result stay at delta = 0.02.

**The menu.** The script `scripts/delta_menu.py` takes delta for `sq_level` and `pilot_level` from {0.02, 0.01, 0.005}. The entries are named Main, Half and Quarter. The two correlation moments keep delta = 0.05. The threshold tau, the box C, the moments, the targets z, every seed and `REPS_MOMENT` do not change. The file `config/design.toml` is never edited.

**How delta is passed.** The functions `moments.discrepancy`, `moments.v_diag_of` and `history_matching.run_waves` take an optional argument `delta`, a dict from moment name to delta. The default is `config.DELTA`, so every existing call behaves as before. A test checks this.

**What is rerun for each entry.** The waves (`run_waves`, same seed), NROY, the 400 sampled points (`SEED_THETA_SAMPLE`), Theta_hm, Theta_exp and `nroy_param_spread`. The script uses the pipeline's own functions for each of these. It reports `finding_hm`, `wave_kept`, `n_nroy`, both images, the spread ratios and the alpha–kappa correlation. An empty NROY (F-EMPTY) is reported as found. Such an entry has no images.

**The foils.** The foils are not rerun. The intervals of the field experimenter at c* do not depend on delta. The script reads them from `results/planted/poc_results.json` and classifies them with `classify_interval` against each entry's Theta_hm (Foil 1) and Theta_exp (Foil 2). The points of the calibrator (min-I, median-I) move with delta. They are not rerun, because that would be a new design.

**The consistency check.** The Main entry must equal the main run in `delta`, `tau`, `Theta_hm`, `Theta_exp`, `n_nroy`, `wave_kept` and `nroy_param_spread`, exactly. If one differs, the script exits with an error and writes no file. This check passed in the committed run.

**Output.** `results/sensitivity/delta_menu.json` has the keys `git_commit`, `ran_at`, `amendment`, `moment_names`, `level_moments`, `main_entry`, `consistency_check`, `c_star_foil_intervals`, `entries` and `notes`. Each entry has `delta_level`, `delta` (four numbers, in the order of `moment_names`), `tau`, `finding_hm`, `wave_kept`, `n_nroy`, `param_names`, `n_theta_sample`, `Theta_hm`, `Theta_exp`, `nroy_param_spread`, `alpha_kappa_corr`, `foil1_vs_Theta_hm` and `foil2_vs_Theta_exp`.

**Macros.** `scripts/write_numbers.py` writes `\MenuDelta<Entry><Item>` to `writeup/numbers.tex`. The entry is Main, Half or Quarter. The items are `Level`, `Finding`, `NNroy`, `ThetaHmLo`, `ThetaHmHi`, `ThetaExpLo`, `ThetaExpHi`, `SpreadRatioAlpha`, `SpreadRatioKappa`, `SpreadRatioGamma`, `FoilOneVerdict` and `FoilTwoVerdict`. Example: `\MenuDeltaHalfThetaHmLo`. The existing macros are unchanged.

**Run time.** About 6 minutes per entry, and about 18 minutes for the menu. `replicate.py` runs it as step 5 and skips it with `--quick`.

**What the menu is not.** It is not a test and not a way to choose delta. It shows the answer under each assumption, in the spirit of Tamer (2010). The numbers are in the JSON file and in `numbers.tex`.

## 8. Amendment A2: three analysts for theta2

Amendment A2 is at the bottom of `docs/preregistration-v2.md`. It was written after the v2 and A1 results were known. The amendment asks about the cost of weaker interference assumptions. All three analysts report an interval for theta2.

**The general contrast.** `estimand.hajek_linear_contrast` takes exposure cells and coefficients. A cell can also have a fixed node mask. The function computes the weighted sum of the Hájek means. It uses exact first-order exposure probabilities and the cached simulated joint probabilities. A node mask sets probabilities to zero outside its fixed set. The variance sums every pairwise linearized Aronow–Samii covariance. The panel uses the same S0b merge rule as `hajek_contrasts`.

**A0.** The script calls `diagnostic.foil1_policy`. Thus A0 is the existing Foil 1 implementation. It does not duplicate the OLS-HC1 code.

**A1.** `analyst_a1` uses the random-arm panel. Its weights are exposure shares under the deterministic degree assignment. If the panel merges S0b, the degree-policy shares use the same merged labels.

**A2.** `analyst_a2` uses the same exposure strata. It also fixes two graph bins. H contains the people seeded by the degree policy. L contains all other people. The function never merges H with L. If a required observed cell is empty, the estimate and interval are undefined. The repeated-panel summary counts these panels and does not impute them.

**Evaluation.** `scripts/interference_tradeoff.py` reads the points, truths, and Theta_hm from the main saved result. It does not rerun the waves. The one-panel readout uses `FOIL_PANEL_OFFSET`. The repeated readout uses `INTERFERENCE_REPETITIONS` fresh offsets from `INTERFERENCE_OFFSET_BASE`.

The repeated readout reports the mean, bias, SD, RMSE, mean SE, SE/SD, and coverage. It also reports an exact Clopper–Pearson 95% interval, mean width, width ratio, and the undefined count. The denominator for A2 statistics is the number of defined panels.

**Output and figure.** The JSON file is `results/interference/tradeoff.json`. The function `figures.draw_tradeoff` reads this file through `scripts/draw_figures.py`. It plots absolute bias against mean width. Coverage appears beside each marker. A vertical line shows the width of Theta_hm.

**Macros.** `scripts/write_numbers.py` uses `\Tradeoff<Point><Analyst><Item>`. Point is MinI, MedI, or Star. Analyst is AZero, AOne, or ATwo. One-panel item names start with OnePanel. The other item names are the repeated-panel readouts. Existing macro names do not change.

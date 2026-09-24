# METHODOLOGY.md — the formal blueprint (single source of truth)

Every numbered object here is frozen BEFORE any wave runs. The Python engine
must reproduce these objects exactly. If code and this document disagree, the
document wins and the code is a bug.

**Freeze date:** 2026-08-26, amended 2026-08-27 (AMENDMENT-02: planted \(z\)).
**In scope for 2026-12-01:** Python engine through the overlay figure (A1–A7).
**Out of scope for December:** NetLogo twin (B1–B3); BCF unless Hahn asks.
**WB country totals:** F-EMPTY archive only; not an input to \(I(c)\) after AMENDMENT-02.

---

## 1. Population

- N = 800 agents, i ∈ {0..N−1}.
- Graph: Erdős–Rényi G(N, p), p = 4/N, drawn once with seed `SEED_GRAPH`.
  Undirected; adjacency A ∈ {0,1}^{N×N}; degree k_i = max(row-sum, 1).
- Covariates X_i ∈ [0,1]^3, uniform, seed `SEED_X`:
  - x1 = education proxy
  - x2 = resource/wellbeing proxy
  - x3 = baseline propensity

## 2. Kernel (linear-in-means with logistic saturation)

For t = 0..T−1:

    Y_i(t+1) = Λ( α + β·Y_i(t) + γ·(Σ_j∈N(i) Y_j(t))/k_i
                  + η·X_i + κ·D_i·1{t ≥ t*} + ε_i(t) )

    Λ(z) = 1/(1+exp(−z)),   ε_i(t) ~ N(0, σε²)

- T = 20, t* = 0.
- Y(0): uniform[0,1] per agent, seeded by the run seed.
- Parameter box C (frozen):
  - α ∈ [−2.5, −0.5]
  - β ∈ [0.05, 0.60]     (persistence)
  - γ ∈ [0.05, 0.80]     (peer influence; γ=0 NOT in the box — see §7 note)
  - κ ∈ [0.25, 2.50]     (targeting strength)
  - η = (0.05, 0.10, 0.02) FIXED — not calibrated
  - σε ∈ [0.01, 0.40]

Five free coordinates, three moments (§6). Underidentification is intended:
the deliverable is a set in c, not a point.

## 3. Assignment rules (three arms)

- π₀ control: D = 0 for all agents.
- π₁ random: D = 1 on n = ceil(0.10·N) = 80 uniformly sampled agents
  (SRSWOR). This arm has a design (known inclusion probabilities).
- π₂ degree: D = 1 on the 80 highest-degree agents (ties by index).
  Deterministic given A — no design-based estimator reaches this arm.

## 4. Estimands

    θ₁(c) = E_c[Ȳ_T | π₁] − E_c[Ȳ_T | π₀]
    θ₂(c) = E_c[Ȳ_T | π₂] − E_c[Ȳ_T | π₀]        ← HEADLINE
    τ(c)  = θ₂(c) − θ₁(c)                         ← targeting premium

Expectations over simulation noise ω only (π₀ and π₂ are deterministic given A;
π₁'s extra randomness is part of ω). Estimated by Monte Carlo with R = 200
paired reps per arm per c.

## 5. Anchors (AMENDMENT-02 — planted \(c^\star\); village narrative)

The DGP *is* the kernel. \(z\) is not an external country series. A single
large village (\(N=800\)) has an acquaintance network \(G(N,4/N)\). \(Y_{i,t}\)
is preventive-practice intensity in \((0,1)\). Covariates: \(x_1\) health
literacy, \(x_2\) resources, \(x_3\) baseline propensity. Campaigns seed 80
households (\(\pi_1\) random, \(\pi_2\) highest-degree infuencers, \(\pi_0\)
none).

| # | Village functional | slot name (historical) |
|---|--------------------|------------------------|
| z1 | mean \(\bar Y_T\) under \(\pi_2\) (hub campaign) | level_imm |
| z2 | \(\mathrm{corr}(Y_T,x_1)\) under \(\pi_2\) (literacy gradient) | gradient_edu |
| z3 | mean \(\bar Y_T\) under \(\pi_1\) (random campaign) | level_internet |

**Plant:** \(c^\star =\) center of \(C\),
\((\alpha,\beta,\gamma,\kappa,\sigma_\varepsilon)=(-1.5,\,0.325,\,0.425,\,1.375,\,0.205)\).
Chosen as midpoints of the already-frozen box — not by looking at \(\theta\).

**\(z := \widehat M(c^\star)\)** with \(R_z = 200\) paired reps, frozen in
`data/planted.json` before waves. Units are already \([0,1]\) (no \(\times 0.01\)).

**Sampling variances of \(z\):** Monte Carlo variances of that 200-rep mean
(diagonal), stored next to \(z\). They replace the World Bank
\((sd)^2/n\) and Pearson formulas.

The 2026-08-12 World Bank fetch remains in `data/anchors.json` as the F-EMPTY
archive of the previous pair \((f,z_{\mathrm{WB}})\). It does not enter \(I(c)\).

z = (z1, z2, z3) is **three-dimensional**.

## 6. History matching

- Design: Latin Hypercube over C via numpy Generator(seed=SEED_HM), 1000 points/wave.
- Moments M(c): run all three arms R_m = 30 times at c; record
  m1 = mean Ȳ_T under π₂, m2 = corr(Y_T, x1) under π₂, m3 = mean Ȳ_T under π₁.
  M̂(c) = per-arm means across reps.
- Implausibility I(c) = (z − M̂(c))ᵀ V⁻¹ (z − M̂(c)),
  V = diag(σ²_sampling(z) + σ²_MC(M̂) + δ²).
- Sampling variances (AMENDMENT-02): the frozen Monte Carlo variances of
  \(\widehat M(c^\star)\) in `data/planted.json`.
  \(\sigma^2_{\mathrm{MC}}\) from the \(R_m\) replications at the candidate \(c\), diagonal.
- Discrepancy budget δ (frozen, same units as z):
  δ = (0.02, 0.05, 0.02)
  i.e. 2 pp on each level after rescaling, 0.05 on the correlation.
- Threshold τ = chi2.ppf(0.95, df=3).
- Waves: 3. Each wave keeps points with I ≤ τ, fits nothing (no emulator —
  direct evaluation only), draws the next LHS concentrated around survivors'
  bounding box inflated 20%.
- NROY = union of surviving points after wave 3.

## 7. Identified set (not-ruled-out image)

Θ_hm = { θ₂(c) : c ∈ NROY }, reported as empirical [L, U] over survivors,
with MC error bars on each θ̂(c_s). S sampled uniformly from NROY, S = 400.
The draw traces the image; it is not a posterior and not a uniform credibility
claim on worlds.

Θ_exp = { δ_spill(c) : c ∈ NROY }, same reporting, same S
(δ_spill defined in §9). Computed from stratum means already recorded during
moment / estimand passes — no extra kernel family.

Design guards:
- If |NROY| = 0 → finding F-EMPTY (reject (f,z)); do not touch τ or δ.
- If NROY collapses (bounding box < 5% of original volume per axis) →
  design failure F-SINGLETON; widen ONE declared coordinate before week gate.
- γ range deliberately excludes 0: the paper is ABOUT interference; a
  no-interference world surviving calibration would be its own finding but
  must not be silently included.

Language: Θ_hm is a **not-ruled-out image**, reported with the same logic as a
Manski set (do not replace it by a point). It is not claimed to be a Manski
identified set (thresholded discrepancy, sampling folded into V, complete kernel).

## 8. Measurement layer (minimal)

Observed scores s_j generated from true Y_T at each diagnostic world c₀:

- m₁ oracle: s = Y_T                       (planner sees truth — positive control)
- m₂ survey:  s = clip(Y_T + N(0, 0.15²))  (admissible)
- m₃ bad-item: s = clip(0.5·Y_T + 0.5·x3 + N(0, 0.10²))
  → fails the pre-declared restriction "measure must not load on treatment-
  channel covariates": |corr(s₃, x3)| > 0.5 threshold → EXCLUDED from M*.

M* = {m₁, m₂}. Θ_cv(c₀) = image of θ₂ over admissible measures at that c₀.
This screens **measures**, not NROY points.

## 9. Diagnostic (two foils, two worlds)

**Worlds.** Two pre-declared selections from NROY, both functions of I only
(never of θ):

- c₀^min  = surviving point with smallest I(c)     (best match; “staff model”)
- c₀^med  = surviving point with median I(c)       (non-extremal)

Report a separate overlay for each. Do not pick one after seeing θ.

**Foil 1 — SUTVA / gold-standard one-world interval.**
econml `CausalForestDML`, honest CIs, seed `SEED_CF`. Fitted on the simulated
panel at that c₀ (D from π₂, features X, outcome s from each m ∈ M*).
Reports I_BCF — named historically; the implementation is the forest, not BCF.
BCF (Hahn–Murray–Carvalho) is **not** required for December; add via rpy2 only
if Hahn asks, as an extra row, same worlds, no new c₀ rule.

The forest estimates a SUTVA functional at one world. It is the ruler for
one-world practice, not a candidate for Θ_hm.
If CausalForestDML cannot import against the pinned numpy, the same role is
filled by OLS of \(s\) on \(D\) given \(X\) with HC1 intervals (AMENDMENT-02).
Report the estimator name; do not call the fallback BCF.

**Foil 2 — exposure-mapped Hájek (AMENDMENT-01, accepted 2026-08-26).**
Lives on π₁ (the only arm with a design). π₂ is deterministic; no design-based
estimator reaches the headline assignment. That fact is reported, not walked around.

- Exposure: g_i = (D_i, s_i), s_i = (Σ_{j∈N(i)} D_j) / k_i.
- Frozen strata: S1: D=1; S0a: D=0, s=0; S0b: D=0, 0<s<0.25; S0c: D=0, s≥0.25.
- Cell-size guard: if any stratum has < 20 agents in a replication, merge S0b
  into S0c for ALL replications of that world and log it.
- δ_dir = Hájek mean(S1) − mean(S0a); δ_spill = mean(S0c) − mean(S0a)
  (δ_spill is the E2 overlay headline).
- Variance: randomization-based Hájek under SRSWOR, exact second-order
  inclusions; conservative variant preferred.
- Appendix robustness (declared now): recompute strata with threshold 0.5;
  report whether F-*_E2 flips.

Each foil interval is judged against **its own** image: I_BCF vs Θ_hm vs
θ_true(c₀); I_E2 vs Θ_exp vs δ_spill,true(c₀).

**Oracle gate (not a finding):** at m₁, if E2's point estimate misses
δ_spill,true(c₀) beyond its CI, the harness is broken — stop, fix, re-run.

**Seeds.** Run streams use explicit integer offsets from `SEED_RUN_BASE`
(or crc32 of a length-prefixed key). **Never** `hash((rule, k))` — CPython
salts string hashes per process.

## 10. Pre-registered findings (all admissible)

Report F-* **per diagnostic world** {min, med}.

- F-OVERCONF: I_BCF ⊂ interior of Θ_hm and excludes θ_true or parts of [L,U].
- F-HONEST: I_BCF covers [L,U].
- F-OVERCONF-E2 / F-HONEST-E2: same pattern for I_E2 against Θ_exp.
- F-EMPTY / F-SINGLETON: as §7.
- No new mechanisms, thresholds, or measures after this freeze date.

"""Policy estimands and the exposure map — METHODOLOGY §4, §7, §9.

θ₂ (hub-seed vs control) is the headline. Θ_hm is its not-ruled-out image
over NROY, reported as empirical [L, U]. Θ_exp is the image of δ_spill.
Neither is a posterior.
"""
from scipy.stats import hypergeom, norm

import numpy as np

from . import config
from .kernel import World, n_treated, simulate_panel


def thetas_from_means(y0: float, y1: float, y2: float):
    """θ₁, θ₂, targeting premium from the three arm means."""
    theta1 = y1 - y0
    theta2 = y2 - y0
    return theta1, theta2, theta2 - theta1


def interval_image(values: np.ndarray):
    """Empirical [L, U] of a not-ruled-out image. Empty → (nan, nan)."""
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if values.size == 0:
        return float("nan"), float("nan")
    return float(np.min(values)), float(np.max(values))


def diagnostic_worlds(nroy: np.ndarray, I: np.ndarray) -> dict:
    """c₀^min and c₀^med — functions of I only, never of θ."""
    I = np.asarray(I, dtype=float)
    order = np.argsort(I, kind="mergesort")
    i_min = int(order[0])
    i_med = int(order[len(order) // 2])
    return {
        "min_I": {"index": i_min, "c_row": nroy[i_min], "I": float(I[i_min])},
        "median_I": {"index": i_med, "c_row": nroy[i_med], "I": float(I[i_med])},
    }


def row_to_c(row: np.ndarray, names) -> dict:
    return {name: float(v) for name, v in zip(names, row)}


def evaluate_thetas(world: World, c: dict, reps: int | None = None) -> dict:
    """Monte Carlo θ₁, θ₂, τ at one c. Paired reps share the state stream."""
    reps = config.REPS_ESTIMAND if reps is None else reps
    y0 = np.empty(reps)
    y1 = np.empty(reps)
    y2 = np.empty(reps)
    for r in range(reps):
        y0[r] = simulate_panel(world, c, "control", r)[0].mean()
        y1[r] = simulate_panel(world, c, "random", r)[0].mean()
        y2[r] = simulate_panel(world, c, "degree", r)[0].mean()
    t1, t2, prem = thetas_from_means(float(y0.mean()), float(y1.mean()), float(y2.mean()))
    return {
        "theta1": t1,
        "theta2": t2,
        "premium": prem,
        "se_theta2": float(np.std(y2 - y0, ddof=1) / np.sqrt(reps)) if reps > 1 else float("nan"),
        "se_theta1": float(np.std(y1 - y0, ddof=1) / np.sqrt(reps)) if reps > 1 else float("nan"),
    }


def exposure_share(world: World, D: np.ndarray) -> np.ndarray:
    """s_i = (Σ_{j ∈ N(i)} D_j) / k_i. Isolated nodes have k_i=1 and s_i=0."""
    return (world.adjacency @ D) / world.degrees


def stratum_labels(D: np.ndarray, share: np.ndarray, cut: float) -> np.ndarray:
    """Frozen strata: S1 / S0a / S0b / S0c (METHODOLOGY §9)."""
    D = np.asarray(D)
    share = np.asarray(share)
    labels = np.empty(D.shape[0], dtype=object)
    treated = D > 0.5
    labels[treated] = "S1"
    labels[~treated & (share == 0.0)] = "S0a"
    labels[~treated & (share > 0.0) & (share < cut)] = "S0b"
    labels[~treated & (share >= cut)] = "S0c"
    return labels


def maybe_merge_s0b(labels: np.ndarray, min_n: int) -> tuple[np.ndarray, bool]:
    """If any stratum is thinner than min_n, merge S0b into S0c."""
    merged = False
    for name in ("S1", "S0a", "S0b", "S0c"):
        if int(np.sum(labels == name)) < min_n:
            merged = True
            break
    if merged:
        labels = labels.copy()
        labels[labels == "S0b"] = "S0c"
    return labels, merged


def true_spill_from_panel(world, Y, D, cut=None, min_n=None) -> dict:
    """Realized stratum-mean contrasts (oracle Y). Empty cell → nan."""
    cut = config.EXPOSURE_SHARE_CUT if cut is None else cut
    min_n = config.STRATUM_MIN_N if min_n is None else min_n
    s = exposure_share(world, D)
    lab = stratum_labels(D, s, cut)
    lab, merged = maybe_merge_s0b(lab, min_n)

    def _mean(name):
        mask = lab == name
        if not np.any(mask):
            return float("nan")
        return float(Y[mask].mean())

    m1, m0a, m0c = _mean("S1"), _mean("S0a"), _mean("S0c")
    return {
        "delta_dir": m1 - m0a,
        "delta_spill": m0c - m0a,
        "merged_s0b": merged,
        "means": {"S1": m1, "S0a": m0a, "S0c": m0c},
    }


def exposure_probs(world: World, k_treat: int, cut: float) -> dict:
    """First-order exposure probabilities under SRSWOR(k of N)."""
    n = world.n
    p_S1 = np.full(n, k_treat / n)
    p_untreated = 1.0 - k_treat / n
    p_S0a = np.zeros(n)
    p_S0b = np.zeros(n)
    p_S0c = np.zeros(n)
    for i in range(n):
        d = int(np.round(world.adjacency[i].sum()))
        if d == 0 or k_treat == 0:
            p_S0a[i] = p_untreated
            continue
        # K | D_i=0 ~ Hypergeom(pop=N-1, successes=k_treat, draws=d)
        rv = hypergeom(M=n - 1, n=k_treat, N=d)
        ks = np.arange(d + 1)
        pmf = rv.pmf(ks)
        share = ks / world.degrees[i]
        p_S0a[i] = p_untreated * float(pmf[share == 0.0].sum())
        p_S0c[i] = p_untreated * float(pmf[share >= cut].sum())
        p_S0b[i] = p_untreated * float(pmf[(share > 0.0) & (share < cut)].sum())
    return {"S1": p_S1, "S0a": p_S0a, "S0b": p_S0b, "S0c": p_S0c}


def hajek_mean(y: np.ndarray, in_set: np.ndarray, p: np.ndarray) -> float:
    """Hájek mean: Σ (1_s Y / p) / Σ (1_s / p)."""
    p = np.clip(np.asarray(p, dtype=float), 1e-12, None)
    w = np.asarray(in_set, dtype=float) / p
    denom = w.sum()
    if denom <= 0:
        return float("nan")
    return float((w * y).sum() / denom)


def conservative_hajek_var(y: np.ndarray, in_set: np.ndarray, p: np.ndarray) -> float:
    """Linearized Hájek variance, first-order (Bernoulli) terms only.

    Dropping second-order (without-replacement) covariances is conservative
    for a contrast of two nearly-partition strata whose covariance is
    typically negative.
    """
    p = np.clip(np.asarray(p, dtype=float), 1e-12, None)
    in_set = np.asarray(in_set, dtype=float)
    mu = hajek_mean(y, in_set, p)
    if not np.isfinite(mu):
        return float("nan")
    w = in_set / p
    denom = w.sum()
    if denom <= 0:
        return float("nan")
    # influence of unit i on the Hajek mean
    u = in_set * (y - mu) / p
    # Bernoulli: Var(1_i) = p_i (1-p_i), so Var(u_i) = (1-p_i)/p_i * 1{...} (y-mu)^2
    # Using the realized indicator: sum_i ((1-p_i)/p_i) * 1_i (y_i-mu)^2 / denom^2
    num = (((1.0 - p) / p) * in_set * (y - mu) ** 2).sum()
    return float(num / (denom ** 2))


def hajek_contrasts(world, Y, D, cut=None, min_n=None) -> dict:
    """Foil 2 on one π₁ panel: Hájek δ_dir, δ_spill and conservative CIs."""
    cut = config.EXPOSURE_SHARE_CUT if cut is None else cut
    min_n = config.STRATUM_MIN_N if min_n is None else min_n
    s = exposure_share(world, D)
    lab = stratum_labels(D, s, cut)
    lab, merged = maybe_merge_s0b(lab, min_n)
    k = n_treated(world.n)
    p = exposure_probs(world, k, cut)
    if merged:
        # S0b probability mass travels with the merge
        p = dict(p)
        p["S0c"] = p["S0c"] + p["S0b"]
        p["S0b"] = np.zeros_like(p["S0b"])

    def _est(name):
        return hajek_mean(Y, lab == name, p[name])

    def _var(name):
        return conservative_hajek_var(Y, lab == name, p[name])

    d_dir = _est("S1") - _est("S0a")
    d_sp = _est("S0c") - _est("S0a")
    se_dir = float(np.sqrt(max(_var("S1"), 0.0) + max(_var("S0a"), 0.0)))
    se_sp = float(np.sqrt(max(_var("S0c"), 0.0) + max(_var("S0a"), 0.0)))
    # two-sided interval at HM_CONFIDENCE: Φ^{-1}((1+p)/2)
    z = float(norm.ppf(0.5 + 0.5 * config.HM_CONFIDENCE))
    return {
        "delta_dir": d_dir,
        "delta_spill": d_sp,
        "ci_dir": (d_dir - z * se_dir, d_dir + z * se_dir),
        "ci_spill": (d_sp - z * se_sp, d_sp + z * se_sp),
        "se_dir": se_dir,
        "se_spill": se_sp,
        "merged_s0b": merged,
    }


def evaluate_spill(world: World, c: dict, reps: int | None = None, cut=None) -> dict:
    """MC truth of δ_spill, δ_dir at c under π₁ (oracle Y)."""
    reps = config.REPS_ESTIMAND if reps is None else reps
    cut = config.EXPOSURE_SHARE_CUT if cut is None else cut
    spills = []
    dirs_ = []
    any_merge = False
    for r in range(reps):
        Y, D = simulate_panel(world, c, "random", r)
        d = true_spill_from_panel(world, Y, D, cut=cut)
        spills.append(d["delta_spill"])
        dirs_.append(d["delta_dir"])
        any_merge = any_merge or d["merged_s0b"]
    spills = np.asarray(spills, dtype=float)
    dirs_ = np.asarray(dirs_, dtype=float)
    return {
        "delta_spill": float(np.nanmean(spills)),
        "delta_dir": float(np.nanmean(dirs_)),
        "merged_s0b": any_merge,
    }


def sample_nroy_rows(nroy: np.ndarray, n_sample: int, rng) -> np.ndarray:
    """Uniform sample of survivor rows. If |NROY| ≤ n_sample, take all."""
    n = nroy.shape[0]
    if n == 0:
        return nroy
    if n <= n_sample:
        return nroy
    idx = rng.choice(n, size=n_sample, replace=False)
    return nroy[idx]

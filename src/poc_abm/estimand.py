"""Policy estimands and the exposure map — METHODOLOGY §4, §7, §9.

θ₂ (hub-seed vs control) is the headline. Θ_hm is its not-ruled-out image
over NROY, reported as empirical [L, U]. Θ_exp is the image of δ_spill.
Neither is a posterior.
"""
import hashlib

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


def evaluate_thetas(world: World, c: dict, reps: int | None = None, offset0: int = 0) -> dict:
    """Monte Carlo θ₁, θ₂, premium at one c. Paired reps share the state stream.

    Uses stream offsets offset0, ..., offset0 + reps - 1.
    """
    reps = config.REPS_ESTIMAND if reps is None else reps
    y0 = np.empty(reps)
    y1 = np.empty(reps)
    y2 = np.empty(reps)
    for j, r in enumerate(range(offset0, offset0 + reps)):
        y0[j] = simulate_panel(world, c, "control", r)[0].mean()
        y1[j] = simulate_panel(world, c, "random", r)[0].mean()
        y2[j] = simulate_panel(world, c, "degree", r)[0].mean()
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


def exposure_indicators(world: World, D_rows: np.ndarray, cut: float, merged: bool) -> dict:
    """Exposure of every person under many assignments at once (one row per assignment).

    The same map as stratum_labels, vectorized. Returns boolean (rows, n) arrays
    for S1 (treated), S0a (untreated, no treated neighbor) and S0c (untreated,
    treated share >= cut). If merged, S0b joins S0c, as in maybe_merge_s0b.
    """
    D_rows = np.atleast_2d(np.asarray(D_rows, dtype=float))
    share = (D_rows @ world.adjacency.T) / world.degrees
    treated = D_rows > 0.5
    untreated = ~treated
    s0c = untreated & (share >= cut)
    if merged:
        s0c = s0c | (untreated & (share > 0.0) & (share < cut))
    return {"S1": treated, "S0a": untreated & (share == 0.0), "S0c": s0c}


def joint_probs(ind: dict) -> dict:
    """First- and second-order exposure probabilities from equally likely assignments.

    p[k][i]        = share of assignments in which person i has exposure k.
    pi[(k, l)][i,j] = share in which i has exposure k AND j has exposure l.
    With every assignment listed, these are exact. With simulated draws they are
    the Monte Carlo estimates of Aronow and Samii (2017, section 5).
    """
    names = tuple(ind.keys())
    F = {k: np.asarray(ind[k], dtype=float) for k in names}
    m = next(iter(F.values())).shape[0]
    p = {k: F[k].mean(axis=0) for k in names}
    pi = {}
    for a, k in enumerate(names):
        for l in names[a:]:
            pi[(k, l)] = (F[k].T @ F[l]) / m
            pi[(l, k)] = pi[(k, l)].T
    return {"p": p, "pi": pi}


def exposure_mc(world: World, k_treat: int, cut: float, merged: bool, draws=None, seed=None) -> dict:
    """Simulate the random arm's design (choose k_treat of N without replacement)
    `draws` times and return joint_probs of the exposures."""
    draws = config.EXPOSURE_MC_DRAWS if draws is None else draws
    seed = config.SEED_FOIL2_MC if seed is None else seed
    rng = np.random.default_rng(seed)
    rows = np.zeros((draws, world.n))
    for m in range(draws):
        rows[m, rng.choice(world.n, size=k_treat, replace=False)] = 1.0
    return joint_probs(exposure_indicators(world, rows, cut, merged))


_EXPOSURE_MC_CACHE: dict = {}


def _exposure_mc_cached(world: World, k_treat: int, cut: float, merged: bool) -> dict:
    """The design depends only on the graph, k, the cut and the merge; compute it once.

    The key hashes the adjacency CONTENTS, so a changed graph (or a reused
    object id) can never receive another graph's probabilities.
    """
    graph = hashlib.sha256(np.ascontiguousarray(world.adjacency, dtype=float).tobytes()).hexdigest()
    key = (graph, world.n, k_treat, float(cut), bool(merged),
           config.EXPOSURE_MC_DRAWS, config.SEED_FOIL2_MC)
    if key not in _EXPOSURE_MC_CACHE:
        _EXPOSURE_MC_CACHE[key] = exposure_mc(world, k_treat, cut, merged)
    return _EXPOSURE_MC_CACHE[key]


def ht_cov(a_k, a_l, p_k, p_l, pi_kl, same: bool) -> float:
    """Aronow-Samii (2017) estimate of Cov(T_k, T_l), with T = sum_i a_i / p_i.

    a_k is zero outside exposure k (a_i = 1_i(k) * e_i). same=True gives Var(T_k).
    Pairs that can be seen together (pi_ij > 0):
        sum_ij (pi_ij - p_i p_j) / pi_ij * a_i a_j / (p_i p_j).
    Pairs that can never be seen together (pi_ij = 0) get Young's inequality:
        variance:   + sum_{pi_ij = 0} [a_i^2 / (2 p_i) + a_j^2 / (2 p_j)]
        covariance: - the same sum.
    Both signs make Var(T_k - T_l) = V_k + V_l - 2 C_kl conservative.
    """
    a_k = np.asarray(a_k, dtype=float)
    a_l = np.asarray(a_l, dtype=float)
    p_k = np.asarray(p_k, dtype=float)
    p_l = np.asarray(p_l, dtype=float)
    pi_kl = np.asarray(pi_kl, dtype=float)
    safe_k = np.where(p_k > 0, p_k, 1.0)
    safe_l = np.where(p_l > 0, p_l, 1.0)
    pos = pi_kl > 0
    W = np.zeros_like(pi_kl)
    W[pos] = (pi_kl[pos] - np.outer(p_k, p_l)[pos]) / pi_kl[pos]
    main = float((a_k / safe_k) @ W @ (a_l / safe_l))
    zero = ~pos
    young = 0.5 * float((a_k ** 2 / safe_k) @ zero.sum(axis=1) + (a_l ** 2 / safe_l) @ zero.sum(axis=0))
    return main + young if same else main - young


def hajek_contrasts(world, Y, D, cut=None, min_n=None) -> dict:
    """Foil 2 on one random-arm panel: Hajek delta_dir, delta_spill and their intervals.

    Point estimates weight each person by 1 / P(exposure), with exact first-order
    probabilities (exposure_probs). Variances linearize the Hajek means
    (e_i = y_i - mean of the exposure) and apply ht_cov with joint probabilities
    from exposure_mc. Var(delta) = V(a) + V(b) - 2 Cov(a, b).
    """
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
    pi = _exposure_mc_cached(world, k, cut, merged)["pi"]
    Y = np.asarray(Y, dtype=float)
    ind = {name: (lab == name) for name in ("S1", "S0a", "S0c")}
    mu = {name: hajek_mean(Y, ind[name], p[name]) for name in ind}
    n_hat = {name: float((ind[name] / np.where(p[name] > 0, p[name], 1.0)).sum()) for name in ind}
    a = {name: ind[name] * (Y - mu[name]) for name in ind}

    def _pi(k1, k2):
        m = pi[(k1, k2)]
        if k1 == k2:  # the diagonal is the first-order probability; use the exact one
            m = m.copy()
            np.fill_diagonal(m, p[k1])
        return m

    def _cov(k1, k2):
        c = ht_cov(a[k1], a[k2], p[k1], p[k2], _pi(k1, k2), same=(k1 == k2))
        return c / (n_hat[k1] * n_hat[k2])

    d_dir = mu["S1"] - mu["S0a"]
    d_sp = mu["S0c"] - mu["S0a"]
    se_dir = float(np.sqrt(max(_cov("S1", "S1") + _cov("S0a", "S0a") - 2 * _cov("S1", "S0a"), 0.0)))
    se_sp = float(np.sqrt(max(_cov("S0c", "S0c") + _cov("S0a", "S0a") - 2 * _cov("S0c", "S0a"), 0.0)))
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
        "variance": f"Aronow-Samii 2017, joint exposure probabilities from {config.EXPOSURE_MC_DRAWS} draws",
    }


def evaluate_spill(world: World, c: dict, reps: int | None = None, cut=None, offset0: int = 0) -> dict:
    """MC truth of δ_spill, δ_dir at c under π₁ (oracle Y)."""
    reps = config.REPS_ESTIMAND if reps is None else reps
    cut = config.EXPOSURE_SHARE_CUT if cut is None else cut
    spills = []
    dirs_ = []
    any_merge = False
    for r in range(offset0, offset0 + reps):
        Y, D = simulate_panel(world, c, "random", r)
        d = true_spill_from_panel(world, Y, D, cut=cut)
        spills.append(d["delta_spill"])
        dirs_.append(d["delta_dir"])
        any_merge = any_merge or d["merged_s0b"]
    spills = np.asarray(spills, dtype=float)
    dirs_ = np.asarray(dirs_, dtype=float)
    ok = spills[np.isfinite(spills)]
    return {
        "delta_spill": float(np.nanmean(spills)),
        "delta_dir": float(np.nanmean(dirs_)),
        "se_spill": float(np.std(ok, ddof=1) / np.sqrt(ok.size)) if ok.size > 1 else float("nan"),
        "merged_s0b": any_merge,
    }


def sample_nroy_index(n: int, n_sample: int, rng) -> np.ndarray:
    """Row indices of a uniform NROY sample without replacement. If n ≤ n_sample, all rows."""
    if n <= n_sample:
        return np.arange(n)
    return rng.choice(n, size=n_sample, replace=False)


def sample_nroy_rows(nroy: np.ndarray, n_sample: int, rng) -> np.ndarray:
    """Uniform sample of NROY rows. If |NROY| ≤ n_sample, take all."""
    if nroy.shape[0] == 0:
        return nroy
    return nroy[sample_nroy_index(nroy.shape[0], n_sample, rng)]

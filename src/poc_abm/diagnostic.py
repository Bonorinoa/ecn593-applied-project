"""Diagnostic overlay: two foils, two worlds — METHODOLOGY §9–§10.

Foil 1 is a SUTVA one-world interval (the ruler for one-world practice).
This pin: OLS-HC1 (CausalForestDML does not import). Report that name;
do not call it BCF. Foil 2 is exposure-mapped Hájek on π₁. Each interval
is judged against ITS OWN image. Foil 1 is not a candidate for Θ_hm.
"""
from scipy.stats import norm

import numpy as np

from . import config
from .estimand import hajek_contrasts
from .kernel import World, simulate_panel, stream_seed
from .measures import admit, apply_measure, theta2_from_scores


def classify_interval(interval, image):
    """Map (I, Θ) to F-HONEST / F-OVERCONF / None.

    F-HONEST: I covers [L, U].
    F-OVERCONF: I is a strict subset of the interior of Θ.
    Anything else is unnamed — we do not add a finding after the freeze.
    """
    lo, hi = interval
    L, U = image
    if not all(np.isfinite(x) for x in (lo, hi, L, U)):
        return None
    if lo <= L and hi >= U:
        return "F-HONEST"
    if lo > L and hi < U:
        return "F-OVERCONF"
    return None


def oracle_gate(point: float, ci: tuple, truth: float) -> bool:
    """True iff truth lies inside the CI (harness OK). Point is unused."""
    lo, hi = ci
    return bool(np.isfinite(truth) and lo <= truth <= hi)


def ols_ate_hc1(y, D, X) -> dict:
    """SUTVA OLS of s on D given X, HC1 interval. Fallback Foil 1.

    Design matrix [1, D, X]. The D coefficient is the ATE under SUTVA
    and unconfoundedness given X. HC1 = n/(n-k) sandwich.
    """
    y = np.asarray(y, dtype=float)
    D = np.asarray(D, dtype=float)
    X = np.asarray(X, dtype=float)
    n = y.shape[0]
    Z = np.column_stack([np.ones(n), D, X])
    k = Z.shape[1]
    xtx = Z.T @ Z
    beta = np.linalg.solve(xtx, Z.T @ y)
    resid = y - Z @ beta
    meat = Z.T @ ((resid ** 2)[:, None] * Z)
    inv = np.linalg.inv(xtx)
    cov = (n / (n - k)) * inv @ meat @ inv
    se = float(np.sqrt(max(cov[1, 1], 0.0)))
    ate = float(beta[1])
    zcrit = float(norm.ppf(0.5 + 0.5 * config.HM_CONFIDENCE))
    return {"ate": ate, "ci": (ate - zcrit * se, ate + zcrit * se), "estimator": "OLS-HC1"}


def fit_forest(X, D, s, seed: int) -> dict:
    """Foil 1: CausalForestDML if importable, else OLS-HC1 (AMENDMENT-02)."""
    try:
        from econml.dml import CausalForestDML

        est = CausalForestDML(
            n_estimators=config.CF_N_ESTIMATORS,
            min_samples_leaf=config.CF_MIN_SAMPLES_LEAF,
            honest=True,
            discrete_treatment=True,
            random_state=seed,
        )
        T = np.asarray(D, dtype=int)
        Xx = np.asarray(X, dtype=float)
        est.fit(Y=np.asarray(s, dtype=float), T=T, X=Xx)
        ate = float(np.mean(est.effect(Xx)))
        lo, hi = est.ate_interval(Xx)
        return {"ate": ate, "ci": (float(lo), float(hi)), "estimator": "CausalForestDML"}
    except Exception:
        return ols_ate_hc1(s, D, X)


def measure_image_theta2(world: World, c: dict, seed_offset: int) -> dict:
    """Θ_cv(c₀) = image of θ₂ over admissible scorings at this world."""
    rng = np.random.default_rng(stream_seed("measure", seed_offset))
    y0, _ = simulate_panel(world, c, "control", seed_offset)
    y2, _ = simulate_panel(world, c, "degree", seed_offset)
    values = {}
    admitted = []
    for name in ("m1", "m2", "m3"):
        s0 = apply_measure(y0, world.X, name, rng)
        s2 = apply_measure(y2, world.X, name, rng)
        ok = admit(s2, world.X)
        values[name] = {"theta2": theta2_from_scores(s0, s2), "admitted": ok}
        if ok:
            admitted.append(values[name]["theta2"])
    L, U = (float(min(admitted)), float(max(admitted))) if admitted else (float("nan"), float("nan"))
    return {
        "per_measure": values,
        "Theta_cv": (L, U),
        "admitted_names": tuple(k for k, v in values.items() if v["admitted"]),
    }


def run_foils(world: World, c: dict, theta2_true: float, spill_true: float) -> dict:
    """Fit both foils at one diagnostic world. Foil 1 on π₂; E2 on π₁."""
    y2, d2 = simulate_panel(world, c, "degree", seed_offset=0)
    y1, d1 = simulate_panel(world, c, "random", seed_offset=0)

    foil1 = {}
    rng_m = np.random.default_rng(stream_seed("measure", 0))
    for mname in ("m1", "m2"):
        s = apply_measure(y2, world.X, mname, rng_m)
        foil1[mname] = fit_forest(world.X, d2, s, seed=config.SEED_CF)

    e2 = hajek_contrasts(world, y1, d1)
    e2_oracle_ok = oracle_gate(e2["delta_spill"], e2["ci_spill"], spill_true)

    return {
        "forest": foil1,  # key kept for overlay payload; estimator name is inside
        "e2": e2,
        "e2_oracle_ok": e2_oracle_ok,
        "theta2_true": theta2_true,
        "spill_true": spill_true,
    }

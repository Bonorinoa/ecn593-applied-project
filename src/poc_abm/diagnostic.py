"""Diagnostic overlay: two foils, three points (min-I, median-I, c_star).

Foil 1 (degree arm) is the whole-village policy estimate of a SUTVA analyst:
OLS-HC1 of Y on [1, D, X] gives beta-hat, and with no interference
theta_2 = (k/N) x (effect on the seeded), so the analyst reports (k/N) x beta-hat
and (k/N) x its interval. It is NOT an identified estimator of theta_2 under the
kernel's interference; that failure is the finding (PLAN item 10, verifier
t_2b7a8d8c). Compared with Theta_hm.

Foil 2 (random arm) is the exposure-mapped Hajek spillover contrast with the
Aronow-Samii variance (estimand.hajek_contrasts). Compared with Theta_exp.

Each interval is judged against its own image (classify_interval). It gets a
covers_truth flag (the truth at its own point) and a covers_planted_truth flag
(the truth at c_star). Both are descriptive containment indicators for that one
panel, not repeated-sampling coverage and not a validity gate. Foil 2 is checked
separately by scripts/check_foil2_coverage.py (PLAN items 11, 14).

Both foils use the true outcome Y. The measurement layer (m1-m3, admission,
Theta_cv) is parked; restore from commit ebed7ce (PLAN item 13).
"""
from scipy.stats import norm

import numpy as np

from . import config
from .estimand import hajek_contrasts
from .kernel import World, simulate_panel


def classify_interval(interval, image):
    """Map (I, Θ) to F-HONEST / F-OVERCONF / None.

    F-HONEST: I covers [L, U].
    F-OVERCONF: I is a strict subset of the interior of Θ.
    Anything else is no verdict (None).
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


def covers_truth(ci, truth: float) -> bool:
    """True iff the truth lies inside this one realized interval. Not coverage; never a stop."""
    lo, hi = ci
    return bool(np.isfinite(truth) and lo <= truth <= hi)


def containment_flags(foil1_ci, foil2_ci, theta2_true: float, spill_true: float,
                      theta2_planted: float, spill_planted: float) -> dict:
    """Containment of each interval's point truth and the planted village truth."""
    return {
        "foil1_covers_truth": covers_truth(foil1_ci, theta2_true),
        "foil2_covers_truth": covers_truth(foil2_ci, spill_true),
        "foil1_covers_planted_truth": covers_truth(foil1_ci, theta2_planted),
        "foil2_covers_planted_truth": covers_truth(foil2_ci, spill_planted),
    }


def ols_ate_hc1(y, D, X) -> dict:
    """OLS of y on [1, D, X]; the D coefficient with an HC1 interval.

    HC1 = n/(n-k) sandwich. Read as an effect only under SUTVA,
    exchangeability and positivity given X, and a correct additive
    constant-effect model.
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


def foil1_policy(world: World, y, D) -> dict:
    """Foil 1: the SUTVA analyst's village-level policy interval, (k/N) x OLS-HC1.

    share = k/N is read from the panel (number seeded / N). Scaling both
    endpoints by a known positive constant keeps the analyst's own coverage
    statement; it does not repair the analyst's assumptions.
    """
    D = np.asarray(D, dtype=float)
    ols = ols_ate_hc1(y, D, world.X)
    share = float(D.sum()) / world.n
    lo, hi = ols["ci"]
    return {
        "beta": ols["ate"],
        "ci_beta": ols["ci"],
        "share": share,
        "estimate": share * ols["ate"],
        "ci": (share * lo, share * hi),
        "estimator": "OLS-HC1 x k/N (SUTVA policy estimate)",
    }


def policy_gap_decomposition(world: World, c: dict, reps: int | None = None,
                             displayed_beta: float = float("nan")) -> dict:
    """Why (k/N) x beta-hat differs from theta_2: an exact split with paired streams.

    For each rep r, the control and degree panels share Y(0) and every shock, so
    y2 - y0 is each person's policy effect in that rep. With S the seeded set:
        theta_2         = (1/N) sum_i (y2 - y0)
        seeded_part     = (1/N) sum_{i in S} (y2 - y0)
        unseeded_part   = (1/N) sum_{i not in S} (y2 - y0)   (zero under SUTVA)
    selected_policy_contrast = mean over S of (y2 - y0). Under interference this
    is the seeded people's policy contrast, NOT a SUTVA own-treatment ATT.
    mean_beta averages the OLS coefficient over the same reps.

    Two gaps are reported and must not be mixed up (verifier t_2b7a8d8c):
    the gap for the 200-rep mean beta, and the gap for the displayed one-panel
    beta (displayed_beta, the Foil 1 fit at FOIL_PANEL_OFFSET).
    """
    reps = config.REPS_ESTIMAND if reps is None else reps
    n = world.n
    theta2, seeded, unseeded, sel, betas, base_gap = [], [], [], [], [], []
    share = float("nan")
    for r in range(reps):
        y0, _ = simulate_panel(world, c, "control", r)
        y2, d2 = simulate_panel(world, c, "degree", r)
        S = d2 > 0.5
        diff = y2 - y0
        share = float(S.sum()) / n
        theta2.append(diff.mean())
        seeded.append(diff[S].sum() / n)
        unseeded.append(diff[~S].sum() / n)
        sel.append(diff[S].mean())
        betas.append(ols_ate_hc1(y2, d2, world.X)["ate"])
        base_gap.append(y0[S].mean() - y0[~S].mean())
    out = {
        "reps": reps,
        "share": share,
        "theta2": float(np.mean(theta2)),
        "seeded_part": float(np.mean(seeded)),
        "unseeded_part": float(np.mean(unseeded)),
        "selected_policy_contrast": float(np.mean(sel)),
        "mean_beta": float(np.mean(betas)),
        "baseline_gap_seeded_minus_unseeded": float(np.mean(base_gap)),
    }
    out["gap_mean_beta"] = out["theta2"] - share * out["mean_beta"]
    out["ols_error_part_mean_beta"] = share * (out["selected_policy_contrast"] - out["mean_beta"])
    out["unseeded_share_of_gap_mean_beta"] = out["unseeded_part"] / out["gap_mean_beta"]
    out["displayed_beta"] = float(displayed_beta)
    out["gap_displayed"] = out["theta2"] - share * float(displayed_beta)
    out["unseeded_share_of_gap_displayed"] = out["unseeded_part"] / out["gap_displayed"]
    return out


def run_foils(world: World, c: dict, theta2_true: float, spill_true: float,
              theta2_planted: float, spill_planted: float) -> dict:
    """Both foils at one point, on one panel each (offset FOIL_PANEL_OFFSET).

    Foil 1 on the degree arm, Foil 2 on the random arm. Outcome: true Y. The
    planted truths are theta2(c*) and delta_spill(c*).
    """
    off = config.FOIL_PANEL_OFFSET
    y2, d2 = simulate_panel(world, c, "degree", seed_offset=off)
    y1, d1 = simulate_panel(world, c, "random", seed_offset=off)
    foil1 = foil1_policy(world, y2, d2)
    foil2 = hajek_contrasts(world, y1, d1)
    return {
        "foil1": foil1,
        "foil2": foil2,
        **containment_flags(foil1["ci"], foil2["ci_spill"], theta2_true, spill_true,
                            theta2_planted, spill_planted),
    }

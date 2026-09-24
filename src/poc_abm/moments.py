"""Moment map M(c) and implausibility I(c) — METHODOLOGY §5–§6.

Read this next to METHODOLOGY.md; the three simulated moments mirror the three
external anchors one-for-one, which is what makes the calibration interpretable.
"""
import json

import numpy as np

from . import config
from .kernel import World, simulate_panel

# moment order is part of the frozen spec:
MOMENT_NAMES = ("level_imm", "gradient_edu", "level_internet")


def load_frozen_z():
    """Load AMENDMENT-02 planted z from data/planted.json.

    z is M̂(c*) in [0,1] already. Sampling variances travel in the audit dict.
    """
    path = config.DATA_DIR / "planted.json"
    raw = json.loads(path.read_text())
    z = np.array(raw["z"], dtype=float)
    audit = {
        "source": "planted",
        "c_star": raw["c_star"],
        "reps_z": int(raw["reps_z"]),
        "sampling_variances": np.array(raw["sampling_variances"], dtype=float),
    }
    return z, audit


def sampling_variances(audit: dict) -> np.ndarray:
    """Diagonal sampling variances of planted z (MC of the R_z mean)."""
    return np.asarray(audit["sampling_variances"], dtype=float)


def plant_and_freeze(world: World, path=None) -> dict:
    """Evaluate M̂(c*) and write data/planted.json. Call once before waves."""
    path = config.DATA_DIR / "planted.json" if path is None else path
    m, mc = simulate_moments(world, config.C_STAR, reps=config.REPS_Z)
    payload = {
        "amendment": "AMENDMENT-02",
        "c_star": {k: float(v) for k, v in config.C_STAR.items()},
        "z": m.tolist(),
        "sampling_variances": mc.tolist(),
        "reps_z": int(config.REPS_Z),
        "moment_names": list(MOMENT_NAMES),
    }
    path.write_text(json.dumps(payload, indent=2))
    return payload


def discrepancy() -> np.ndarray:
    """δ² on the moment diagonal, same units as z."""
    return np.array([config.DELTA[name] ** 2 for name in MOMENT_NAMES], dtype=float)


def implausibility(z: np.ndarray, m_hat: np.ndarray, v_diag: np.ndarray) -> float:
    """I(c) = (z − M̂)ᵀ V⁻¹ (z − M̂) with V = diag(v_diag).

    I is a squared Mahalanobis discrepancy, not a distance.
    """
    diff = np.asarray(z, dtype=float) - np.asarray(m_hat, dtype=float)
    inv = 1.0 / np.asarray(v_diag, dtype=float)
    return float(diff @ (inv * diff))


def v_diag_of(sampling: np.ndarray, mc: np.ndarray) -> np.ndarray:
    """V = diag(σ²_sampling + σ²_MC + δ²)."""
    return np.asarray(sampling, dtype=float) + np.asarray(mc, dtype=float) + discrepancy()


def simulate_moments(world: World, c: dict, reps: int = None):
    """Estimate M(c) = (level_imm, gradient_edu, level_internet) and σ²_MC.

    level_imm      : mean Ȳ_T under degree-seed arm (preventive behavior level)
    gradient_edu   : corr(Y_T, education covariate) under degree-seed arm
    level_internet : mean Ȳ_T under random-seed arm (diffusion/adoption level)

    σ²_MC is the variance of the mean: sample var of the R_m reps / R_m.
    Paired reps: rep r of every arm shares seed_offset r (state stream).
    """
    reps = config.REPS_MOMENT if reps is None else reps
    edu = world.X[:, 0]
    edu_ok = float(np.std(edu)) > 0.0

    levels_deg = np.empty(reps)
    corrs = np.empty(reps)
    levels_rand = np.empty(reps)
    for r in range(reps):
        y_deg, _ = simulate_panel(world, c, "degree", r)
        y_rnd, _ = simulate_panel(world, c, "random", r)
        levels_deg[r] = y_deg.mean()
        levels_rand[r] = y_rnd.mean()
        if edu_ok and float(np.std(y_deg)) > 0.0:
            corrs[r] = np.corrcoef(y_deg, edu)[0, 1]
        else:
            corrs[r] = np.nan

    m = np.array(
        [np.mean(levels_deg), np.nanmean(corrs), np.mean(levels_rand)],
        dtype=float,
    )
    # variance of the mean; ddof=1. All-nan corr column -> inf so I rejects.
    def _mean_var(x):
        x = x[np.isfinite(x)]
        if x.size < 2:
            return np.inf
        return float(np.var(x, ddof=1) / x.size)

    mc = np.array(
        [_mean_var(levels_deg), _mean_var(corrs), _mean_var(levels_rand)],
        dtype=float,
    )
    return m, mc

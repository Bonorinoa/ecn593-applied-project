"""Moment map M(c), the planted targets z, and implausibility I(c)."""
import json

import numpy as np

from . import config
from .kernel import World, simulate_panel

# moment order is part of the frozen spec:
MOMENT_NAMES = ("sq_level", "sq_corr_x1", "sq_peer_corr", "pilot_level")


def load_z(source: str = "planted"):
    """Load z and its audit dict. The planted source is the only v2 source."""
    if source == "planted":
        return load_frozen_z()
    raise ValueError(f"unknown z source: {source!r}")


def load_frozen_z():
    """Load the planted targets z from data/planted.json.

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
        "design": "preregistration-v2",
        "c_star": {k: float(v) for k, v in config.C_STAR.items()},
        "z": m.tolist(),
        "sampling_variances": mc.tolist(),
        "reps_z": int(config.REPS_Z),
        "moment_names": list(MOMENT_NAMES),
    }
    path.write_text(json.dumps(payload, indent=2))
    return payload


def discrepancy(delta: dict | None = None) -> np.ndarray:
    """δ² on the moment diagonal, same units as z.

    `delta` is a dict {moment name: δ}. The default is config.DELTA (the design).
    scripts/delta_menu.py passes its own, so the design file is never edited.
    """
    delta = config.DELTA if delta is None else delta
    return np.array([delta[name] ** 2 for name in MOMENT_NAMES], dtype=float)


def implausibility(z: np.ndarray, m_hat: np.ndarray, v_diag: np.ndarray) -> float:
    """I(c) = (z − M̂)ᵀ V⁻¹ (z − M̂) with V = diag(v_diag).

    I is a squared Mahalanobis discrepancy, not a distance.
    """
    diff = np.asarray(z, dtype=float) - np.asarray(m_hat, dtype=float)
    inv = 1.0 / np.asarray(v_diag, dtype=float)
    return float(diff @ (inv * diff))


def v_diag_of(sampling: np.ndarray, mc: np.ndarray, delta: dict | None = None) -> np.ndarray:
    """V = diag(σ²_sampling + σ²_MC + δ²). `delta` defaults to config.DELTA."""
    return np.asarray(sampling, dtype=float) + np.asarray(mc, dtype=float) + discrepancy(delta)


def peer_correlation(world: World, y: np.ndarray) -> float:
    """Correlation of y with the row-normalized peer mean W y."""
    y = np.asarray(y, dtype=float)
    peer_mean = (world.adjacency @ y) / world.degrees
    if float(np.std(y)) == 0.0 or float(np.std(peer_mean)) == 0.0:
        return float("nan")
    return float(np.corrcoef(y, peer_mean)[0, 1])


def simulate_moments(world: World, c: dict, reps: int = None):
    """Estimate the four v2 moments and their Monte Carlo variances.

    The control and random arms use the same state stream at each rep. The
    degree arm is not simulated. Each variance is the sample variance of the
    finite rep values, divided by their count.
    """
    reps = config.REPS_MOMENT if reps is None else reps
    x1 = world.X[:, 0]
    x1_ok = float(np.std(x1)) > 0.0

    sq_levels = np.empty(reps)
    sq_corr_x1 = np.empty(reps)
    sq_peer_corr = np.empty(reps)
    pilot_levels = np.empty(reps)
    for r in range(reps):
        y_sq, _ = simulate_panel(world, c, "control", r)
        y_rnd, _ = simulate_panel(world, c, "random", r)
        sq_levels[r] = y_sq.mean()
        pilot_levels[r] = y_rnd.mean()
        if x1_ok and float(np.std(y_sq)) > 0.0:
            sq_corr_x1[r] = np.corrcoef(y_sq, x1)[0, 1]
        else:
            sq_corr_x1[r] = np.nan
        sq_peer_corr[r] = peer_correlation(world, y_sq)

    m = np.array(
        [np.mean(sq_levels), np.nanmean(sq_corr_x1),
         np.nanmean(sq_peer_corr), np.mean(pilot_levels)],
        dtype=float,
    )
    # Variance of the mean; ddof=1. An all-nan correlation gives inf, so I rejects.
    def _mean_var(x):
        x = x[np.isfinite(x)]
        if x.size < 2:
            return np.inf
        return float(np.var(x, ddof=1) / x.size)

    mc = np.array(
        [_mean_var(sq_levels), _mean_var(sq_corr_x1),
         _mean_var(sq_peer_corr), _mean_var(pilot_levels)],
        dtype=float,
    )
    return m, mc

"""Measurement layer — METHODOLOGY §8.

Observed scores s are generated from true Y_T. Admission screens MEASURES
against a pre-declared restriction (must not load on the treatment-channel
covariate x3). It does not re-filter NROY.
"""
import numpy as np

from . import config


def apply_measure(Y, X, name: str, rng, noise=None) -> np.ndarray:
    """Map true Y_T to a scored outcome s."""
    Y = np.asarray(Y, dtype=float)
    X = np.asarray(X, dtype=float)
    if name == "m1":
        return Y.copy()
    if name == "m2":
        eps = np.zeros_like(Y) if noise is not None else rng.normal(0.0, config.SURVEY_NOISE_SD, size=Y.shape)
        if noise is not None:
            eps = np.asarray(noise, dtype=float)
        return np.clip(Y + eps, 0.0, 1.0)
    if name == "m3":
        load = config.BAD_ITEM_X_LOAD
        eps = np.zeros_like(Y) if noise is not None else rng.normal(0.0, config.BAD_ITEM_NOISE_SD, size=Y.shape)
        if noise is not None:
            eps = np.asarray(noise, dtype=float)
        return np.clip((1.0 - load) * Y + load * X[:, 2] + eps, 0.0, 1.0)
    raise ValueError(f"unknown measure: {name}")


def admit(s: np.ndarray, X: np.ndarray) -> bool:
    """True iff |corr(s, x3)| is strictly below the frozen threshold.

    Undefined corr (zero variance) is treated as not loading → admitted.
    """
    s = np.asarray(s, dtype=float)
    x3 = np.asarray(X, dtype=float)[:, 2]
    if float(np.std(s)) == 0.0 or float(np.std(x3)) == 0.0:
        return True
    r = float(np.corrcoef(s, x3)[0, 1])
    if not np.isfinite(r):
        return True
    return abs(r) < config.ADMISSION_CORR_THRESHOLD


def admitted_measures(Y, X, rng) -> tuple:
    """M* at this panel. Pre-declared candidates: m1, m2, m3."""
    kept = []
    for name in ("m1", "m2", "m3"):
        s = apply_measure(Y, X, name, rng)
        if admit(s, X):
            kept.append(name)
    return tuple(kept)


def theta2_from_scores(s_control: np.ndarray, s_degree: np.ndarray) -> float:
    """θ₂ analogue on scored outcomes: mean(s | π₂) − mean(s | π₀)."""
    return float(s_degree.mean() - s_control.mean())

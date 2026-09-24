"""History matching: LHS waves -> NROY set — METHODOLOGY §6–§7.

Deliberately emulator-free: direct evaluation only. Empty NROY is a finding;
τ is never loosened.
"""
from scipy.stats import chi2
from scipy.stats.qmc import LatinHypercube

import numpy as np

from . import config
from .moments import implausibility, simulate_moments, v_diag_of


def tau_threshold() -> float:
    """τ = χ²_{N_MOMENTS} quantile at HM_CONFIDENCE."""
    return float(chi2.ppf(config.HM_CONFIDENCE, config.N_MOMENTS))


def latin_hypercube(n_points: int, box: dict, rng) -> dict:
    """LHS over the (possibly concentrated) parameter box. Returns {param: values}."""
    names = list(box.keys())
    sampler = LatinHypercube(d=len(names), rng=rng)
    u = sampler.random(n_points)
    samples = {}
    for j, name in enumerate(names):
        lo, hi = box[name]
        samples[name] = lo + u[:, j] * (hi - lo)
    return samples


def points_to_array(samples: dict) -> np.ndarray:
    return np.column_stack([samples[k] for k in samples.keys()])


def array_to_params(row: np.ndarray, names) -> dict:
    return {name: float(v) for name, v in zip(names, row)}


def survivor_bbox(points: np.ndarray, inflation: float):
    """Bounding box of survivors, inflated by `inflation` fraction on each side.

    pad = inflation * span / 2, so inflation=0.20 expands the box 10% each side
    (20% of the span in total).
    """
    lo = points.min(axis=0)
    hi = points.max(axis=0)
    span = hi - lo
    pad = inflation * span / 2.0
    return lo - pad, hi + pad


def clip_box(lo: np.ndarray, hi: np.ndarray, names) -> dict:
    """Never search outside the frozen parameter box C."""
    box = {}
    for j, name in enumerate(names):
        orig_lo, orig_hi = config.PARAM_BOX[name]
        box[name] = (float(max(lo[j], orig_lo)), float(min(hi[j], orig_hi)))
        if box[name][0] > box[name][1]:
            # numerical guard: empty slice -> keep original
            box[name] = (float(orig_lo), float(orig_hi))
    return box


def _collapsed(nroy: np.ndarray, names) -> bool:
    """F-SINGLETON: every axis span is < 5% of the original box span."""
    for j, name in enumerate(names):
        orig_lo, orig_hi = config.PARAM_BOX[name]
        orig_span = orig_hi - orig_lo
        span = float(nroy[:, j].max() - nroy[:, j].min())
        if orig_span <= 0:
            continue
        if span >= 0.05 * orig_span:
            return False
    return True


def run_waves(
    world,
    z: np.ndarray,
    sampling: np.ndarray,
    n_points: int | None = None,
    n_waves: int | None = None,
    moment_fn=None,
    rng=None,
):
    """The wave loop. Returns a dict with NROY, I(c), finding, τ.

    NROY is the UNION of points with I ≤ τ across waves (METHODOLOGY §6).
    """
    n_points = config.WAVE_POINTS if n_points is None else n_points
    n_waves = config.WAVES if n_waves is None else n_waves
    tau = tau_threshold()
    moment_fn = simulate_moments if moment_fn is None else moment_fn
    rng = np.random.default_rng(config.SEED_HM) if rng is None else rng

    names = list(config.PARAM_BOX.keys())
    box = {k: tuple(v) for k, v in config.PARAM_BOX.items()}

    nroy_pts = []
    nroy_I = []
    nroy_M = []
    wave_kept = []
    wave_I_stats = []
    closest = None  # (I, c, M) of the best rejected-or-kept point

    for wave in range(n_waves):
        samples = latin_hypercube(n_points, box, rng)
        pts = points_to_array(samples)
        kept = []
        kept_I = []
        kept_M = []
        I_this = []
        for i in range(pts.shape[0]):
            c = array_to_params(pts[i], names)
            m, mc = moment_fn(world, c)
            v = v_diag_of(sampling, mc)
            I = implausibility(z, m, v)
            I_this.append(I)
            if closest is None or I < closest["I"]:
                closest = {"I": I, "c": c, "M": np.asarray(m, dtype=float).tolist()}
            if I <= tau:
                kept.append(pts[i])
                kept_I.append(I)
                kept_M.append(np.asarray(m, dtype=float))
            if (i + 1) % 100 == 0:
                print(f"  evaluated {i + 1}/{pts.shape[0]}", flush=True)
        I_this = np.asarray(I_this, dtype=float)
        wave_I_stats.append(
            {
                "min": float(I_this.min()),
                "median": float(np.median(I_this)),
                "max": float(I_this.max()),
            }
        )
        wave_kept.append(len(kept))
        print(
            f"wave {wave + 1}: {len(kept)} survivors of {pts.shape[0]} "
            f"(I min={I_this.min():.2f} med={np.median(I_this):.2f})"
        )
        if not kept:
            break
        nroy_pts.extend(kept)
        nroy_I.extend(kept_I)
        nroy_M.extend(kept_M)
        lo, hi = survivor_bbox(np.vstack(kept), config.BOX_INFLATION)
        box = clip_box(lo, hi, names)

    if not nroy_pts:
        return {
            "nroy": np.empty((0, len(names))),
            "I": np.empty((0,)),
            "M": np.empty((0, 3)),
            "param_names": names,
            "wave_kept": wave_kept,
            "wave_I_stats": wave_I_stats,
            "closest": closest,
            "tau": tau,
            "finding": "F-EMPTY",
        }

    nroy = np.vstack(nroy_pts)
    finding = "F-SINGLETON" if _collapsed(nroy, names) else None
    return {
        "nroy": nroy,
        "I": np.asarray(nroy_I, dtype=float),
        "M": np.vstack(nroy_M),
        "param_names": names,
        "wave_kept": wave_kept,
        "wave_I_stats": wave_I_stats,
        "closest": closest,
        "tau": tau,
        "finding": finding,
    }

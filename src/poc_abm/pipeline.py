"""End-to-end run: history matching, the two images, the two foils.

Steps: load z -> waves -> NROY -> 400 sampled points -> Theta_hm, Theta_exp ->
nroy_param_spread -> three points (min-I, median-I, c_star) -> both foils at each.
An empty NROY is a finding (F-EMPTY). tau and delta are never loosened.

Usage:  python -m poc_abm.pipeline [planted]     (default: planted)
Outputs: results/planted/poc_results.json, results/planted/image_points.json,
figures/planted/{waves,overlay,image_points,empty}.png, locks/freeze-planted.txt.
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from poc_abm import config
from poc_abm.estimand import (
    diagnostic_worlds,
    evaluate_spill,
    evaluate_thetas,
    interval_image,
    row_to_c,
    sample_nroy_index,
)
from poc_abm.figures import draw_empty, draw_image_points, draw_overlay, draw_waves
from poc_abm.history_matching import run_waves, tau_threshold
from poc_abm.kernel import World
from poc_abm.moments import MOMENT_NAMES, load_z, sampling_variances
from poc_abm.diagnostic import classify_interval, policy_gap_decomposition, run_foils


def _jsonable(obj):
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, (np.floating, np.integer)):
        return obj.item()
    if isinstance(obj, dict):
        return {str(k): _jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_jsonable(v) for v in obj]
    return obj


def _write_lock(tag: str) -> Path:
    locks = config.ROOT / "locks"
    locks.mkdir(parents=True, exist_ok=True)
    path = locks / f"freeze-{tag}.txt"
    out = subprocess.check_output(
        ["uv", "pip", "freeze", "--python", sys.executable],
        text=True,
    )
    path.write_text(out)
    return path


def _git_commit() -> str:
    """HEAD sha, with '+dirty' if code or inputs differ from it.

    Only config/, src/, scripts/, data/ and requirements*.txt count. Outputs
    (results/, figures/, locks/, writeup/) are ignored, so running one source
    after another does not mark the second run dirty.
    """
    repo = Path(__file__).resolve().parents[2]
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
    paths = ["config", "src", "scripts", "data", "requirements.txt", "requirements-dev.txt"]
    dirty = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", *paths], cwd=repo).returncode != 0
    return sha + ("+dirty" if dirty else "")


SOURCES = ("planted",)


def nroy_param_spread(image_points: list, param_names) -> dict:
    """Descriptive readout: how far the targets restrict each parameter.

    For each parameter: the standard deviation (ddof = 1) over the sampled NROY
    points, divided by the standard deviation of a uniform draw over C on that
    axis, span / sqrt(12). A ratio near 1 means the moments do not restrict it.
    Also the correlation matrix of the parameters over the same points.
    """
    names = list(param_names)
    values = np.array([[p["c"][n] for n in names] for p in image_points], dtype=float)
    sd = values.std(axis=0, ddof=1)
    uniform_sd = np.array([(config.PARAM_BOX[n][1] - config.PARAM_BOX[n][0]) / np.sqrt(12.0)
                           for n in names])
    return {
        "param_names": names,
        "n_points": int(values.shape[0]),
        "sd_sampled_nroy": {n: float(s) for n, s in zip(names, sd)},
        "sd_uniform_box": {n: float(s) for n, s in zip(names, uniform_sd)},
        "sd_ratio": {n: float(s / u) for n, s, u in zip(names, sd, uniform_sd)},
        "correlation_matrix": np.corrcoef(values, rowvar=False).tolist(),
    }


def run_poc(source: str = "planted") -> dict:
    if source not in SOURCES:
        raise ValueError(f"source must be one of {SOURCES}, got {source!r}")
    res_dir = config.RESULTS_DIR / source
    fig_dir = config.FIGURES_DIR / source
    res_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)

    z, audit = load_z(source)
    sampling = sampling_variances(audit)
    tau = tau_threshold()
    world = World()
    print(f"{source}: truth at c* ({config.REPS_ESTIMAND} reps per arm)", flush=True)
    th_star = evaluate_thetas(world, config.C_STAR, reps=config.REPS_ESTIMAND)
    sp_star = evaluate_spill(world, config.C_STAR, reps=config.REPS_ESTIMAND)

    hm = run_waves(world, z, sampling)
    payload = {
        "git_commit": _git_commit(),
        "ran_at": datetime.now(timezone.utc).isoformat(),
        "z_source": source,
        "z": z.tolist(),
        "z_names": list(MOMENT_NAMES),
        "sampling_variances": sampling.tolist(),
        "delta": [config.DELTA[n] for n in MOMENT_NAMES],
        "tau": tau,
        "finding_hm": hm["finding"],
        "wave_kept": hm["wave_kept"],
        "wave_I_stats": hm["wave_I_stats"],
        "closest": hm["closest"],
        "n_nroy": int(hm["nroy"].shape[0]),
        "param_names": hm["param_names"],
        "c_star": {k: float(v) for k, v in config.C_STAR.items()},
        "theta_star": th_star,
        "spill_star": sp_star,
        "notes": [],
    }
    payload["figures"] = []

    if hm["finding"] == "F-EMPTY":
        payload["notes"].append(
            "F-EMPTY: no c in the frozen box C has I(c) ≤ τ. "
            "τ and δ were not touched. This rejects the pair (kernel, z), "
            "not a license to widen the box after seeing the waves."
        )
        payload["notes"].append(
            "Closest M vs z is a discrepancy report, not a calibrated world."
        )
        payload["figures"] = draw_figures(payload, None, fig_dir)
        _dump(payload, res_dir, source)
        return payload

    rng = np.random.default_rng(config.SEED_THETA_SAMPLE)
    idx = sample_nroy_index(hm["nroy"].shape[0], config.THETA_SAMPLE, rng)
    image_points = []
    print(f"images: theta2 and delta_spill at {len(idx)} sampled NROY points", flush=True)
    for n_done, i in enumerate(idx, 1):
        c = row_to_c(hm["nroy"][i], hm["param_names"])
        th = evaluate_thetas(world, c, reps=config.REPS_ESTIMAND)
        sp = evaluate_spill(world, c, reps=config.REPS_ESTIMAND)
        image_points.append({
            "nroy_index": int(i),
            "I": float(hm["I"][i]),
            "c": c,
            "theta2": th["theta2"],
            "se_theta2": th["se_theta2"],
            "delta_spill": sp["delta_spill"],
            "se_spill": sp["se_spill"],
        })
        if n_done % 50 == 0:
            print(f"  image points done {n_done}/{len(idx)}", flush=True)
    theta2s = np.array([p["theta2"] for p in image_points])
    spills = np.array([p["delta_spill"] for p in image_points])
    Theta_hm = interval_image(theta2s)
    Theta_exp = interval_image(spills)
    payload["Theta_hm"] = list(Theta_hm)
    payload["Theta_exp"] = list(Theta_exp)
    payload["n_theta_sample"] = len(image_points)
    payload["nroy_param_spread"] = nroy_param_spread(image_points, hm["param_names"])
    print("endpoint recheck: fresh reps at the four winning points", flush=True)
    payload["endpoint_recheck"] = recheck_extremizers(world, image_points)
    _dump_json(res_dir / "image_points.json", image_points)

    worlds = diagnostic_worlds(hm["nroy"], hm["I"])
    findings = {}
    for key in ("min_I", "median_I", "c_star"):
        print(f"foils at the {key} point", flush=True)
        if key == "c_star":
            c, th, sp = dict(config.C_STAR), th_star, sp_star   # the truth is already computed
        else:
            c = row_to_c(worlds[key]["c_row"], hm["param_names"])
            th = evaluate_thetas(world, c, reps=config.REPS_ESTIMAND)
            sp = evaluate_spill(world, c, reps=config.REPS_ESTIMAND)
        foils = run_foils(world, c, th["theta2"], sp["delta_spill"],
                          theta2_planted=th_star["theta2"], spill_planted=sp_star["delta_spill"])
        foil1, foil2 = foils["foil1"], foils["foil2"]
        decomp = policy_gap_decomposition(world, c, displayed_beta=foil1["beta"])
        findings[key] = {
            "c": c,
            "theta2_true": th["theta2"],
            "se_theta2": th["se_theta2"],
            "spill_true": sp["delta_spill"],
            "se_spill": sp["se_spill"],
            "foil1_estimator": foil1["estimator"],
            "foil1_beta": foil1["beta"],
            "foil1_ci_beta": list(foil1["ci_beta"]),
            "foil1_share": foil1["share"],
            "foil1_ci": list(foil1["ci"]),
            "foil1_vs_Theta_hm": classify_interval(foil1["ci"], Theta_hm),
            "foil1_covers_truth": foils["foil1_covers_truth"],
            "foil1_covers_planted_truth": foils["foil1_covers_planted_truth"],
            "foil1_gap_decomposition": decomp,
            "foil2_estimate": foil2["delta_spill"],
            "foil2_se": foil2["se_spill"],
            "foil2_merged_s0b": foil2["merged_s0b"],
            "foil2_ci": list(foil2["ci_spill"]),
            "foil2_vs_Theta_exp": classify_interval(foil2["ci_spill"], Theta_exp),
            "foil2_covers_truth": foils["foil2_covers_truth"],
            "foil2_covers_planted_truth": foils["foil2_covers_planted_truth"],
        }
        if key != "c_star":
            findings[key]["I"] = worlds[key]["I"]
            findings[key]["nroy_index"] = worlds[key]["index"]
    payload["findings"] = findings
    payload["notes"].append(
        "At each of the three points, covers_truth reports whether the displayed interval "
        "contains that point's own simulator truth, and covers_planted_truth whether it "
        "contains the truth at c_star (the two coincide at c_star). Both are descriptive "
        "containment indicators for one realized panel, not estimates of repeated-sampling "
        "coverage and not validity gates. Foil 2 is checked separately by the pre-declared "
        "repeated-assignment calibration in scripts/check_foil2_coverage.py."
    )
    payload["figures"] = draw_figures(_jsonable(payload), image_points, fig_dir)
    _dump(payload, res_dir, source)
    return payload


def draw_figures(payload: dict, image_points: list | None, fig_dir: Path) -> list:
    """Every figure of a run, built only from saved results. Used by the pipeline
    and by scripts/draw_figures.py, so a figure never needs a rerun to be redrawn."""
    out = [_rel(draw_waves(payload["wave_kept"], payload["wave_I_stats"], payload["tau"],
                           payload["z_source"], fig_dir / "waves.png"))]
    if payload["finding_hm"] == "F-EMPTY":
        info = {k: payload[k] for k in ("z", "tau", "closest", "wave_I_stats")}
        out.append(_rel(draw_empty(info, fig_dir / "empty.png")))
        return out
    out.append(_rel(draw_image_points(image_points, payload["Theta_hm"], payload["Theta_exp"],
                                      fig_dir / "image_points.png")))
    overlay = {"worlds": {}}
    for key, f in payload["findings"].items():
        overlay["worlds"][key] = {
            "Theta_hm": payload["Theta_hm"],
            "Theta_exp": payload["Theta_exp"],
            "theta2_true": f["theta2_true"],
            "spill_true": f["spill_true"],
            "foil1_ci": f["foil1_ci"],
            "foil1_label": r"Foil 1: $(k/N)\times$OLS-HC1",
            "foil2_ci": f["foil2_ci"],
            "theta2_star": None if key == "c_star" else payload["theta_star"]["theta2"],
            "spill_star": None if key == "c_star" else payload["spill_star"]["delta_spill"],
        }
    out.append(_rel(draw_overlay(overlay, fig_dir / "overlay.png")))
    return out


def recheck_extremizers(world: World, image_points: list) -> dict:
    """Independent recheck of the pilot-selected endpoint candidates.

    The image endpoints are the min and max of 400 noisy estimates, so the
    estimate at the winning point is biased outward (it won partly on noise).
    Each distinct winner is re-evaluated with fresh reps on a disjoint stream
    block. This removes reuse-of-noise bias at those points. It is NOT a
    confidence interval for the true extrema, and it does not show that the
    pilot picked the true extremizer (verifier t_1f00fc3b, item 5).
    """
    reps = config.REPS_ESTIMAND
    lo, hi = config.RECHECK_OFFSET, config.RECHECK_OFFSET + reps - 1
    out = {"reps": reps, "stream_offsets": [lo, hi], "candidates": []}
    for est, key, se_key in (("Theta_hm", "theta2", "se_theta2"),
                             ("Theta_exp", "delta_spill", "se_spill")):
        vals = np.array([p[key] for p in image_points])
        for end, j in (("lower", int(np.nanargmin(vals))), ("upper", int(np.nanargmax(vals)))):
            p = image_points[j]
            if est == "Theta_hm":
                fresh = evaluate_thetas(world, p["c"], reps=reps, offset0=lo)
            else:
                fresh = evaluate_spill(world, p["c"], reps=reps, offset0=lo)
            out["candidates"].append({
                "image": est, "endpoint": end, "nroy_index": p["nroy_index"],
                "pilot_value": p[key], "pilot_pointwise_se": p[se_key],
                "fresh_value": fresh[key], "fresh_pointwise_se": fresh[se_key],
            })
    return out


def _rel(path: Path) -> str:
    return str(Path(path).relative_to(config.ROOT))


def _dump_json(path: Path, obj) -> Path:
    path.write_text(json.dumps(_jsonable(obj), indent=2))
    print(f"wrote {path}")
    return path


def _dump(payload: dict, res_dir: Path, source: str) -> None:
    _dump_json(res_dir / "poc_results.json", payload)
    lock = _write_lock(source)
    print(f"lock file {lock}")


def main():
    sys.path.insert(0, str(config.ROOT / "src"))
    source = sys.argv[1] if len(sys.argv) > 1 else "planted"
    payload = run_poc(source)
    print(json.dumps({k: payload[k] for k in ("finding_hm", "n_nroy", "tau", "notes") if k in payload}, indent=2))


if __name__ == "__main__":
    main()

"""End-to-end run: history matching, the two images, the two foils.

Steps: load z -> waves -> NROY -> 400 sampled points -> Theta_hm, Theta_exp ->
the two diagnostic points (min-I, median-I) -> both foils.
An empty NROY is a finding (F-EMPTY). tau and delta are never loosened.

Usage:  python -m poc_abm.pipeline [planted|worldbank]     (default: planted)
Outputs, per source S: results/S/poc_results.json, results/S/image_points.json,
figures/S/{waves,overlay,image_points,empty}.png, locks/freeze-S.txt.
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
    """HEAD sha, with '+dirty' if tracked files differ from it."""
    repo = Path(__file__).resolve().parents[2]
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
    dirty = subprocess.run(["git", "diff", "--quiet", "HEAD"], cwd=repo).returncode != 0
    return sha + ("+dirty" if dirty else "")


SOURCES = ("planted", "worldbank")


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
        "delta": [config.DELTA[n] for n in ("level_imm", "gradient_edu", "level_internet")],
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
    for i in idx:
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
    theta2s = np.array([p["theta2"] for p in image_points])
    spills = np.array([p["delta_spill"] for p in image_points])
    Theta_hm = interval_image(theta2s)
    Theta_exp = interval_image(spills)
    payload["Theta_hm"] = list(Theta_hm)
    payload["Theta_exp"] = list(Theta_exp)
    payload["n_theta_sample"] = len(image_points)
    # Monte Carlo SE of each endpoint = SE of the point that attains it.
    payload["image_endpoint_se"] = {
        "Theta_hm": [image_points[int(np.nanargmin(theta2s))]["se_theta2"],
                     image_points[int(np.nanargmax(theta2s))]["se_theta2"]],
        "Theta_exp": [image_points[int(np.nanargmin(spills))]["se_spill"],
                      image_points[int(np.nanargmax(spills))]["se_spill"]],
    }
    _dump_json(res_dir / "image_points.json", image_points)

    worlds = diagnostic_worlds(hm["nroy"], hm["I"])
    findings = {}
    for key in ("min_I", "median_I"):
        row = worlds[key]["c_row"]
        c = row_to_c(row, hm["param_names"])
        th = evaluate_thetas(world, c, reps=config.REPS_ESTIMAND)
        sp = evaluate_spill(world, c, reps=config.REPS_ESTIMAND)
        foils = run_foils(world, c, th["theta2"], sp["delta_spill"])
        foil1, foil2 = foils["foil1"], foils["foil2"]
        decomp = policy_gap_decomposition(world, c, displayed_beta=foil1["beta"])
        findings[key] = {
            "I": worlds[key]["I"],
            "nroy_index": worlds[key]["index"],
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
            "foil1_gap_decomposition": decomp,
            "foil2_estimate": foil2["delta_spill"],
            "foil2_se": foil2["se_spill"],
            "foil2_merged_s0b": foil2["merged_s0b"],
            "foil2_ci": list(foil2["ci_spill"]),
            "foil2_vs_Theta_exp": classify_interval(foil2["ci_spill"], Theta_exp),
            "foil2_covers_truth": foils["foil2_covers_truth"],
        }
    payload["findings"] = findings
    payload["notes"].append(
        "covers_truth is reported, never a stop: a correct 95% interval misses "
        "the truth 5% of the time. The check on the Foil 2 code is "
        "scripts/check_foil2_coverage.py (PLAN items 11, 14)."
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
            "theta2_star": payload["theta_star"]["theta2"],
            "spill_star": payload["spill_star"]["delta_spill"],
        }
    out.append(_rel(draw_overlay(overlay, fig_dir / "overlay.png")))
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

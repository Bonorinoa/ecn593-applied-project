"""End-to-end PoC runner — A1 through A7, or F-EMPTY if the box cannot hit z.

Empty NROY is a finding. τ and δ are never loosened.
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
    sample_nroy_rows,
)
from poc_abm.figures import draw_empty, draw_overlay
from poc_abm.history_matching import run_waves, tau_threshold
from poc_abm.kernel import World
from poc_abm.moments import MOMENT_NAMES, load_frozen_z, sampling_variances
from poc_abm.diagnostic import classify_interval, measure_image_theta2, run_foils


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


def run_poc() -> dict:
    config.RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    config.FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    z, audit = load_frozen_z()
    sampling = sampling_variances(audit)
    tau = tau_threshold()
    world = World()
    th_star = evaluate_thetas(world, config.C_STAR, reps=config.REPS_ESTIMAND)
    sp_star = evaluate_spill(world, config.C_STAR, reps=config.REPS_ESTIMAND)

    hm = run_waves(world, z, sampling)
    payload = {
        "freeze_date": "2026-08-26 / AMENDMENT-02 2026-08-27",
        "ran_at": datetime.now(timezone.utc).isoformat(),
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

    if hm["finding"] == "F-EMPTY":
        payload["notes"].append(
            "F-EMPTY: no c in the frozen box C has I(c) ≤ τ. "
            "τ and δ were not touched. This rejects the pair (kernel, z), "
            "not a license to widen the box after seeing the waves."
        )
        payload["notes"].append(
            "Closest M vs z is a discrepancy report, not a calibrated world."
        )
        fig = draw_empty(
            {
                "z": z.tolist(),
                "tau": tau,
                "closest": hm["closest"],
                "wave_I_stats": hm["wave_I_stats"],
            },
            config.FIGURES_DIR / "overlay.png",
        )
        payload["figure"] = str(fig)
        _dump(payload)
        return payload

    rng = np.random.default_rng(config.SEED_HM + 1)
    sample = sample_nroy_rows(hm["nroy"], config.THETA_SAMPLE, rng)
    # I values for the sampled rows: match by scanning (NROY is small enough)
    # For the sample we recompute nothing about I; pair by taking the same
    # indices when we subsampled from the full NROY.
    # sample_nroy_rows doesn't return indices — evaluate θ on the sample, and
    # pick c0 from FULL NROY via I.
    theta2s = []
    spills = []
    for row in sample:
        c = row_to_c(row, hm["param_names"])
        th = evaluate_thetas(world, c, reps=config.REPS_ESTIMAND)
        sp = evaluate_spill(world, c, reps=config.REPS_ESTIMAND)
        theta2s.append(th["theta2"])
        spills.append(sp["delta_spill"])
    Theta_hm = interval_image(np.array(theta2s))
    Theta_exp = interval_image(np.array(spills))
    payload["Theta_hm"] = list(Theta_hm)
    payload["Theta_exp"] = list(Theta_exp)
    payload["n_theta_sample"] = int(sample.shape[0])

    worlds = diagnostic_worlds(hm["nroy"], hm["I"])
    overlay = {"worlds": {}}
    findings = {}
    for key in ("min_I", "median_I"):
        row = worlds[key]["c_row"]
        c = row_to_c(row, hm["param_names"])
        th = evaluate_thetas(world, c, reps=config.REPS_ESTIMAND)
        sp = evaluate_spill(world, c, reps=config.REPS_ESTIMAND)
        foils = run_foils(world, c, th["theta2"], sp["delta_spill"])
        cv = measure_image_theta2(world, c, seed_offset=0)
        foil1 = foils["forest"]["m1"]
        foil1_ci = foil1["ci"]
        foil1_name = foil1["estimator"]
        e2_ci = foils["e2"]["ci_spill"]
        findings[key] = {
            "foil1_estimator": foil1_name,
            "forest_vs_Theta_hm": classify_interval(foil1_ci, Theta_hm),
            "e2_vs_Theta_exp": classify_interval(e2_ci, Theta_exp),
            "e2_oracle_ok": foils["e2_oracle_ok"],
            "I": worlds[key]["I"],
            "c": c,
            "theta2_true": th["theta2"],
            "spill_true": sp["delta_spill"],
            "foil1_ci": list(foil1_ci),
            "forest_ci": list(foil1_ci),
            "e2_ci": list(e2_ci),
            "Theta_cv": list(cv["Theta_cv"]),
            "admitted_measures": list(cv["admitted_names"]),
        }
        overlay["worlds"][key] = {
            "Theta_hm": Theta_hm,
            "Theta_exp": Theta_exp,
            "theta2_true": th["theta2"],
            "spill_true": sp["delta_spill"],
            "foil1_ci": foil1_ci,
            "foil1_label": foil1_name,
            "forest_ci": foil1_ci,
            "e2_ci": e2_ci,
            "Theta_cv": cv["Theta_cv"],
            "theta2_star": th_star["theta2"],
            "spill_star": sp_star["delta_spill"],
        }
        if not foils["e2_oracle_ok"]:
            payload["notes"].append(
                f"ORACLE GATE FAILED at {key}: E2 CI missed δ_spill,true. "
                "Harness broken — findings at this world do not count."
            )
    payload["findings"] = findings
    fig = draw_overlay(overlay, config.FIGURES_DIR / "overlay.png")
    payload["figure"] = str(fig)
    _dump(payload)
    return payload


def _dump(payload: dict) -> None:
    path = config.RESULTS_DIR / "poc_results.json"
    path.write_text(json.dumps(_jsonable(payload), indent=2))
    try:
        lock = _write_lock("A3")
        print(f"lock file {lock}")
    except Exception as exc:
        print(f"lock skipped: {exc}")
    print(f"wrote {path}")


def main():
    sys.path.insert(0, str(config.ROOT / "src"))
    payload = run_poc()
    print(json.dumps({k: payload[k] for k in ("finding_hm", "n_nroy", "tau", "notes") if k in payload}, indent=2))


if __name__ == "__main__":
    main()

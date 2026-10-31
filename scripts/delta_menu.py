#!/usr/bin/env python
"""Amendment A1 of docs/preregistration-v2.md: the delta menu.

The main design uses delta = 0.02 for the two level moments. This script asks
how the image changes if that one assumption changes. It is a menu of answers
indexed by an assumption, not a test, and never a way to pick a delta.

Menu: delta for sq_level and pilot_level in {0.02, 0.01, 0.005}. The two
correlation moments keep their delta. tau, C, the moments, z and every seed
are unchanged. Per entry the script reruns only what delta touches: the waves,
NROY, the 400-point image sample, Theta_hm, Theta_exp and nroy_param_spread.
It does NOT rerun the foils. The c* intervals of both foils do not depend on
delta, so they are read from results/planted/poc_results.json and classified
against each entry's images.

Built-in check: the delta = 0.02 entry must reproduce the main run's Theta_hm,
Theta_exp, n_nroy, wave_kept and nroy_param_spread exactly. If not, the script
exits non-zero and writes nothing.

Usage:  python scripts/delta_menu.py          (about 4 min per entry)
Output: results/sensitivity/delta_menu.json
"""
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from poc_abm import config  # noqa: E402
from poc_abm.diagnostic import classify_interval  # noqa: E402
from poc_abm.estimand import (  # noqa: E402
    evaluate_spill,
    evaluate_thetas,
    interval_image,
    row_to_c,
    sample_nroy_index,
)
from poc_abm.history_matching import run_waves, tau_threshold  # noqa: E402
from poc_abm.kernel import World  # noqa: E402
from poc_abm.moments import MOMENT_NAMES, load_z, sampling_variances  # noqa: E402
from poc_abm.pipeline import _git_commit, _jsonable, nroy_param_spread  # noqa: E402

# The menu, as written in amendment A1. The tag is the name used in the paper's macros.
LEVEL_MOMENTS = ("sq_level", "pilot_level")      # the two moments whose delta moves
MENU = (("Main", 0.02), ("Half", 0.01), ("Quarter", 0.005))
MAIN_TAG = "Main"                                # the entry that must equal the main run

MAIN_RESULTS = ROOT / "results" / "planted" / "poc_results.json"
OUT = ROOT / "results" / "sensitivity" / "delta_menu.json"


def delta_for(level: float) -> dict:
    """The design's delta with the two level moments set to `level`. config.DELTA is not changed."""
    delta = dict(config.DELTA)
    for name in LEVEL_MOMENTS:
        delta[name] = level
    return delta


def run_entry(world, z, sampling, delta: dict, star_foils: dict, label: str = "") -> dict:
    """One menu entry: waves, NROY, the image sample, both images, spread, c* classification.

    `star_foils` = {"foil1_ci": [lo, hi], "foil2_ci": [lo, hi]}: the c* intervals of the main run.
    An empty NROY is a finding (F-EMPTY): the entry then has no images.
    """
    hm = run_waves(world, z, sampling, delta=delta)
    entry = {
        "delta": [delta[n] for n in MOMENT_NAMES],
        "tau": hm["tau"],
        "finding_hm": hm["finding"],
        "wave_kept": hm["wave_kept"],
        "n_nroy": int(hm["nroy"].shape[0]),
        "param_names": hm["param_names"],
        "n_theta_sample": 0,
        "Theta_hm": None,
        "Theta_exp": None,
        "nroy_param_spread": None,
        "alpha_kappa_corr": None,
        "foil1_vs_Theta_hm": None,
        "foil2_vs_Theta_exp": None,
    }
    if hm["finding"] == "F-EMPTY":
        return entry

    rng = np.random.default_rng(config.SEED_THETA_SAMPLE)
    idx = sample_nroy_index(hm["nroy"].shape[0], config.THETA_SAMPLE, rng)
    print(f"{label}images: theta2 and delta_spill at {len(idx)} sampled NROY points", flush=True)
    image_points = []
    for n_done, i in enumerate(idx, 1):
        c = row_to_c(hm["nroy"][i], hm["param_names"])
        th = evaluate_thetas(world, c, reps=config.REPS_ESTIMAND)
        sp = evaluate_spill(world, c, reps=config.REPS_ESTIMAND)
        image_points.append({"c": c, "theta2": th["theta2"], "delta_spill": sp["delta_spill"]})
        if n_done % 50 == 0:
            print(f"  {label}image points done {n_done}/{len(idx)}", flush=True)
    Theta_hm = interval_image(np.array([p["theta2"] for p in image_points]))
    Theta_exp = interval_image(np.array([p["delta_spill"] for p in image_points]))
    entry["n_theta_sample"] = len(image_points)
    entry["Theta_hm"] = list(Theta_hm)
    entry["Theta_exp"] = list(Theta_exp)
    entry["foil1_vs_Theta_hm"] = classify_interval(star_foils["foil1_ci"], Theta_hm)
    entry["foil2_vs_Theta_exp"] = classify_interval(star_foils["foil2_ci"], Theta_exp)
    if len(image_points) >= 2:                      # a standard deviation needs two points
        spread = nroy_param_spread(image_points, hm["param_names"])
        names = spread["param_names"]
        entry["nroy_param_spread"] = spread
        entry["alpha_kappa_corr"] = spread["correlation_matrix"][names.index("alpha")][names.index("kappa")]
    return entry


def check_main_entry(entry: dict, main: dict) -> None:
    """The delta = 0.02 entry must equal the main run, exactly. Exit non-zero on any difference."""
    mine, theirs = _jsonable(entry), _jsonable(main)
    bad = [k for k in ("delta", "tau", "Theta_hm", "Theta_exp", "n_nroy", "wave_kept", "nroy_param_spread")
           if mine[k] != theirs[k]]
    if bad:
        sys.exit(f"CONSISTENCY CHECK FAILED: the delta = {MENU[0][1]} entry differs from "
                 f"{MAIN_RESULTS.relative_to(ROOT)} in: {', '.join(bad)}")


def run_menu(menu=MENU, main: dict | None = None) -> dict:
    main = json.loads(MAIN_RESULTS.read_text()) if main is None else main
    star = main["findings"]["c_star"]
    star_foils = {"foil1_ci": star["foil1_ci"], "foil2_ci": star["foil2_ci"]}
    z, audit = load_z("planted")
    sampling = sampling_variances(audit)
    world = World()
    assert tau_threshold() == main["tau"], "tau differs from the main run"
    entries = {}
    for tag, level in menu:
        t0 = time.time()
        print(f"entry {tag}: delta_level = {level} (sq_level, pilot_level); "
              f"corr deltas {config.DELTA['sq_corr_x1']}, {config.DELTA['sq_peer_corr']}", flush=True)
        entries[tag] = {"delta_level": level,
                        **run_entry(world, z, sampling, delta_for(level), star_foils, label=f"{tag}: ")}
        e = entries[tag]
        print(f"entry {tag}: finding {e['finding_hm']}, wave_kept {e['wave_kept']}, n_nroy {e['n_nroy']}, "
              f"Theta_hm {e['Theta_hm']}, foil1 {e['foil1_vs_Theta_hm']}, foil2 {e['foil2_vs_Theta_exp']} "
              f"({time.time() - t0:.0f} s)", flush=True)
        if tag == MAIN_TAG:
            check_main_entry(e, main)
            print("check: the delta = 0.02 entry reproduces the main run (Theta_hm, Theta_exp, n_nroy, "
                  "wave_kept, nroy_param_spread)", flush=True)
    return {
        "git_commit": _git_commit(),
        "ran_at": datetime.now(timezone.utc).isoformat(),
        "amendment": "A1 (docs/preregistration-v2.md)",
        "moment_names": list(MOMENT_NAMES),
        "level_moments": list(LEVEL_MOMENTS),
        "main_entry": MAIN_TAG,
        "consistency_check": "passed: the main entry equals results/planted/poc_results.json",
        "c_star_foil_intervals": star_foils,
        "entries": entries,
        "notes": ["A menu of answers indexed by delta, not a test. It is never used to pick a delta.",
                  "The c* intervals are read from the main run; the foils are not rerun."],
    }


def main():
    result = run_menu()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(_jsonable(result), indent=2))
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()

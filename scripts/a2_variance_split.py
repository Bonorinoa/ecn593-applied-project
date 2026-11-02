#!/usr/bin/env python
"""Run addendum A2.1 without changing an A2 estimator or result."""
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from poc_abm import config  # noqa: E402
from poc_abm.estimand import hajek_linear_contrast  # noqa: E402
from poc_abm.kernel import World, simulate_panel, stream_seed  # noqa: E402
from check_foil2_coverage import _design_panel  # noqa: E402
import interference_tradeoff as tradeoff  # noqa: E402

POINTS = ("min_I", "median_I", "c_star")
ANALYSTS = ("A1", "A2", "Spill")
OUT = ROOT / "results" / "interference" / "variance_split.json"
V3_LOG = ROOT / "reviews" / "probes" / "V3" / "probe_a2.log"


def _spill(world, y, d):
    return hajek_linear_contrast(
        world,
        y,
        d,
        cells=[{"stratum": "S0c"}, {"stratum": "S0a"}],
        coefficients=[1.0, -1.0],
        return_variance_parts=True,
    )


def _analysts(world, y, d):
    return {
        "A1": tradeoff.analyst_a1(world, y, d, return_variance_parts=True),
        "A2": tradeoff.analyst_a2(world, y, d, return_variance_parts=True),
        "Spill": _spill(world, y, d),
    }


def _split(result):
    parts = result["variance_parts"]
    reported = float(parts["reported"])
    main = float(parts["positive_joint_probability"])
    young = float(parts["young_bound"])
    return {
        "reported_variance": reported,
        "positive_joint_probability_term": main,
        "young_bound_term": young,
        "young_share": young / reported if reported != 0 else float("nan"),
    }


def one_panel_splits(world, c):
    """Split the three reported variances on the declared one-panel draw."""
    y, d = simulate_panel(world, c, "random", config.FOIL_PANEL_OFFSET)
    return {name: _split(result) for name, result in _analysts(world, y, d).items()}


def _design_summary(draws, redraws):
    valid = [draw for draw in draws if not draw["undefined"] and np.isfinite(draw["estimate"])]
    if len(valid) < 2:
        nan = float("nan")
        return {
            "redraws": redraws,
            "n_defined": len(valid),
            "sd": nan,
            "mean_main_term_se2_over_design_variance": nan,
            "mean_full_se2_over_design_variance": nan,
        }
    estimates = np.asarray([draw["estimate"] for draw in valid], dtype=float)
    design_variance = float(np.var(estimates, ddof=1))
    main = np.asarray(
        [draw["variance_parts"]["positive_joint_probability"] for draw in valid],
        dtype=float,
    )
    full = np.asarray([draw["variance_parts"]["reported"] for draw in valid], dtype=float)
    return {
        "redraws": redraws,
        "n_defined": len(valid),
        "sd": float(np.sqrt(design_variance)),
        "mean_main_term_se2_over_design_variance": float(np.mean(main) / design_variance),
        "mean_full_se2_over_design_variance": float(np.mean(full) / design_variance),
    }


def _v3_probe_design():
    """Read V3's committed c_star A1 comparison instead of copying its numbers."""
    for line in V3_LOG.read_text().splitlines():
        if line.startswith("DESIGN "):
            row = json.loads(line.removeprefix("DESIGN "))
            return {
                "design_sd": float(row["own_sd"]),
                "main_term_ratio": float(row["main_se2_over_design_var"]),
                "full_ratio": float(row["se2_over_design_var"]),
                "redraws": int(row["reps"]),
                "assignment_seed_scheme": "20261101 + r",
            }
    raise ValueError(f"V3 DESIGN row not found in {V3_LOG}")


def _relative_difference(left, right):
    return abs(left - right) / abs(right) if right != 0 else abs(left - right)


def _v3_check(c_star_a1, v3_probe):
    ours = {
        "design_sd": c_star_a1["sd"],
        "main_term_ratio": c_star_a1["mean_main_term_se2_over_design_variance"],
        "full_ratio": c_star_a1["mean_full_se2_over_design_variance"],
    }
    relative = {name: _relative_difference(ours[name], v3_probe[name]) for name in ours}
    tolerances = {"design_sd": 0.15, "main_term_ratio": 0.30, "full_ratio": 0.30}
    agrees = all(relative[name] <= tolerances[name] for name in ours)
    return {
        "ours": ours,
        "v3_probe": v3_probe,
        "relative_difference": relative,
        "relative_tolerance": tolerances,
        "agrees_within_mc_noise": agrees,
        "note": "Different assignment streams; tolerances cover Monte Carlo variation from 400 redraws.",
    }


def build_variance_split(
    main_results,
    world=None,
    design_redraws=None,
    offset_base=None,
    v3_probe="load",
):
    """Build the A2.1 readout from saved points and fixed-noise assignment redraws."""
    world = World() if world is None else world
    design_redraws = config.INTERFERENCE_DESIGN_REDRAWS if design_redraws is None else design_redraws
    offset_base = config.INTERFERENCE_DESIGN_OFFSET_BASE if offset_base is None else offset_base
    payload = {
        "R_design": design_redraws,
        "offset_base": offset_base,
        "foil_panel_offset": config.FOIL_PANEL_OFFSET,
        "points": {},
    }
    progress_every = max(1, min(25, design_redraws))
    for point in POINTS:
        c = main_results["findings"][point]["c"]
        one_panel = one_panel_splits(world, c)
        draws = {name: [] for name in ANALYSTS}
        for r in range(design_redraws):
            assignment_offset = offset_base + r
            assignment_seed = stream_seed("assign:random", assignment_offset)
            y, d = _design_panel(world, c, config.FOIL_PANEL_OFFSET, assignment_seed)
            for name, result in _analysts(world, y, d).items():
                draws[name].append(result)
            if (r + 1) % progress_every == 0:
                print(f"  {point}: design redraws {r + 1}/{design_redraws}", flush=True)
        payload["points"][point] = {
            name: {
                "one_panel": one_panel[name],
                "design": _design_summary(draws[name], design_redraws),
            }
            for name in ANALYSTS
        }
    if v3_probe is not None:
        reference = _v3_probe_design() if v3_probe == "load" else v3_probe
        check = _v3_check(payload["points"]["c_star"]["A1"]["design"], reference)
        payload["v3_c_star_a1_check"] = check
        ours = check["ours"]
        v3 = check["v3_probe"]
        print(
            "V3 check A1 c_star: "
            f"ours sd={ours['design_sd']:.6g}, main={ours['main_term_ratio']:.6g}, full={ours['full_ratio']:.6g}; "
            f"V3 sd={v3['design_sd']:.6g}, main={v3['main_term_ratio']:.6g}, full={v3['full_ratio']:.6g}; "
            f"agrees={check['agrees_within_mc_noise']}",
            flush=True,
        )
    return payload


def _git_commit():
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    paths = ["config", "src", "scripts", "data", "requirements.txt", "requirements-dev.txt"]
    dirty = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", *paths], cwd=ROOT).returncode != 0
    return sha + ("+dirty" if dirty else "")


def main():
    source = json.loads((ROOT / "results" / "planted" / "poc_results.json").read_text())
    print(
        f"A2.1 variance split: {config.INTERFERENCE_DESIGN_REDRAWS} fixed-noise design redraws "
        "at each of 3 points",
        flush=True,
    )
    payload = build_variance_split(source)
    payload = {"git_commit": _git_commit(), "ran_at": datetime.now(timezone.utc).isoformat(), **payload}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}", flush=True)
    if not payload["v3_c_star_a1_check"]["agrees_within_mc_noise"]:
        raise SystemExit("A2.1 c_star A1 redraw does not agree with V3 within the declared Monte Carlo tolerances")


if __name__ == "__main__":
    main()

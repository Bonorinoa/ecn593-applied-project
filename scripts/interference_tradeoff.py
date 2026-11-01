#!/usr/bin/env python
"""Run amendment A2 without rerunning the history-matching waves."""
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.stats import beta, norm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from poc_abm import config  # noqa: E402
from poc_abm.diagnostic import classify_interval, covers_truth, foil1_policy  # noqa: E402
from poc_abm.estimand import (  # noqa: E402
    exposure_share,
    hajek_linear_contrast,
    maybe_merge_s0b,
    stratum_labels,
)
from poc_abm.kernel import World, assign, simulate_panel  # noqa: E402

POINTS = ("min_I", "median_I", "c_star")
ANALYSTS = ("A0", "A1", "A2")
OUT = ROOT / "results" / "interference" / "tradeoff.json"


def _panel_merge(world, d, cut, min_n):
    labels = stratum_labels(d, exposure_share(world, d), cut)
    return maybe_merge_s0b(labels, min_n)[1]


def _degree_labels(world, cut, merged):
    d2 = assign(world, "degree", np.random.default_rng(0))
    labels = stratum_labels(d2, exposure_share(world, d2), cut)
    if merged:
        labels = labels.copy()
        labels[labels == "S0b"] = "S0c"
    return d2, labels


def analyst_a1(world, y, d, cut=None, min_n=None):
    """A1: transport exposure means with the degree-policy exposure shares."""
    cut = config.EXPOSURE_SHARE_CUT if cut is None else cut
    min_n = config.STRATUM_MIN_N if min_n is None else min_n
    merged = _panel_merge(world, d, cut, min_n)
    _, policy_labels = _degree_labels(world, cut, merged)
    cells, coefficients, weights = [], [], {}
    for name in ("S1", "S0b", "S0c"):
        weight = float(np.mean(policy_labels == name))
        if weight > 0:
            cells.append({"stratum": name})
            coefficients.append(weight)
            weights[name] = weight
    baseline_coefficient = -sum(coefficients)
    cells.append({"stratum": "S0a"})
    coefficients.append(baseline_coefficient)
    result = hajek_linear_contrast(world, y, d, cells, coefficients, cut=cut, min_n=min_n)
    result["interval"] = result.pop("ci")
    result["weights"] = weights
    return result


def analyst_a2(world, y, d, cut=None, min_n=None):
    """A2: A1 with fixed degree-policy H and L node bins."""
    cut = config.EXPOSURE_SHARE_CUT if cut is None else cut
    min_n = config.STRATUM_MIN_N if min_n is None else min_n
    merged = _panel_merge(world, d, cut, min_n)
    d2, policy_labels = _degree_labels(world, cut, merged)
    high = d2 > 0.5
    low = ~high
    high_weight = float(high.mean())
    cells = [
        {"stratum": "S1", "nodes": high},
        {"stratum": "S0a", "nodes": high},
    ]
    coefficients = [high_weight, -high_weight]
    weights = {"S1,H": high_weight}
    low_total = 0.0
    for name in ("S1", "S0b", "S0c"):
        weight = float(np.sum((policy_labels == name) & low) / world.n)
        if weight > 0:
            cells.append({"stratum": name, "nodes": low})
            coefficients.append(weight)
            weights[f"{name},L"] = weight
            low_total += weight
    if low_total > 0:
        cells.append({"stratum": "S0a", "nodes": low})
        coefficients.append(-low_total)
    result = hajek_linear_contrast(world, y, d, cells, coefficients, cut=cut, min_n=min_n)
    result["interval"] = result.pop("ci")
    result["weights"] = weights
    return result


def analyst_a0(world, y, d):
    """A0 reuses the existing Foil 1 implementation."""
    result = foil1_policy(world, y, d)
    z = float(norm.ppf(0.5 + 0.5 * config.HM_CONFIDENCE))
    lo, hi = result["ci"]
    return {"estimate": result["estimate"], "se": (hi - lo) / (2.0 * z),
            "interval": result["ci"], "undefined": False}


def panel_analysts(world, c, offset):
    y_degree, d_degree = simulate_panel(world, c, "degree", offset)
    y_random, d_random = simulate_panel(world, c, "random", offset)
    return {
        "A0": analyst_a0(world, y_degree, d_degree),
        "A1": analyst_a1(world, y_random, d_random),
        "A2": analyst_a2(world, y_random, d_random),
    }


def clopper_pearson(successes, trials, confidence=0.95):
    if trials == 0:
        return [float("nan"), float("nan")]
    alpha = 1.0 - confidence
    lo = 0.0 if successes == 0 else float(beta.ppf(alpha / 2.0, successes, trials - successes + 1))
    hi = 1.0 if successes == trials else float(beta.ppf(1.0 - alpha / 2.0, successes + 1, trials - successes))
    return [lo, hi]


def summarize(draws, truth, theta_width):
    valid = [d for d in draws if not d["undefined"] and np.isfinite(d["estimate"])]
    undefined = len(draws) - len(valid)
    if not valid:
        nan = float("nan")
        return {"mean": nan, "bias": nan, "sd": nan, "rmse": nan, "mean_se": nan,
                "se_over_sd": nan, "coverage": nan,
                "coverage_clopper_pearson_95": [nan, nan], "mean_width": nan,
                "width_over_theta_hm": nan, "undefined_count": undefined, "n_defined": 0}
    estimates = np.array([d["estimate"] for d in valid], dtype=float)
    ses = np.array([d["se"] for d in valid], dtype=float)
    widths = np.array([d["interval"][1] - d["interval"][0] for d in valid], dtype=float)
    covered = np.array([covers_truth(d["interval"], truth) for d in valid], dtype=bool)
    sd = float(np.std(estimates, ddof=1)) if len(valid) > 1 else float("nan")
    mean_se = float(np.mean(ses))
    successes = int(covered.sum())
    return {
        "mean": float(np.mean(estimates)),
        "bias": float(np.mean(estimates) - truth),
        "sd": sd,
        "rmse": float(np.sqrt(np.mean((estimates - truth) ** 2))),
        "mean_se": mean_se,
        "se_over_sd": mean_se / sd if sd > 0 else float("nan"),
        "coverage": float(np.mean(covered)),
        "coverage_clopper_pearson_95": clopper_pearson(successes, len(valid)),
        "mean_width": float(np.mean(widths)),
        "width_over_theta_hm": float(np.mean(widths) / theta_width),
        "undefined_count": undefined,
        "n_defined": len(valid),
    }


def _one_panel(result, truth, planted_truth, theta_hm):
    interval = result["interval"]
    return {
        "estimate": result["estimate"],
        "se": result["se"],
        "interval": list(interval),
        "covers_truth": covers_truth(interval, truth),
        "covers_planted_truth": covers_truth(interval, planted_truth),
        "vs_Theta_hm": classify_interval(interval, theta_hm),
        "undefined": result["undefined"],
    }


def build_tradeoff(main_results, world=None, repetitions=None, offset_base=None):
    """Build the A2 result from saved main points and fresh panel offsets."""
    world = World() if world is None else world
    repetitions = config.INTERFERENCE_REPETITIONS if repetitions is None else repetitions
    offset_base = config.INTERFERENCE_OFFSET_BASE if offset_base is None else offset_base
    theta_hm = main_results["Theta_hm"]
    theta_width = float(theta_hm[1] - theta_hm[0])
    planted_truth = float(main_results["theta_star"]["theta2"])
    payload = {"repetitions": repetitions, "offset_base": offset_base,
               "foil_panel_offset": config.FOIL_PANEL_OFFSET,
               "Theta_hm": theta_hm, "theta_hm_width": theta_width, "points": {}}
    for point_name in POINTS:
        finding = main_results["findings"][point_name]
        c = finding["c"]
        truth = float(finding["theta2_true"])
        one = panel_analysts(world, c, config.FOIL_PANEL_OFFSET)
        draws = {name: [] for name in ANALYSTS}
        for r in range(repetitions):
            panel = panel_analysts(world, c, offset_base + r)
            for name in ANALYSTS:
                draws[name].append(panel[name])
            if (r + 1) % max(1, min(25, repetitions)) == 0:
                print(f"  {point_name}: panels {r + 1}/{repetitions}", flush=True)
        payload["points"][point_name] = {
            "c": c,
            "theta2_true": truth,
            "theta2_planted": planted_truth,
            "one_panel": {name: _one_panel(one[name], truth, planted_truth, theta_hm)
                          for name in ANALYSTS},
            "repeated": {name: summarize(draws[name], truth, theta_width) for name in ANALYSTS},
        }
    return payload


def _git_commit():
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    paths = ["config", "src", "scripts", "data", "requirements.txt", "requirements-dev.txt"]
    dirty = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", *paths], cwd=ROOT).returncode != 0
    return sha + ("+dirty" if dirty else "")


def main():
    source = json.loads((ROOT / "results" / "planted" / "poc_results.json").read_text())
    print(f"interference tradeoff: {config.INTERFERENCE_REPETITIONS} panels at each of 3 points", flush=True)
    payload = build_tradeoff(source)
    payload = {"git_commit": _git_commit(), "ran_at": datetime.now(timezone.utc).isoformat(), **payload}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}", flush=True)


if __name__ == "__main__":
    main()

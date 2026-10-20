"""Coverage of the Foil 2 interval: one gate and one reported result.

GATE (does the implemented variance estimate understate on average?). Outcomes
are built to obey the exposure map exactly: y_i = b_i + 0.05 * 1{S1} + 0.03 * 1{S0c},
with b fixed, so the true spillover is exactly 0.03. This is an
implementation-specific, repeated-assignment calibration check MOTIVATED by
Aronow-Samii (2017). It is not a direct test of their theorem: their exact
result is for Horvitz-Thompson totals with exact joint probabilities, while this
code uses Hajek means, a first-order linearization, and one simulated table of
joint probabilities. Rule (one-sided falsification, written before the run):
FAIL iff mean(SE^2)/Var + 1.645 * paired bootstrap SE < 1, on 10,000
assignments from a fresh seed block (PLAN item 11). Coverage of the nominal 95%
interval is reported with an exact Clopper-Pearson interval, not gated.

RESULT (how does a careful one-world analyst do on this kernel?). For each
point (c*, min-I, median-I): R random-arm panels from the kernel, and coverage
of the code's target (evaluate_spill). Then the same with the noise path held
fixed and only the assignment redrawn. This is reported, not gated: the
kernel breaks the exposure map (people two steps from a treated person still
feel the campaign), so under-coverage here is a finding about Foil 2.

Output: results/checks/foil2_coverage.json. Exit code 1 if the gate fails.

Run from the repo root:
    env -u PYTHONPATH PYTHONPATH=src python scripts/check_foil2_coverage.py
"""
import json
import sys
from pathlib import Path

import numpy as np
from scipy.stats import beta

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from poc_abm import config  # noqa: E402
from poc_abm.estimand import (  # noqa: E402
    evaluate_spill,
    exposure_share,
    hajek_contrasts,
    maybe_merge_s0b,
    stratum_labels,
    true_spill_from_panel,
)
from poc_abm.kernel import World, assign, logistic, simulate_panel, stream_seed  # noqa: E402

R = 200            # kernel panels per point (reported result)
R_DESIGN = 300     # assignment-only redraws per point (reported result)
R_GATE = 10_000    # map-consistent assignments for the gate
GATE_SEED = 1_000_000  # fresh block, declared before first use (PLAN item 11)
GATE_EFFECT_S1, GATE_EFFECT_S0C = 0.05, 0.03
BOOT_REPS, BOOT_SEED = 1_000, 20261020


def _design_panel(world, c, state_offset, assign_seed):
    """simulate_panel with the state stream fixed and the assignment seed chosen freely."""
    rs = np.random.default_rng(stream_seed("state", state_offset))
    y = rs.random(world.n)
    xw = world.X @ np.asarray(config.ETA_FIXED)
    d = assign(world, "random", np.random.default_rng(assign_seed))
    inv = 1.0 / world.degrees
    for t in range(config.HORIZON):
        treat = c["kappa"] * d * (t >= config.INTERVENTION_TIME)
        y = logistic(c["alpha"] + c["beta"] * y + c["gamma"] * (world.adjacency @ y) * inv
                     + xw + treat + c["sigma_eps"] * rs.standard_normal(world.n))
    return y, d


def gate(world):
    """Does the implemented variance estimate understate on average?

    Calibration check motivated by Aronow-Samii (2017), not a test of their
    theorem (Hajek + linearization + simulated pi). Rule declared before the run
    (PLAN item 11): ratio = mean(SE^2) / Var(estimate) over R_GATE map-consistent
    assignments on a fresh seed block. FAIL iff ratio + 1.645 * paired bootstrap
    SE(ratio) < 1 (one-sided falsification). Coverage is reported with an exact
    Clopper-Pearson interval and is not gated.
    """
    base, _ = simulate_panel(world, dict(config.C_STAR), "control", 0)  # realistic levels, held fixed
    est, se, hit = [], [], []
    for a in range(R_GATE):
        d = assign(world, "random", np.random.default_rng(GATE_SEED + a))
        lab = stratum_labels(d, exposure_share(world, d), config.EXPOSURE_SHARE_CUT)
        lab, _ = maybe_merge_s0b(lab, config.STRATUM_MIN_N)
        y = base + GATE_EFFECT_S1 * (lab == "S1") + GATE_EFFECT_S0C * (lab == "S0c")
        h = hajek_contrasts(world, y, d)
        lo, hi = h["ci_spill"]
        est.append(h["delta_spill"])
        se.append(h["se_spill"])
        hit.append(lo <= GATE_EFFECT_S0C <= hi)
    est, v = np.asarray(est), np.asarray(se) ** 2
    ratio = float(v.mean() / est.var(ddof=1))
    rng = np.random.default_rng(BOOT_SEED)
    boots = []
    for _ in range(BOOT_REPS):
        idx = rng.integers(0, R_GATE, R_GATE)
        boots.append(v[idx].mean() / est[idx].var(ddof=1))
    ratio_se = float(np.std(boots, ddof=1))
    hits = int(np.sum(hit))
    alpha = 1.0 - config.HM_CONFIDENCE
    cp_lo = float(beta.ppf(alpha / 2, hits, R_GATE - hits + 1)) if hits > 0 else 0.0
    cp_hi = float(beta.ppf(1 - alpha / 2, hits + 1, R_GATE - hits)) if hits < R_GATE else 1.0
    row = {
        "R": R_GATE, "seed_block_start": GATE_SEED, "truth": GATE_EFFECT_S0C,
        "mean_estimate": float(est.mean()),
        "variance_ratio": ratio, "variance_ratio_boot_se": ratio_se,
        "variance_ratio_upper_one_sided_95": ratio + 1.645 * ratio_se,
        "coverage": hits / R_GATE, "coverage_clopper_pearson_95": [cp_lo, cp_hi],
        "rule": "FAIL iff variance_ratio + 1.645 * boot SE < 1",
    }
    row["pass"] = bool(row["variance_ratio_upper_one_sided_95"] >= 1.0)
    print(f"GATE      mean(SE^2)/Var={ratio:.4f} (boot SE {ratio_se:.4f})  "
          f"coverage={row['coverage']:.4f} CP95=[{cp_lo:.4f}, {cp_hi:.4f}]  pass={row['pass']}", flush=True)
    return row


def kernel_result(world, name, c):
    """Coverage on panels from the kernel itself (reported, not gated)."""
    truth = evaluate_spill(world, c, reps=R)["delta_spill"]
    est, se, hit = [], [], []
    for r in range(R):
        y, d = simulate_panel(world, c, "random", r)
        h = hajek_contrasts(world, y, d)
        lo, hi = h["ci_spill"]
        est.append(h["delta_spill"])
        se.append(h["se_spill"])
        hit.append(lo <= truth <= hi)
    d_est, d_se, d_ci, d_true = [], [], [], []
    for a in range(R_DESIGN):
        y, d = _design_panel(world, c, 0, 10_000 + a)
        h = hajek_contrasts(world, y, d)
        d_est.append(h["delta_spill"])
        d_se.append(h["se_spill"])
        d_ci.append(h["ci_spill"])
        d_true.append(true_spill_from_panel(world, y, d)["delta_spill"])
    d_target = float(np.mean(d_true))
    row = {
        "truth": truth,
        "coverage": float(np.mean(hit)),
        "sd_estimate": float(np.std(est, ddof=1)),
        "mean_se": float(np.mean(se)),
        "design_target": d_target,
        "design_coverage": float(np.mean([lo <= d_target <= hi for lo, hi in d_ci])),
        "design_sd_estimate": float(np.std(d_est, ddof=1)),
        "design_mean_se": float(np.mean(d_se)),
    }
    print(f"{name:9s} coverage={row['coverage']:.3f} design={row['design_coverage']:.3f} "
          f"SE/SD={row['mean_se'] / row['sd_estimate']:.2f}", flush=True)
    return row


def main():
    run_path = ROOT / "results" / "planted" / "poc_results.json"
    if not run_path.exists():
        sys.exit("results/planted/poc_results.json not found: run the pipeline first "
                 "(the min-I and median-I points come from that run).")
    run = json.loads(run_path.read_text())
    points = {
        "c_star": dict(config.C_STAR),
        "min_I": run["findings"]["min_I"]["c"],
        "median_I": run["findings"]["median_I"]["c"],
    }
    world = World()
    out = {"nominal": config.HM_CONFIDENCE, "gate": gate(world),
           "kernel": {"R": R, "R_design": R_DESIGN, "points": {}}}
    for name, c in points.items():
        out["kernel"]["points"][name] = kernel_result(world, name, c)
    out["pass"] = out["gate"]["pass"]
    path = ROOT / "results" / "checks" / "foil2_coverage.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, indent=2))
    print(f"wrote {path.relative_to(ROOT)}  gate pass={out['pass']}")
    sys.exit(0 if out["pass"] else 1)


if __name__ == "__main__":
    main()

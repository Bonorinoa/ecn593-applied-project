"""V3 independent probe for amendment A2.

Recomputes A1/A2 point estimates without calling the analysts' functions.
Splits the reported variance into the Aronow-Samii main term and the Young
bound. Compares the reported SE^2 with the design variance of the A1
estimate when the noise path is fixed and only the assignment is redrawn.

Run from the repo root:
  env -u PYTHONPATH .venv/bin/python reviews/probes/V3/probe_a2.py
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.stats import beta, norm

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from poc_abm import config  # noqa: E402
from poc_abm.estimand import (  # noqa: E402
    _exposure_mc_cached,
    _exposure_probs_cached,
    exposure_probs,
    exposure_share,
    hajek_contrasts,
    hajek_linear_contrast,
    ht_cov,
    stratum_labels,
)
from poc_abm.kernel import World, assign, logistic, n_treated, simulate_panel, stream_seed  # noqa: E402
import interference_tradeoff as tradeoff  # noqa: E402


def panel_with_assign_rng(world, c, rule, noise_offset, assign_rng):
    """Same dynamics as kernel.simulate_panel, but the assignment RNG is separate.

    The state stream stays stream_seed('state', noise_offset). Passing the
    paired assignment stream recovers simulate_panel exactly.
    """
    rng_state = np.random.default_rng(stream_seed("state", noise_offset))
    n = world.n
    Y = rng_state.random(n)
    Xw = world.X @ np.asarray(config.ETA_FIXED)
    D = assign(world, rule, assign_rng)
    sigma = c["sigma_eps"]
    inv_deg = 1.0 / world.degrees
    for t in range(config.HORIZON):
        peer = c["gamma"] * (world.adjacency @ Y) * inv_deg
        treat = c["kappa"] * D * (t >= config.INTERVENTION_TIME)
        eps = sigma * rng_state.standard_normal(n)
        Y = logistic(c["alpha"] + c["beta"] * Y + peer + Xw + treat + eps)
    return Y.copy(), D.copy()


def my_hajek(y, mask, p):
    mask = np.asarray(mask, dtype=bool)
    p = np.asarray(p, dtype=float)
    if not np.any(mask):
        return float("nan")
    if np.any(p[mask] <= 0):
        raise RuntimeError("observed unit has nonpositive exposure probability")
    w = np.zeros(y.shape[0], dtype=float)
    w[mask] = 1.0 / p[mask]
    return float(np.dot(w, y) / np.sum(w))


def merge_labels(labels, min_n):
    counts = {name: int(np.sum(labels == name)) for name in ("S1", "S0a", "S0b", "S0c")}
    merged = any(counts[name] < min_n for name in counts)
    if merged:
        labels = labels.copy()
        labels[labels == "S0b"] = "S0c"
    return labels, merged, counts


def policy_weights(world, merged, cut):
    rng = np.random.default_rng(0)  # degree arm ignores this
    d2 = assign(world, "degree", rng)
    labels = stratum_labels(d2, exposure_share(world, d2), cut)
    if merged:
        labels = labels.copy()
        labels[labels == "S0b"] = "S0c"
    high = d2 > 0.5
    weights = {name: float(np.mean(labels == name)) for name in ("S1", "S0a", "S0b", "S0c")}
    low = ~high
    low_weights = {
        name: float(np.sum((labels == name) & low) / world.n)
        for name in ("S1", "S0a", "S0b", "S0c")
    }
    return d2, high, weights, low_weights


def my_transport(y, labels, p, weights):
    """sum_{s != S0a} w_s (mu_s - mu_S0a), own Hajek means."""
    mu = {}
    for name, w in weights.items():
        if w > 0 or name == "S0a":
            mu[name] = my_hajek(y, labels == name, p[name])
    estimate = 0.0
    for name, w in weights.items():
        if name == "S0a" or w == 0:
            continue
        estimate += w * (mu[name] - mu["S0a"])
    return estimate, mu


def my_a1_a2(world, y, d, cut, min_n):
    labels, merged, counts = merge_labels(stratum_labels(d, exposure_share(world, d), cut), min_n)
    p = exposure_probs(world, n_treated(world.n), cut)
    if merged:
        p = dict(p)
        p["S0c"] = p["S0c"] + p["S0b"]
        p["S0b"] = np.zeros_like(p["S0b"])
    _, high, weights, low_weights = policy_weights(world, merged, cut)
    a1, mu = my_transport(y, labels, p, weights)
    # A2: within-bin transport. H contrast uses 80/N, not a re-estimated share.
    high_w = float(np.mean(high))
    mu_h = {
        "S1": my_hajek(y, (labels == "S1") & high, np.where(high, p["S1"], 0.0)),
        "S0a": my_hajek(y, (labels == "S0a") & high, np.where(high, p["S0a"], 0.0)),
    }
    a2 = high_w * (mu_h["S1"] - mu_h["S0a"])
    mu_l_base = my_hajek(y, (labels == "S0a") & ~high, np.where(~high, p["S0a"], 0.0))
    low_parts = {}
    for name in ("S1", "S0b", "S0c"):
        w = low_weights[name]
        if w == 0:
            continue
        mu_l = my_hajek(y, (labels == name) & ~high, np.where(~high, p[name], 0.0))
        low_parts[name] = mu_l
        a2 += w * (mu_l - mu_l_base)
    return {
        "merged": merged,
        "counts": counts,
        "weights": weights,
        "low_weights": low_weights,
        "high_n": int(high.sum()),
        "a1": a1,
        "a2": a2,
        "mu": mu,
        "min_observed_p": float(min(p[name][labels == name].min()
                                    for name in ("S1", "S0a", "S0c")
                                    if np.any(labels == name))),
    }


def ht_parts(a_k, a_l, p_k, p_l, pi_kl, same):
    """Split ht_cov into the pi>0 term and the signed Young term."""
    a_k = np.asarray(a_k, dtype=float)
    a_l = np.asarray(a_l, dtype=float)
    p_k = np.asarray(p_k, dtype=float)
    p_l = np.asarray(p_l, dtype=float)
    pi_kl = np.asarray(pi_kl, dtype=float)
    safe_k = np.where(p_k > 0, p_k, 1.0)
    safe_l = np.where(p_l > 0, p_l, 1.0)
    pos = pi_kl > 0
    W = np.zeros_like(pi_kl)
    W[pos] = (pi_kl[pos] - np.outer(p_k, p_l)[pos]) / pi_kl[pos]
    main = float((a_k / safe_k) @ W @ (a_l / safe_l))
    zero = ~pos
    young = 0.5 * float((a_k ** 2 / safe_k) @ zero.sum(axis=1) + (a_l ** 2 / safe_l) @ zero.sum(axis=0))
    signed = young if same else -young
    return main, signed, int(zero.sum())


def reproduced_variance(world, y, d, cells, coefficients, cut, min_n):
    """Quadratic form of ht_cov, split into main and Young, own accumulation."""
    from poc_abm.estimand import maybe_merge_s0b
    labels, merged = maybe_merge_s0b(stratum_labels(d, exposure_share(world, d), cut), min_n)
    k = n_treated(world.n)
    p_base = dict(_exposure_probs_cached(world, k, cut))
    if merged:
        p_base["S0c"] = p_base["S0c"] + p_base["S0b"]
        p_base["S0b"] = np.zeros_like(p_base["S0b"])
    pi_base = _exposure_mc_cached(world, k, cut, merged)["pi"]
    prepared = []
    for cell in cells:
        nodes = np.asarray(cell.get("nodes", np.ones(world.n, dtype=bool)))
        ind = (labels == cell["stratum"]) & nodes
        p = np.where(nodes, p_base[cell["stratum"]], 0.0)
        mu = my_hajek(y, ind, p) if np.any(ind) else float("nan")
        n_hat = float((ind / np.where(p > 0, p, 1.0)).sum())
        prepared.append({"name": cell["stratum"], "nodes": nodes, "has_nodes": "nodes" in cell,
                         "a": ind * (y - mu), "p": p, "n_hat": n_hat})
    pair = {}
    var_main = 0.0
    var_young = 0.0
    for i, ci in enumerate(coefficients):
        for j, cj in enumerate(coefficients):
            if j < i:
                continue
            left, right = prepared[i], prepared[j]
            joint = pi_base[(left["name"], right["name"])] * np.outer(left["nodes"], right["nodes"])
            if left["name"] == right["name"]:
                joint = joint.copy()
                np.fill_diagonal(joint, p_base[left["name"]] * left["nodes"] * right["nodes"])
            rows = left["nodes"] if left["has_nodes"] else np.ones(world.n, dtype=bool)
            cols = right["nodes"] if right["has_nodes"] else np.ones(world.n, dtype=bool)
            main, signed, n_zero = ht_parts(
                left["a"][rows], right["a"][cols], left["p"][rows], right["p"][cols],
                joint[np.ix_(rows, cols)], same=(i == j),
            )
            scale = ci * cj / (left["n_hat"] * right["n_hat"])
            mult = 1.0 if i == j else 2.0
            var_main += mult * scale * main
            var_young += mult * scale * signed
            pair[(i, j)] = {"main": main, "young": signed, "n_zero": n_zero,
                            "contrib": mult * scale * (main + signed),
                            "scaled_young": mult * scale * signed,
                            "scaled_main": mult * scale * main}
    full = var_main + var_young
    # shipped function, for the match check only
    shipped = hajek_linear_contrast(world, y, d, cells, coefficients, cut=cut, min_n=min_n)
    return {"var_main": var_main, "var_young": var_young, "var": full,
            "se_repro": float(np.sqrt(max(full, 0.0))),
            "se_main": float(np.sqrt(max(var_main, 0.0))),
            "shipped_se": shipped["se"], "shipped_est": shipped["estimate"],
            "pairs": pair}


def design_redraw(world, c, noise_offset, reps, cut, min_n):
    """Fix the shock path. Redraw only the random assignment. R is capped by the caller."""
    estimates = np.empty(reps)
    their_est = np.empty(reps)
    their_se = np.empty(reps)
    main_se = np.empty(reps)
    t0 = time.perf_counter()
    for r in range(reps):
        y, d = panel_with_assign_rng(
            world, c, "random", noise_offset, np.random.default_rng(20_261_101 + r)
        )
        own = my_a1_a2(world, y, d, cut, min_n)
        estimates[r] = own["a1"]
        got = tradeoff.analyst_a1(world, y, d, cut=cut, min_n=min_n)
        their_est[r] = got["estimate"]
        their_se[r] = got["se"]
        # main-only SE on this draw, using the cells the shipped analyst built
        cells, coefs = [], []
        # recover cells from weights so the split uses the same contrast
        merged = own["merged"]
        _, _, weights, _ = policy_weights(world, merged, cut)
        for name in ("S1", "S0b", "S0c"):
            if weights[name] > 0:
                cells.append({"stratum": name})
                coefs.append(weights[name])
        cells.append({"stratum": "S0a"})
        coefs.append(-sum(coefs))
        parts = reproduced_variance(world, y, d, cells, coefs, cut, min_n)
        main_se[r] = parts["se_main"]
        if r == 0:
            dt = time.perf_counter() - t0
            print(f"design first draw {dt:.2f}s", flush=True)
        elif (r + 1) % 50 == 0:
            print(f"design draws {r + 1}/{reps} elapsed {time.perf_counter() - t0:.1f}s", flush=True)
    sd = float(np.std(estimates, ddof=1))
    return {
        "reps": reps,
        "noise_offset": noise_offset,
        "own_sd": sd,
        "own_mean": float(np.mean(estimates)),
        "max_abs_own_vs_shipped": float(np.max(np.abs(estimates - their_est))),
        "mean_se": float(np.mean(their_se)),
        "mean_se2": float(np.mean(their_se ** 2)),
        "mean_main_se2": float(np.mean(main_se ** 2)),
        "se_over_design_sd": float(np.mean(their_se) / sd),
        "se2_over_design_var": float(np.mean(their_se ** 2) / sd ** 2),
        "main_se2_over_design_var": float(np.mean(main_se ** 2) / sd ** 2),
        "elapsed_s": time.perf_counter() - t0,
    }


def check_expectations(payload):
    nominal = 0.95
    rows = []
    for point, block in payload["points"].items():
        rep = block["repeated"]
        abs_bias = {a: abs(rep[a]["bias"]) for a in ("A0", "A1", "A2")}
        a = abs_bias["A0"] > abs_bias["A1"] > abs_bias["A2"]
        b_sd = rep["A0"]["sd"] < rep["A1"]["sd"] < rep["A2"]["sd"]
        b_w = rep["A0"]["mean_width"] < rep["A1"]["mean_width"] < rep["A2"]["mean_width"]
        dist = {name: abs(rep[name]["coverage"] - nominal) for name in ("A0", "A1", "A2")}
        closest = min(dist.values())
        c_a0_far = rep["A0"]["coverage"] < 0.5
        c_a2_closest = dist["A2"] == closest
        c_tie = dist["A1"] == dist["A2"]
        d = rep["A1"]["bias"] < 0 and rep["A2"]["bias"] < 0
        e = all(rep[name]["width_over_theta_hm"] < 1 for name in ("A0", "A1", "A2"))
        # Clopper-Pearson from the reported coverage and n_defined
        for name in ("A0", "A1", "A2"):
            n = rep[name]["n_defined"]
            k = int(round(rep[name]["coverage"] * n))
            lo, hi = tradeoff.clopper_pearson(k, n)
            got = rep[name]["coverage_clopper_pearson_95"]
            cp_ok = abs(lo - got[0]) < 1e-12 and abs(hi - got[1]) < 1e-12
            rows.append(f"cp {point} {name} k={k} n={n} match={cp_ok} "
                        f"lo_diff={lo - got[0]:.3e} hi_diff={hi - got[1]:.3e}")
        rows.append(
            f"expect {point} a={a} b_sd={b_sd} b_width={b_w} "
            f"c_a0_far={c_a0_far} c_a2_closest={c_a2_closest} c_tie_a1={c_tie} d={d} e={e} "
            f"dist={dist} se_over_sd="
            + str({name: rep[name]["se_over_sd"] for name in ("A0", "A1", "A2")})
        )
    return rows


def main():
    cut = config.EXPOSURE_SHARE_CUT
    min_n = config.STRATUM_MIN_N
    payload = json.loads((ROOT / "results" / "interference" / "tradeoff.json").read_text())
    main_results = json.loads((ROOT / "results" / "planted" / "poc_results.json").read_text())
    print("config", {
        "N": config.N_AGENTS, "k": n_treated(), "cut": cut, "min_n": min_n,
        "R": config.INTERFERENCE_REPETITIONS, "offset_base": config.INTERFERENCE_OFFSET_BASE,
        "foil_offset": config.FOIL_PANEL_OFFSET, "confidence": config.HM_CONFIDENCE,
        "mc_draws": config.EXPOSURE_MC_DRAWS,
    })
    print("json_R", payload["repetitions"], "json_base", payload["offset_base"],
          "json_foil", payload["foil_panel_offset"])
    for line in check_expectations(payload):
        print(line)

    world = World()
    c = main_results["findings"]["c_star"]["c"]
    truth = float(main_results["findings"]["c_star"]["theta2_true"])
    planted = float(main_results["theta_star"]["theta2"])
    print("truth_fields_equal_at_cstar", truth == planted, "theta2", truth)
    # one paired rep of the truth functional, own code, not a replacement for the locked MC truth
    y0, _ = panel_with_assign_rng(world, c, "control", 0, np.random.default_rng(1))
    y2, d2 = panel_with_assign_rng(world, c, "degree", 0, np.random.default_rng(1))
    y0b, d0 = simulate_panel(world, c, "control", 0)
    y2b, d2b = simulate_panel(world, c, "degree", 0)
    print("dynamics_copy_matches_simulate_panel",
          bool(np.array_equal(y0, y0b) and np.array_equal(y2, y2b) and np.array_equal(d2, d2b)))
    print("one_rep_theta2_sign", float(y2.mean() - y0.mean()), "degree_seeded", int((d2 > 0.5).sum()))

    y_d, d_d = simulate_panel(world, c, "degree", config.FOIL_PANEL_OFFSET)
    y_r, d_r = simulate_panel(world, c, "random", config.FOIL_PANEL_OFFSET)
    # paired-stream recovery
    y_r2, d_r2 = panel_with_assign_rng(
        world, c, "random", config.FOIL_PANEL_OFFSET,
        np.random.default_rng(stream_seed("assign:random", config.FOIL_PANEL_OFFSET)),
    )
    print("random_panel_copy_matches", bool(np.array_equal(y_r, y_r2) and np.array_equal(d_r, d_r2)))

    own = my_a1_a2(world, y_r, d_r, cut, min_n)
    json_one = payload["points"]["c_star"]["one_panel"]
    print("own_weights", own["weights"])
    print("own_low_weights", own["low_weights"])
    print("own_high_n", own["high_n"], "merged", own["merged"], "counts", own["counts"])
    print("min_observed_p", own["min_observed_p"])
    print("A1_absdiff", abs(own["a1"] - json_one["A1"]["estimate"]))
    print("A2_absdiff", abs(own["a2"] - json_one["A2"]["estimate"]))
    print("A1_equal", own["a1"] == json_one["A1"]["estimate"])
    print("A2_equal", own["a2"] == json_one["A2"]["estimate"])

    # A0, own OLS-HC1 share, point only
    n = len(y_d)
    Z = np.column_stack([np.ones(n), d_d, world.X])
    beta_hat = np.linalg.lstsq(Z, y_d, rcond=None)[0][1]
    a0 = float(d_d.sum() / n * beta_hat)
    print("A0_absdiff", abs(a0 - json_one["A0"]["estimate"]), "A0_equal", a0 == json_one["A0"]["estimate"])

    shipped_a1 = tradeoff.analyst_a1(world, y_r, d_r)
    shipped_a2 = tradeoff.analyst_a2(world, y_r, d_r)
    print("shipped_A1_matches_own", shipped_a1["estimate"] == own["a1"])
    print("shipped_A2_matches_own", shipped_a2["estimate"] == own["a2"])
    z = float(norm.ppf(0.5 + 0.5 * config.HM_CONFIDENCE))
    for name, got in (("A1", shipped_a1), ("A2", shipped_a2)):
        lo, hi = got["interval"]
        width_from_se = 2 * z * got["se"]
        print(name, "interval_halfwidth_minus_zse", (hi - lo) / 2 - z * got["se"],
              "json_se_absdiff", abs(got["se"] - json_one[name]["se"]))

    # identity: general contrast vs existing spill contrast, and a dropped-cross mutation
    old = hajek_contrasts(world, y_r, d_r)
    ident = hajek_linear_contrast(
        world, y_r, d_r, [{"stratum": "S0c"}, {"stratum": "S0a"}], [1.0, -1.0]
    )
    print("identity_estimate", ident["estimate"] == old["delta_spill"],
          "identity_se", ident["se"] == old["se_spill"])
    parts_id = reproduced_variance(
        world, y_r, d_r, [{"stratum": "S0c"}, {"stratum": "S0a"}], [1.0, -1.0], cut, min_n
    )
    print("identity_repro_se_absdiff", abs(parts_id["se_repro"] - old["se_spill"]))
    print("identity_young_share", parts_id["var_young"] / parts_id["var"] if parts_id["var"] else None)
    # mutation: drop the cross term. The identity test's SE assertion must move.
    var_no_cross = parts_id["pairs"][(0, 0)]["contrib"] + parts_id["pairs"][(1, 1)]["contrib"]
    print("identity_se_if_cross_dropped", float(np.sqrt(max(var_no_cross, 0.0))),
          "shipped_se", old["se_spill"],
          "cross_changes_se", abs(np.sqrt(max(var_no_cross, 0.0)) - old["se_spill"]) > 1e-12)

    # scaling pin: w*(mu_S1 - mu_S0a) must have SE = w * se_dir
    w = 0.1
    scaled = hajek_linear_contrast(
        world, y_r, d_r, [{"stratum": "S1"}, {"stratum": "S0a"}], [w, -w]
    )
    print("scale_se_absdiff", abs(scaled["se"] - w * old["se_dir"]),
          "scale_est_absdiff", abs(scaled["estimate"] - w * old["delta_dir"]))

    # A1 variance split on the committed one panel
    cells, coefs = [], []
    for name in ("S1", "S0b", "S0c"):
        if own["weights"][name] > 0:
            cells.append({"stratum": name})
            coefs.append(own["weights"][name])
    cells.append({"stratum": "S0a"})
    coefs.append(-sum(coefs))
    parts = reproduced_variance(world, y_r, d_r, cells, coefs, cut, min_n)
    print("A1_repro_se_absdiff", abs(parts["se_repro"] - shipped_a1["se"]))
    print("A1_var_main", parts["var_main"], "A1_var_young", parts["var_young"],
          "A1_young_share", parts["var_young"] / parts["var"] if parts["var"] else None)
    print("A1_se", shipped_a1["se"], "A1_se_main_only", parts["se_main"])
    for key, item in parts["pairs"].items():
        print(f"A1_pair {key} contrib={item['contrib']:.6e} young={item['young']:.6e} n_zero={item['n_zero']}")

    # direct quadratic form vs contrast-of-contrasts expansion
    # Var(sum w_s (mu_s - mu_0)) from the mu covariances already in `parts`
    print("A1_diagonal_only_se", float(np.sqrt(sum(
        parts["pairs"][(i, i)]["contrib"] for i in range(len(coefs))
    ))))

    reps = 400
    print(f"starting design redraw R={reps}", flush=True)
    design = design_redraw(world, c, config.FOIL_PANEL_OFFSET, reps, cut, min_n)
    print("DESIGN", json.dumps(design, sort_keys=True))
    # second noise path, smaller, only if the first finished quickly
    if design["elapsed_s"] < 70:
        design2 = design_redraw(world, c, config.INTERFERENCE_OFFSET_BASE, 200, cut, min_n)
        print("DESIGN2", json.dumps(design2, sort_keys=True))
    else:
        print("DESIGN2 skipped, first redraw used the time budget")


if __name__ == "__main__":
    main()

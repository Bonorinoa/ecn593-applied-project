"""One-panel variance split for A1 and A2. Does not redraw assignments.

Run:
  env -u PYTHONPATH .venv/bin/python reviews/probes/V3/probe_a2_split.py
"""
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from poc_abm import config  # noqa: E402
from poc_abm.kernel import World, simulate_panel  # noqa: E402
import interference_tradeoff as tradeoff  # noqa: E402
from probe_a2 import my_a1_a2, reproduced_variance  # noqa: E402


def cells_from_result(result):
    """Rebuild the cell list the analyst passed, from the returned weights and means order.

    analyst_a1 stores positive-stratum weights only. analyst_a2 stores bin labels.
    We instead call the analyst functions' cell construction by replaying the
    public weights: A1 keys are stratum names; A2 keys are 'S,bin'.
    """
    return result


def a1_cells(weights):
    cells, coefs, names = [], [], []
    for name in ("S1", "S0b", "S0c"):
        if weights[name] > 0:
            cells.append({"stratum": name})
            coefs.append(weights[name])
            names.append(name)
    cells.append({"stratum": "S0a"})
    coefs.append(-sum(coefs))
    names.append("S0a")
    return cells, coefs, names


def a2_cells(world, y, d, cut, min_n):
    # Replay analyst_a2's cell list without trusting its variance.
    merged = tradeoff._panel_merge(world, d, cut, min_n)
    d2, labels = tradeoff._degree_labels(world, cut, merged)
    high = d2 > 0.5
    low = ~high
    cells = [{"stratum": "S1", "nodes": high}, {"stratum": "S0a", "nodes": high}]
    coefs = [float(high.mean()), -float(high.mean())]
    names = ["S1,H", "S0a,H"]
    low_total = 0.0
    for name in ("S1", "S0b", "S0c"):
        weight = float(np.sum((labels == name) & low) / world.n)
        if weight > 0:
            cells.append({"stratum": name, "nodes": low})
            coefs.append(weight)
            names.append(f"{name},L")
            low_total += weight
    if low_total > 0:
        cells.append({"stratum": "S0a", "nodes": low})
        coefs.append(-low_total)
        names.append("S0a,L")
    return cells, coefs, names


def report(tag, parts, names):
    var = parts["var"]
    print(f"{tag} se_repro_absdiff {abs(parts['se_repro'] - parts['shipped_se'])}")
    print(f"{tag} shipped_se {parts['shipped_se']}")
    print(f"{tag} se_main {parts['se_main']}")
    print(f"{tag} young_share {parts['var_young'] / var if var else None}")
    print(f"{tag} var_main {parts['var_main']} var_young {parts['var_young']}")
    for (i, j), item in parts["pairs"].items():
        scale_note = item["contrib"]
        young_share_pair = None
        print(f"{tag} pair {names[i]}:{names[j]} contrib={scale_note:.6e} "
              f"scaled_young={item['scaled_young']:.6e} scaled_main={item['scaled_main']:.6e} "
              f"n_zero={item['n_zero']}")


def main():
    cut = config.EXPOSURE_SHARE_CUT
    min_n = config.STRATUM_MIN_N
    payload = json.loads((ROOT / "results" / "interference" / "tradeoff.json").read_text())
    main_results = json.loads((ROOT / "results" / "planted" / "poc_results.json").read_text())
    world = World()
    # containment flags vs the saved truth, all three points, one panel
    for point in ("min_I", "median_I", "c_star"):
        truth = float(main_results["findings"][point]["theta2_true"])
        planted = float(main_results["theta_star"]["theta2"])
        block = payload["points"][point]
        assert block["theta2_true"] == truth
        for name in ("A0", "A1", "A2"):
            lo, hi = block["one_panel"][name]["interval"]
            contains = lo <= truth <= hi
            contains_p = lo <= planted <= hi
            ok = contains == block["one_panel"][name]["covers_truth"]
            ok_p = contains_p == block["one_panel"][name]["covers_planted_truth"]
            print(f"flag {point} {name} contains={contains} json={block['one_panel'][name]['covers_truth']} "
                  f"match={ok} planted_match={ok_p} vs={block['one_panel'][name]['vs_Theta_hm']}")

    c = main_results["findings"]["c_star"]["c"]
    y, d = simulate_panel(world, c, "random", config.FOIL_PANEL_OFFSET)
    own = my_a1_a2(world, y, d, cut, min_n)
    cells, coefs, names = a1_cells(own["weights"])
    parts = reproduced_variance(world, y, d, cells, coefs, cut, min_n)
    report("A1", parts, names)

    cells2, coefs2, names2 = a2_cells(world, y, d, cut, min_n)
    parts2 = reproduced_variance(world, y, d, cells2, coefs2, cut, min_n)
    report("A2", parts2, names2)
    shipped = tradeoff.analyst_a2(world, y, d)
    json_est = payload["points"]["c_star"]["one_panel"]["A2"]["estimate"]
    print("A2_shipped_equals_json", shipped["estimate"] == json_est)
    print("A2_shipped_minus_json", shipped["estimate"] - json_est)
    print("A2_own_minus_shipped", own["a2"] - shipped["estimate"])

    # two calls, same offset: determinism of the one panel
    a = tradeoff.panel_analysts(world, c, config.FOIL_PANEL_OFFSET)
    b = tradeoff.panel_analysts(world, c, config.FOIL_PANEL_OFFSET)
    print("one_panel_repeat_identical",
          all(a[name]["estimate"] == b[name]["estimate"] and a[name]["se"] == b[name]["se"]
              for name in ("A0", "A1", "A2")))


if __name__ == "__main__":
    main()

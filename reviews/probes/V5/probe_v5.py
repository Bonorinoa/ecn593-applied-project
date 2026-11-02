"""V5 independent probe. Does not call the A2.1 split or the variance-parts helper.

Run from the repo root:
  env -u PYTHONPATH .venv/bin/python -u reviews/probes/V5/probe_v5.py
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from poc_abm import config  # noqa: E402
from poc_abm.estimand import exposure_mc, exposure_probs, exposure_share  # noqa: E402
from poc_abm.kernel import World, assign, n_treated, simulate_panel  # noqa: E402


def fail(msg):
    print("FAIL", msg)
    raise SystemExit(1)


def own_fmt(x, dp, keep=None):
    """Same rounding rule as scripts/write_numbers.py:fmt, written out here."""
    s = f"{float(x):.{dp}f}"
    keep = dp if keep is None else keep
    if "." in s:
        whole, frac = s.split(".")
        while len(frac) > keep and frac.endswith("0"):
            frac = frac[:-1]
        s = whole + ("." + frac if frac else "")
    return s


def own_ht_parts(a_k, a_l, p_k, p_l, pi, same):
    """Aronow-Samii main term and signed Young term, from the formula, not ht_cov.

    Positive joint probability:
        sum_ij (pi_ij - p_i p_j) / pi_ij * (a_i / p_i) * (a_j / p_j)
    Zero joint probability, same cell:
        + sum_{pi_ij=0} [a_i^2 / (2 p_i) + a_j^2 / (2 p_j)]
    Zero joint probability, different cells: the same sum with a minus sign.
    """
    a_k = np.asarray(a_k, dtype=float)
    a_l = np.asarray(a_l, dtype=float)
    p_k = np.asarray(p_k, dtype=float)
    p_l = np.asarray(p_l, dtype=float)
    pi = np.asarray(pi, dtype=float)
    safe_k = np.where(p_k > 0, p_k, 1.0)
    safe_l = np.where(p_l > 0, p_l, 1.0)
    pos = pi > 0
    outer = np.outer(p_k, p_l)
    weight = np.zeros_like(pi)
    weight[pos] = (pi[pos] - outer[pos]) / pi[pos]
    main = float((a_k / safe_k) @ weight @ (a_l / safe_l))
    zero = ~pos
    young = 0.5 * float(
        (a_k ** 2 / safe_k) @ zero.sum(axis=1) + (a_l ** 2 / safe_l) @ zero.sum(axis=0)
    )
    signed = young if same else -young
    return main, signed


def hand_example():
    """Two nodes. Only the diagonal has positive joint probability."""
    a = np.array([1.0, 0.0])
    p = np.array([0.5, 0.5])
    pi = np.array([[0.5, 0.0], [0.0, 0.5]])
    main, young = own_ht_parts(a, a, p, p, pi, same=True)
    # (a/p)=[2,0]; W_00=(0.5-0.25)/0.5=0.5; main = 2*0.5*2 = 2.
    # Off-diagonal zeros: 0.5 * (2 + 2) = 2.
    print(f"HAND main={main} young={young}")
    if main != 2.0 or young != 2.0:
        fail(f"hand example moved: main={main} young={young}")


def own_hajek(y, mask, p):
    mask = np.asarray(mask, dtype=bool)
    p = np.asarray(p, dtype=float)
    if not np.any(mask):
        return float("nan")
    clipped = np.clip(p, 1e-12, None)
    w = np.zeros(y.shape[0], dtype=float)
    w[mask] = 1.0 / clipped[mask]
    return float(np.dot(w, y) / np.sum(w))


def own_labels(d, share, cut):
    d = np.asarray(d)
    share = np.asarray(share)
    labels = np.empty(d.shape[0], dtype=object)
    treated = d > 0.5
    labels[treated] = "S1"
    labels[~treated & (share == 0.0)] = "S0a"
    labels[~treated & (share > 0.0) & (share < cut)] = "S0b"
    labels[~treated & (share >= cut)] = "S0c"
    return labels


def panel_merged(labels, min_n):
    thin = any(int(np.sum(labels == name)) < min_n for name in ("S1", "S0a", "S0b", "S0c"))
    if thin:
        labels = labels.copy()
        labels[labels == "S0b"] = "S0c"
    return labels, thin


def a1_young_share(world, c):
    """A1 at the declared one-panel draw. Own weights, own means, own quadratic form."""
    cut = config.EXPOSURE_SHARE_CUT
    min_n = config.STRATUM_MIN_N
    y, d = simulate_panel(world, c, "random", config.FOIL_PANEL_OFFSET)
    labels = own_labels(d, exposure_share(world, d), cut)
    labels, merged = panel_merged(labels, min_n)
    d2 = np.zeros(world.n)
    order = np.lexsort((np.arange(world.n), -world.degrees))
    d2[order[: n_treated(world.n)]] = 1.0
    policy = own_labels(d2, exposure_share(world, d2), cut)
    if merged:
        policy = policy.copy()
        policy[policy == "S0b"] = "S0c"
    cells = []
    coefs = []
    for name in ("S1", "S0b", "S0c"):
        weight = float(np.mean(policy == name))
        if weight > 0:
            cells.append(name)
            coefs.append(weight)
    cells.append("S0a")
    coefs.append(-sum(coefs))

    k = n_treated(world.n)
    p_base = exposure_probs(world, k, cut)
    if merged:
        p_base = dict(p_base)
        p_base["S0c"] = p_base["S0c"] + p_base["S0b"]
        p_base["S0b"] = np.zeros_like(p_base["S0b"])
    pi_base = exposure_mc(world, k, cut, merged)["pi"]

    prepared = []
    for name in cells:
        indicator = labels == name
        probability = p_base[name]
        mean = own_hajek(y, indicator, probability)
        n_hat = float((indicator / np.where(probability > 0, probability, 1.0)).sum())
        prepared.append({
            "name": name,
            "indicator": indicator,
            "p": probability,
            "mean": mean,
            "n_hat": n_hat,
            "a": indicator * (y - mean),
        })

    def cov_parts(i, j):
        left, right = prepared[i], prepared[j]
        joint = pi_base[(left["name"], right["name"])].copy()
        if left["name"] == right["name"]:
            np.fill_diagonal(joint, p_base[left["name"]])
        main, young = own_ht_parts(
            left["a"], right["a"], left["p"], right["p"], joint, same=(i == j)
        )
        denom = left["n_hat"] * right["n_hat"]
        return main / denom, young / denom

    main_total = 0.0
    young_total = 0.0
    for i, coef in enumerate(coefs):
        main, young = cov_parts(i, i)
        scale = float(coef) ** 2
        main_total += scale * main
        young_total += scale * young
    for i in range(len(prepared)):
        for j in range(i + 1, len(prepared)):
            main, young = cov_parts(i, j)
            scale = 2.0 * float(coefs[i]) * float(coefs[j])
            main_total += scale * main
            young_total += scale * young
    reported = main_total + young_total
    share = young_total / reported
    return {
        "merged": merged,
        "cells": cells,
        "coefs": coefs,
        "main": main_total,
        "young": young_total,
        "reported": reported,
        "share": share,
        "degree_assignment_matches_assign": bool(np.array_equal(
            d2, assign(world, "degree", np.random.default_rng(0))
        )),
    }


def check_json_identity(split):
    bad = 0
    for point, analysts in split["points"].items():
        for name, cell in analysts.items():
            one = cell["one_panel"]
            summed = one["positive_joint_probability_term"] + one["young_bound_term"]
            gap = abs(summed - one["reported_variance"])
            share = one["young_bound_term"] / one["reported_variance"]
            share_gap = abs(share - one["young_share"])
            design = cell["design"]
            print(
                f"SPLIT {point} {name} sum_gap={gap:.3e} share_gap={share_gap:.3e} "
                f"redraws={design['redraws']} n_defined={design['n_defined']}"
            )
            if gap > 1e-18 or share_gap > 1e-15:
                bad += 1
            if design["redraws"] != 400 or design["n_defined"] != 400:
                bad += 1
    if split["R_design"] != 400 or split["offset_base"] != 3_000_000 or split["foil_panel_offset"] != 0:
        bad += 1
        print("FAIL design block", split["R_design"], split["offset_base"], split["foil_panel_offset"])
    if bad:
        fail(f"{bad} split-identity rows")
    print("SPLIT_IDENTITY ok")


def check_ranges(split):
    young, main, full = [], [], []
    for point in ("min_I", "median_I", "c_star"):
        for name in ("A1", "A2"):
            cell = split["points"][point][name]
            young.append((cell["one_panel"]["young_share"], name, point))
            main.append((cell["design"]["mean_main_term_se2_over_design_variance"], name, point))
            full.append((cell["design"]["mean_full_se2_over_design_variance"], name, point))
    print("RANGE young", min(young), max(young))
    print("RANGE main", min(main), max(main))
    print("RANGE full", min(full), max(full))
    if min(young)[1:] != ("A2", "min_I") or max(young)[1:] != ("A1", "median_I"):
        fail("young-share endpoints are not A2 min_I and A1 median_I")
    if min(main)[1:] != ("A2", "min_I") or max(main)[1:] != ("A1", "min_I"):
        fail("main-term endpoints moved")
    if min(full)[1:] != ("A2", "min_I") or max(full)[1:] != ("A1", "median_I"):
        fail("full-ratio endpoints moved")
    if any(value >= 1 for value, _, _ in main) or any(value <= 1 for value, _, _ in full):
        fail("A1/A2 pattern is not main<1<full")
    print("RANGES ok")


def check_macros(split):
    point_tags = {"min_I": "MinI", "median_I": "MedI", "c_star": "Star"}
    analyst_tags = {"A1": "AOne", "A2": "ATwo", "Spill": "Spill"}
    expected = {}
    for point, point_tag in point_tags.items():
        for analyst, analyst_tag in analyst_tags.items():
            suffix = f"{analyst_tag}{point_tag}"
            one = split["points"][point][analyst]["one_panel"]
            design = split["points"][point][analyst]["design"]
            expected[f"YoungShare{suffix}"] = own_fmt(one["young_share"], 3)
            expected[f"DesignRedraws{suffix}"] = str(design["redraws"])
            expected[f"DesignMainTermRatio{suffix}"] = own_fmt(
                design["mean_main_term_se2_over_design_variance"], 3
            )
            expected[f"DesignFullRatio{suffix}"] = own_fmt(
                design["mean_full_se2_over_design_variance"], 3
            )
            expected[f"VarianceReported{suffix}"] = own_fmt(one["reported_variance"], 8)
            expected[f"VarianceYoungTerm{suffix}"] = own_fmt(one["young_bound_term"], 8)
    text = (ROOT / "thesis" / "numbers.tex").read_text()
    writeup = (ROOT / "writeup" / "numbers.tex").read_text()
    print("NUMBERS_BYTE_IDENTICAL", text == writeup)
    if text != writeup:
        fail("thesis/numbers.tex differs from writeup/numbers.tex")
    found = dict(re.findall(r"\\newcommand\{\\(\w+)\}\{([^}]*)\}", text))
    mismatches = []
    for name, value in expected.items():
        if found.get(name) != value:
            mismatches.append((name, value, found.get(name)))
    print(f"MACRO_CHECKED {len(expected)} mismatches {len(mismatches)}")
    for row in mismatches:
        print("MACRO_MISMATCH", row)
    if mismatches:
        fail("macros do not match the JSON under the published rounding")
    cited = [
        "YoungShareAOneStar", "YoungShareATwoStar", "YoungShareSpillStar",
        "DesignRedrawsAOneStar", "DesignMainTermRatioAOneStar", "DesignFullRatioAOneStar",
        "YoungShareATwoMinI", "YoungShareAOneMedI",
        "DesignMainTermRatioATwoMinI", "DesignMainTermRatioAOneMinI",
        "DesignFullRatioATwoMinI", "DesignFullRatioAOneMedI",
        "DesignFullRatioSpillStar",
    ]
    for name in cited:
        print(f"CITED {name} {found[name]}")


def check_reported_variance(split, tradeoff):
    """The split's reported variance is the already-committed one-panel SE^2."""
    for point in ("min_I", "median_I", "c_star"):
        for name in ("A1", "A2"):
            se = tradeoff["points"][point]["one_panel"][name]["se"]
            reported = split["points"][point][name]["one_panel"]["reported_variance"]
            gap = abs(se ** 2 - reported)
            print(f"REPORTED {point} {name} se2_gap={gap:.3e}")
            if gap > 1e-18:
                fail(f"reported variance is not the committed SE^2 at {point} {name}")
    print("REPORTED_IS_COMMITTED_SE2 ok")


def check_paper():
    thesis = ROOT / "thesis"
    uses = []
    for path in thesis.rglob("*.tex"):
        for i, line in enumerate(path.read_text().splitlines(), 1):
            if "\\MISSING{" in line or "\\MISSING " in line:
                uses.append(f"{path.relative_to(ROOT)}:{i}")
    print("MISSING_CALLS", uses or "none")
    if uses:
        fail("a \\\\MISSING call remains")
    replacements = {
        "thesis/sections/07-results.tex": [
            "YoungShareAOneStar", "YoungShareATwoStar", "DesignRedrawsAOneStar",
            "DesignMainTermRatioAOneStar", "DesignFullRatioAOneStar",
        ],
        "thesis/sections/C-foil2-check.tex": ["YoungShareSpillStar"],
    }
    for rel, names in replacements.items():
        text = (ROOT / rel).read_text()
        for name in names:
            if f"\\{name}" not in text:
                fail(f"{rel} missing \\{name}")
            if f"\\MISSING{{{name}}}" in text:
                fail(f"{rel} still has the placeholder for {name}")
    print("V4_REPLACEMENTS applied")
    labels = {
        "thesis/sections/07-results.tex": [
            "descriptive and is not a pre-registered result",
            "designed after the A2 results",
            "A post hoc reading of the trade-off",
            "depends on the exposure map",
            "They are not calibrated",
            "shrinks the bias but does not remove it",
        ],
        "thesis/sections/C-foil2-check.tex": [
            "descriptive variance split of addendum A2.1, designed after the A2 results",
        ],
        "thesis/sections/06-evaluation.tex": [
            "Addendum A2.1, written after these results were seen",
            "it is descriptive",
        ],
        "thesis/sections/F-replication.tex": [
            "descriptive",
            "addendum A2.1",
            "skips the Foil~2",
            "both amendments and the addendum",
        ],
        "thesis/sections/G-disclosures.tex": [
            "Two amendments and one addendum",
            "Addendum A2.1 was written after the A2",
            "descriptive",
            "states no expectation",
        ],
    }
    for rel, phrases in labels.items():
        text = (ROOT / rel).read_text()
        for phrase in phrases:
            if phrase not in text:
                fail(f"{rel} missing phrase: {phrase}")
    print("LABELS ok")
    diff = subprocess.check_output(
        ["git", "diff", "-U0", "8831e5d", "4ffb45b", "--", "thesis/sections"],
        cwd=ROOT, text=True,
    )
    digit_lines = []
    for line in diff.splitlines():
        if not line.startswith("+") or line.startswith("+++"):
            continue
        if re.search(r"\d", line) and "\\" not in line.split("%")[0]:
            digit_lines.append(line)
        elif re.search(r"(?<!\\)\b\d+\.\d+\b", line):
            digit_lines.append(line)
    print("ADDED_DIGIT_LINES_WITHOUT_MACRO", len(digit_lines))
    for line in digit_lines:
        print("DIGIT", line)
    calibrated = []
    for rel in (
        "thesis/sections/07-results.tex",
        "thesis/sections/C-foil2-check.tex",
        "thesis/sections/06-evaluation.tex",
        "thesis/sections/G-disclosures.tex",
    ):
        for i, line in enumerate((ROOT / rel).read_text().splitlines(), 1):
            if "calibrat" in line.lower():
                calibrated.append(f"{rel}:{i}: {line.strip()}")
    print("CALIBRATED_HITS", len(calibrated))
    for row in calibrated:
        print("CAL", row)


def main():
    hand_example()
    split = json.loads((ROOT / "results/interference/variance_split.json").read_text())
    tradeoff = json.loads((ROOT / "results/interference/tradeoff.json").read_text())
    check_json_identity(split)
    check_ranges(split)
    check_macros(split)
    check_reported_variance(split, tradeoff)
    check_paper()
    planted = json.loads((ROOT / "results/planted/poc_results.json").read_text())
    c = planted["findings"]["c_star"]["c"]
    own = a1_young_share(World(), c)
    committed = split["points"]["c_star"]["A1"]["one_panel"]
    print(
        "OWN_A1_CSTAR",
        {k: own[k] for k in ("merged", "cells", "coefs", "share", "reported", "young", "main")},
    )
    print("JSON_A1_CSTAR", committed)
    print("degree_assignment_matches_assign", own["degree_assignment_matches_assign"])
    share_gap = abs(own["share"] - committed["young_share"])
    reported_gap = abs(own["reported"] - committed["reported_variance"])
    young_gap = abs(own["young"] - committed["young_bound_term"])
    print(f"OWN_GAPS share={share_gap:.3e} reported={reported_gap:.3e} young={young_gap:.3e}")
    if share_gap > 1e-12 or reported_gap > 1e-12 or young_gap > 1e-12:
        fail("independent A1 c_star Young share does not match the committed split")
    if own["merged"]:
        fail("c_star panel merged; the A1 cell list would not be the unmerged one")
    print("OWN_YOUNG_SHARE ok")
    print("PROBE_OK")


if __name__ == "__main__":
    main()

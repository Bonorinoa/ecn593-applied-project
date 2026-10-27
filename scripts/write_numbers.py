"""Write writeup/numbers.tex: every number in the paper, read from the code's outputs.

The paper never types a result. main.tex and cover.tex use the macros defined
here, so a rerun followed by this script (and a LaTeX build) updates the PDF.
Sources, in order of the table below:
  C  = config/world.toml and config/design.toml (exogenous, via poc_abm.config)
  G  = the drawn graph (endogenous, recomputed from the code in a few ms)
  P  = results/planted/poc_results.json
  F  = results/checks/foil2_coverage.json

Format rule, one for every number: round to `dp` decimals, then drop trailing
zeros, but keep at least `keep` decimals. Example: fmt(0.9300, 4, 3) = 0.930.

Usage: python scripts/write_numbers.py
"""
import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from poc_abm import config as C  # noqa: E402
from poc_abm.kernel import World, assign, n_treated  # noqa: E402

OUT = ROOT / "writeup" / "numbers.tex"


def fmt(x, dp, keep=None, sign=False, pct=False):
    """Round x to dp decimals; trim trailing zeros down to `keep` decimals."""
    x = 100 * x if pct else x
    s = f"{x:+.{dp}f}" if sign else f"{x:.{dp}f}"
    keep = dp if keep is None else keep
    if "." in s:
        whole, frac = s.split(".")
        while len(frac) > keep and frac.endswith("0"):
            frac = frac[:-1]
        s = whole + ("." + frac if frac else "")
    return s


def count(n):
    """An integer with a thousands comma: 10000 -> 10,000."""
    return f"{int(n):,}"


def load(path):
    return json.loads((ROOT / path).read_text())


def graph_facts():
    world = World()
    d = assign(world, "degree", np.random.default_rng(0))   # the degree arm is deterministic
    deg = world.degrees.astype(int)
    cut = int(deg[d == 1].min())                             # lowest degree that gets seeded
    n, p = C.N_AGENTS, C.EDGE_P
    a = (world.adjacency > 0).astype(np.int64)               # binary, symmetric, no self-loops
    k = a.sum(axis=1)                                         # true degrees (isolated people have 0)
    closed = int(np.trace(a @ a @ a))                         # = 6 x triangles (each one counted 6 times)
    triples = int((k * (k - 1)).sum()) // 2                   # connected triples: sum_i C(k_i, 2)
    return {
        "mean": float(world.degrees.mean()),
        "theory": (n - 1) * (1 - (1 - p) ** 2),
        "cut": cut,
        "at_cut": int((deg == cut).sum()),
        "seeded_at_cut": int(((deg == cut) & (d == 1)).sum()),
        "mean_degree_true": float(k.mean()),
        "triangles": closed // 6,
        "triples": triples,
        "clustering": (closed // 2) / triples,                # 3 x triangles / connected triples
        "clustering_theory": 1 - (1 - p) ** 2,                # edge probability, the ER expectation
    }


def yn(flag):
    return "yes" if flag else "no"


def verdict(label):
    return label if label else "no verdict"


TEXT_VALUES = {"yes", "no", "no verdict", "F-OVERCONF", "F-HONEST"}   # the only non-numeric macros
PARAM_TAG = {"alpha": "Alpha", "beta": "Beta", "gamma": "Gamma", "kappa": "Kappa", "sigma_eps": "Sigma"}


def table():
    P = load("results/planted/poc_results.json")
    F = load("results/checks/foil2_coverage.json")
    G = graph_facts()
    k = n_treated()
    lo, mi, cs = P["findings"]["min_I"], P["findings"]["median_I"], P["findings"]["c_star"]
    dlo, dmi, dcs = (f["foil1_gap_decomposition"] for f in (lo, mi, cs))
    spread = P["nroy_param_spread"]
    rc = P["endpoint_recheck"]["candidates"]   # 0, 1: Theta_hm lower, upper; 2, 3: Theta_exp lower, upper
    kp = F["kernel"]["points"]
    gate = F["gate"]
    box = C.PARAM_BOX

    rows = [
        # ---- C: the world and the design (exogenous) ----
        ("NAgents", count(C.N_AGENTS)),
        ("KSeeded", str(k)),
        ("SeedShare", fmt(k / C.N_AGENTS, 2, 1)),
        ("SeedSharePct", fmt(k / C.N_AGENTS, 0, pct=True)),
        ("Horizon", str(C.HORIZON)),
        ("EdgeRate", fmt(C.WORLD["population"]["edge_rate"], 0)),
        ("BoxAlphaLo", fmt(box["alpha"][0], 1)), ("BoxAlphaHi", fmt(box["alpha"][1], 1)),
        ("BoxBetaLo", fmt(box["beta"][0], 2)), ("BoxBetaHi", fmt(box["beta"][1], 2)),
        ("BoxGammaLo", fmt(box["gamma"][0], 2)), ("BoxGammaHi", fmt(box["gamma"][1], 2)),
        ("BoxKappaLo", fmt(box["kappa"][0], 2)), ("BoxKappaHi", fmt(box["kappa"][1], 2)),
        ("BoxSigmaLo", fmt(box["sigma_eps"][0], 2)), ("BoxSigmaHi", fmt(box["sigma_eps"][1], 2)),
        ("EtaOne", fmt(C.ETA_FIXED[0], 2)), ("EtaTwo", fmt(C.ETA_FIXED[1], 2)), ("EtaThree", fmt(C.ETA_FIXED[2], 2)),
        ("CStarAlpha", fmt(P["c_star"]["alpha"], 3, 1)), ("CStarBeta", fmt(P["c_star"]["beta"], 3)),
        ("CStarGamma", fmt(P["c_star"]["gamma"], 3)), ("CStarKappa", fmt(P["c_star"]["kappa"], 3)),
        ("CStarSigma", fmt(P["c_star"]["sigma_eps"], 3)),
        ("RepsEstimand", str(C.REPS_ESTIMAND)),
        ("RepsMoment", str(C.REPS_MOMENT)),
        ("RepsZ", str(C.REPS_Z)),
        ("ThetaSample", str(C.THETA_SAMPLE)),
        ("WavePoints", str(C.WAVE_POINTS)),
        ("WavePointsComma", count(C.WAVE_POINTS)),
        ("PointsEvaluated", count(C.WAVES * C.WAVE_POINTS)),
        ("BoxInflationPct", fmt(C.BOX_INFLATION, 0, pct=True)),
        ("Confidence", fmt(C.HM_CONFIDENCE, 2)),
        ("ConfidencePct", fmt(C.HM_CONFIDENCE, 0, pct=True)),
        ("NMoments", str(C.N_MOMENTS)),
        ("DeltaOne", fmt(C.DELTA["sq_level"], 2)), ("DeltaTwo", fmt(C.DELTA["sq_corr_x1"], 2)),
        ("DeltaThree", fmt(C.DELTA["sq_peer_corr"], 2)), ("DeltaFour", fmt(C.DELTA["pilot_level"], 2)),
        ("ShareCut", fmt(C.EXPOSURE_SHARE_CUT, 2)),
        ("StratumMinN", str(C.STRATUM_MIN_N)),
        ("ExposureDraws", count(C.EXPOSURE_MC_DRAWS)),
        ("CheckPanels", str(C.FOIL2_CHECK["kernel_panels"])),
        ("GateTruth", fmt(C.FOIL2_CHECK["gate_effect_s0c"], 2)),
        # ---- G: the drawn graph ----
        ("MeanDegree", fmt(G["mean"], 3)),
        ("MeanDegreeTheory", fmt(G["theory"], 2)),
        ("DegreeCut", str(G["cut"])),
        ("DegreeCutTotal", str(G["at_cut"])),
        ("DegreeCutSeeded", str(G["seeded_at_cut"])),
        ("MeanDegreeTrue", fmt(G["mean_degree_true"], 3)),
        ("Triangles", count(G["triangles"])),
        ("ConnectedTriples", count(G["triples"])),
        ("GlobalClustering", fmt(G["clustering"], 4)),
        ("GlobalClusteringTheory", fmt(G["clustering_theory"], 4)),
        # ---- P: planted run, history matching ----
        ("Tau", fmt(P["tau"], 4)),
        ("ZOne", fmt(P["z"][0], 4)), ("ZTwo", fmt(P["z"][1], 4, 2)), ("ZThree", fmt(P["z"][2], 4)),
        ("ZFour", fmt(P["z"][3], 4)), ("PilotMinusSq", fmt(P["z"][3] - P["z"][0], 5)),
        ("WaveKeptOne", str(P["wave_kept"][0])), ("WaveKeptTwo", str(P["wave_kept"][1])),
        ("WaveKeptThree", str(P["wave_kept"][2])),
        ("NNroy", str(P["n_nroy"])),
        ("WaveMinIOne", fmt(P["wave_I_stats"][0]["min"], 4)), ("WaveMinITwo", fmt(P["wave_I_stats"][1]["min"], 4)),
        ("WaveMinIThree", fmt(P["wave_I_stats"][2]["min"], 4)),
        ("WaveMedIOne", fmt(P["wave_I_stats"][0]["median"], 2)), ("WaveMedITwo", fmt(P["wave_I_stats"][1]["median"], 2)),
        ("WaveMedIThree", fmt(P["wave_I_stats"][2]["median"], 2)),
        ("MinI", fmt(lo["I"], 4)), ("MedI", fmt(mi["I"], 4)),
        ("MinIAlpha", fmt(lo["c"]["alpha"], 4)), ("MinIBeta", fmt(lo["c"]["beta"], 4, 3)),
        ("MinIGamma", fmt(lo["c"]["gamma"], 4)), ("MinIKappa", fmt(lo["c"]["kappa"], 4)),
        ("MinISigma", fmt(lo["c"]["sigma_eps"], 4)), ("MedIKappa", fmt(mi["c"]["kappa"], 4)),
        # ---- P: effects at c*, images, endpoint recheck ----
        ("ThetaOneStar", fmt(P["theta_star"]["theta1"], 5)), ("ThetaTwoStar", fmt(P["theta_star"]["theta2"], 5)),
        ("ThetaTwoStarShort", fmt(P["theta_star"]["theta2"], 4)),
        ("PremiumStar", fmt(P["theta_star"]["premium"], 5)), ("SpillStar", fmt(P["spill_star"]["delta_spill"], 5)),
        ("ThetaHmLo", fmt(P["Theta_hm"][0], 5)), ("ThetaHmHi", fmt(P["Theta_hm"][1], 5)),
        ("ThetaHmLoShort", fmt(P["Theta_hm"][0], 4)), ("ThetaHmHiShort", fmt(P["Theta_hm"][1], 4)),
        ("ThetaExpLo", fmt(P["Theta_exp"][0], 6)), ("ThetaExpHi", fmt(P["Theta_exp"][1], 6)),
    ]
    for tag, c in zip(("HmLo", "HmHi", "ExpLo", "ExpHi"), rc):
        rows += [
            (f"Recheck{tag}Index", str(c["nroy_index"])),
            (f"Recheck{tag}Pilot", fmt(c["pilot_value"], 6, sign=True)),
            (f"Recheck{tag}PilotSE", fmt(c["pilot_pointwise_se"], 6)),
            (f"Recheck{tag}Fresh", fmt(c["fresh_value"], 6, sign=True)),
            (f"Recheck{tag}FreshSE", fmt(c["fresh_pointwise_se"], 6)),
        ]
    rows += [
        ("RecheckExpLoFreshAbs", fmt(rc[2]["fresh_value"], 6)),
    ]
    # ---- P: nroy_param_spread (sd over the sampled NROY points / sd of a uniform draw over C) ----
    for name, tag in PARAM_TAG.items():
        rows.append((f"SpreadRatio{tag}", fmt(spread["sd_ratio"][name], 3)))
    names = spread["param_names"]
    for i, a in enumerate(names):
        for j in range(i + 1, len(names)):
            rows.append((f"SpreadCorr{PARAM_TAG[a]}{PARAM_TAG[names[j]]}",
                         fmt(spread["correlation_matrix"][i][j], 3, sign=True)))
    rows += [
        # ---- P: the two diagnostic points (min-I, median-I) ----
        ("MinIThetaTwo", fmt(lo["theta2_true"], 5)), ("MedIThetaTwo", fmt(mi["theta2_true"], 5)),
        ("MinIThetaTwoShort", fmt(lo["theta2_true"], 4)),
        ("MinIFoilOneLo", fmt(lo["foil1_ci"][0], 5)), ("MinIFoilOneHi", fmt(lo["foil1_ci"][1], 5)),
        ("MedIFoilOneLo", fmt(mi["foil1_ci"][0], 5)), ("MedIFoilOneHi", fmt(mi["foil1_ci"][1], 5)),
        ("MinIBetaHat", fmt(lo["foil1_beta"], 4)), ("MedIBetaHat", fmt(mi["foil1_beta"], 4)),
        ("MinIBetaLo", fmt(lo["foil1_ci_beta"][0], 4)), ("MinIBetaHi", fmt(lo["foil1_ci_beta"][1], 4)),
        ("MedIBetaLo", fmt(mi["foil1_ci_beta"][0], 4)), ("MedIBetaHi", fmt(mi["foil1_ci_beta"][1], 4)),
        ("MinIFoilOneBelowPct", fmt(1 - lo["foil1_share"] * lo["foil1_beta"] / lo["theta2_true"], 1, pct=True)),
        ("MedIFoilOneBelowPct", fmt(1 - mi["foil1_share"] * mi["foil1_beta"] / mi["theta2_true"], 1, pct=True)),
        ("MinISpill", fmt(lo["spill_true"], 5)), ("MedISpill", fmt(mi["spill_true"], 5)),
        ("MinISpillShort", fmt(lo["spill_true"], 4)),
        ("MinIFoilTwoEst", fmt(lo["foil2_estimate"], 5)), ("MinIFoilTwoSE", fmt(lo["foil2_se"], 5)),
        ("MedIFoilTwoEst", fmt(mi["foil2_estimate"], 5)), ("MedIFoilTwoSE", fmt(mi["foil2_se"], 5)),
        ("MinIFoilTwoLo", fmt(lo["foil2_ci"][0], 6)), ("MinIFoilTwoHi", fmt(lo["foil2_ci"][1], 6)),
        ("MedIFoilTwoLo", fmt(mi["foil2_ci"][0], 6)), ("MedIFoilTwoHi", fmt(mi["foil2_ci"][1], 6)),
    ]
    # ---- P: the c_star point (the field experimenter): the same quantities ----
    rows += [
        ("StarPtFoilOneLo", fmt(cs["foil1_ci"][0], 5)), ("StarPtFoilOneHi", fmt(cs["foil1_ci"][1], 5)),
        ("StarPtBetaHat", fmt(cs["foil1_beta"], 4)),
        ("StarPtBetaLo", fmt(cs["foil1_ci_beta"][0], 4)), ("StarPtBetaHi", fmt(cs["foil1_ci_beta"][1], 4)),
        ("StarPtFoilOneBelowPct", fmt(1 - cs["foil1_share"] * cs["foil1_beta"] / cs["theta2_true"], 1, pct=True)),
        ("StarPtFoilTwoEst", fmt(cs["foil2_estimate"], 5)), ("StarPtFoilTwoSE", fmt(cs["foil2_se"], 5)),
        ("StarPtFoilTwoLo", fmt(cs["foil2_ci"][0], 6)), ("StarPtFoilTwoHi", fmt(cs["foil2_ci"][1], 6)),
    ]
    # ---- P: verdicts and containment flags at all three points ----
    for tag, f in (("MinI", lo), ("MedI", mi), ("StarPt", cs)):
        rows += [
            (f"{tag}FoilOneVerdict", verdict(f["foil1_vs_Theta_hm"])),
            (f"{tag}FoilTwoVerdict", verdict(f["foil2_vs_Theta_exp"])),
            (f"{tag}FoilOneCoversTruth", yn(f["foil1_covers_truth"])),
            (f"{tag}FoilOneCoversPlanted", yn(f["foil1_covers_planted_truth"])),
            (f"{tag}FoilTwoCoversTruth", yn(f["foil2_covers_truth"])),
            (f"{tag}FoilTwoCoversPlanted", yn(f["foil2_covers_planted_truth"])),
        ]
    # ---- P: Foil 1 gap decomposition (min-I, median-I) ----
    for tag, d in (("MinI", dlo), ("MedI", dmi), ("StarPt", dcs)):
        rows += [
            (f"{tag}SeededPart", fmt(d["seeded_part"], 5)),
            (f"{tag}UnseededPart", fmt(d["unseeded_part"], 5)),
            (f"{tag}SeededContrast", fmt(d["selected_policy_contrast"], 4)),
            (f"{tag}MeanBeta", fmt(d["mean_beta"], 4)),
            (f"{tag}GapMeanBeta", fmt(d["gap_mean_beta"], 5)),
            (f"{tag}UnseededShareMeanBeta", fmt(d["unseeded_share_of_gap_mean_beta"], 4)),
            (f"{tag}OlsErrorPart", fmt(d["ols_error_part_mean_beta"], 5)),
            (f"{tag}GapDisplayed", fmt(d["gap_displayed"], 5)),
            (f"{tag}UnseededShareDisplayed", fmt(d["unseeded_share_of_gap_displayed"], 4)),
            (f"{tag}BaselineGap", fmt(d["baseline_gap_seeded_minus_unseeded"], 4)),
            (f"{tag}UnseededShareDisplayedPct", fmt(d["unseeded_share_of_gap_displayed"], 0, pct=True)),
        ]
    rows += [
        ("UnseededShareMeanBetaPct", fmt(dlo["unseeded_share_of_gap_mean_beta"], 0, pct=True)),
        # ---- F: the Foil 2 calibration check ----
        ("GateAssignments", count(gate["R"])),
        ("GateMeanEstimate", fmt(gate["mean_estimate"], 5)),
        ("GateRatio", fmt(gate["variance_ratio"], 3)),
        ("GateRatioBootSE", fmt(gate["variance_ratio_boot_se"], 4)),
        ("GateCoveragePct", fmt(gate["coverage"], 1, pct=True)),
        ("GateCoverageLoPct", fmt(gate["coverage_clopper_pearson_95"][0], 1, pct=True)),
        ("GateCoverageHiPct", fmt(gate["coverage_clopper_pearson_95"][1], 1, pct=True)),
        ("KernelCovStar", fmt(kp["c_star"]["coverage"], 4, 3)),
        ("KernelCovMinI", fmt(kp["min_I"]["coverage"], 4, 3)),
        ("KernelCovMedI", fmt(kp["median_I"]["coverage"], 4, 3)),
        ("DesignCovStar", fmt(kp["c_star"]["design_coverage"], 4, 3)),
        ("DesignCovMinI", fmt(kp["min_I"]["design_coverage"], 4, 3)),
        ("DesignCovMedI", fmt(kp["median_I"]["design_coverage"], 4, 3)),
    ]
    assert all(v in TEXT_VALUES or math.isfinite(float(v.replace(",", ""))) for _, v in rows)
    names = [n for n, _ in rows]
    assert len(names) == len(set(names)), "duplicate macro name"
    return rows


def main():
    rows = table()
    lines = ["% numbers.tex: GENERATED by scripts/write_numbers.py from config/ and results/.",
             "% Do not edit by hand. Rerun the script after any run.", ""]
    lines += [f"\\newcommand{{\\{name}}}{{{value}}}" for name, value in rows]
    OUT.write_text("\n".join(lines) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}: {len(rows)} numbers")


if __name__ == "__main__":
    main()

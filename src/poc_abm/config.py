"""Constants of the run. Every number the code uses is defined here.

The code is law: the docs describe this file, not the other way round.
A rerun with the same code and environment reproduces every number exactly
(all random streams are seeded below or by crc32 keys in kernel.stream_seed).
"""
from pathlib import Path

# ---- reproducibility -------------------------------------------------------
SEED_GRAPH = 20260812          # graph draw
SEED_X = 20260813              # covariates
SEED_HM = 20260814             # history-matching designs (one Generator for all waves)
SEED_THETA_SAMPLE = SEED_HM + 1  # = 20260815: the 400 NROY points mapped to the images
SEED_FOIL2_MC = 20260817       # Foil 2: simulated assignments for joint exposure probabilities
# Simulation noise and assignment streams are not seeded here: they use
# kernel.stream_seed(label, rep) = crc32 of a length-prefixed key.

# ---- population ------------------------------------------------------------
N_AGENTS = 800
# Edge rule (kernel.World): draw A_ij ~ Bernoulli(EDGE_P) for every ordered pair,
# then symmetrize A | A.T. So P(i~j) = 1 - (1 - EDGE_P)^2 ≈ 2·EDGE_P and the
# expected degree is (N-1)(1 - (1 - EDGE_P)^2) ≈ 7.97 (measured: 8.085).
EDGE_P = 4.0 / N_AGENTS
N_COVARIATES = 3

# ---- dynamics ---------------------------------------------------------------
HORIZON = 20                   # T
INTERVENTION_TIME = 0          # t*

# parameter box C (alpha, beta, gamma, kappa, sigma_eps); eta fixed
PARAM_BOX = {
    "alpha": (-2.5, -0.5),
    "beta": (0.05, 0.60),
    "gamma": (0.05, 0.80),
    "kappa": (0.25, 2.50),
    "sigma_eps": (0.01, 0.40),
}
ETA_FIXED = (0.05, 0.10, 0.02)  # literacy, resources, baseline-propensity weights

# planted point c* = center of C. Midpoint of each interval.
C_STAR = {name: 0.5 * (lo + hi) for name, (lo, hi) in PARAM_BOX.items()}

# ---- assignment rules -------------------------------------------------------
SEED_FRACTION = 0.10           # k = ceil(0.10 · N) people seeded in the random and degree arms

# ---- Monte Carlo ------------------------------------------------------------
REPS_ESTIMAND = 200            # reps per arm when evaluating theta(c), delta_spill(c)
REPS_MOMENT = 30               # reps per arm when evaluating M(c)
REPS_Z = REPS_ESTIMAND         # z := M̂(c*) at estimand precision (scripts/plant_z.py)

# ---- World Bank anchors (scripts/fetch_anchors.py; the archived F-EMPTY run) --
WB_BASE = "https://api.worldbank.org/v2"
WB_INDICATORS = {
    "immunization": "SH.IMM.IDPT",       # z1: preventive behavior level
    "sec_completion": "SE.SEC.CMPT.LO.ZS",  # z2: gradient source
    "internet": "IT.NET.USER.ZS",        # z3: adoption/diffusion level
}
AGGREGATE_NAMES_EXCLUDED = {"World", "Euro area", "European Union",
                            "OECD members", "High income", "Low income",
                            "Upper middle income", "Lower middle income",
                            "Least developed countries: UN classification"}
ANCHOR_LEVEL_SCALE = 0.01      # the API gives levels in percent; z is on [0, 1]

# discrepancy delta, same units as z: levels in [0,1], corr unitless
DELTA = {"level_imm": 0.02, "gradient_edu": 0.05, "level_internet": 0.02}
N_MOMENTS = 3
HM_CONFIDENCE = 0.95           # tau = chi2 quantile (df = N_MOMENTS); also the CI level of both foils

# ---- history matching ---------------------------------------------------------
WAVE_POINTS = 1000             # LHS points per wave
WAVES = 3
BOX_INFLATION = 0.20           # next-wave box = NROY bounding box, span widened by 20% (10% per side)
SINGLETON_SPAN_FRACTION = 0.05 # F-SINGLETON flag: every NROY axis span < 5% of the box span
THETA_SAMPLE = 400             # NROY points sampled for the images
# Independent recheck of the points that set each image endpoint (verifier t_1f00fc3b
# item 5): fresh REPS_ESTIMAND reps on stream offsets RECHECK_OFFSET, RECHECK_OFFSET+1, ...
# Disjoint from the image reps (0..199), the foil panel (0) and the Foil 2 gate (1,000,000+).
RECHECK_OFFSET = 100_000

# ---- measurement layer: parked 2026-10-20 (PLAN item 13; restore from ebed7ce) --

# ---- foils ---------------------------------------------------------------------
FOIL_PANEL_OFFSET = 0          # the one panel each foil sees (rep offset for stream_seed)
EXPOSURE_SHARE_CUT = 0.25      # Foil 2 strata: S0b vs S0c
STRATUM_MIN_N = 20             # merge S0b into S0c if any cell thinner (decided per panel)
EXPOSURE_MC_DRAWS = 10_000     # Foil 2 variance: simulated random-arm assignments

# ---- paths -------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[2]   # repo root (src/poc_abm/config.py)
DATA_DIR = ROOT / "data"
RESULTS_DIR = ROOT / "results"
FIGURES_DIR = ROOT / "figures"

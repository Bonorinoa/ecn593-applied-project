"""Frozen constants. Every number here is stated in SPECIFICATION.md
and reported in writeup/main.tex.

Nothing in this packet may hardcode a constant that is not defined here.
If this file and the write-up disagree, the JSON in results/ is what ran.
Freeze date: 2026-08-26, amended 2026-08-27 (AMENDMENT-02).
"""
from pathlib import Path

# ---- reproducibility -------------------------------------------------------
SEED_GRAPH = 20260812          # graph draw
SEED_X = 20260813              # covariates
SEED_HM = 20260814             # history-matching designs
SEED_RUN_BASE = 20260815       # simulation noise streams (offset per rep)
SEED_CF = 20260816             # causal forest (Foil 1)
SEED_E2 = 20260817             # exposure-mapped estimator (Foil 2)

# ---- population ------------------------------------------------------------
N_AGENTS = 800
EDGE_P = 4.0 / N_AGENTS        # ER graph, mean degree ≈ 4
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

# planted world = center of C (AMENDMENT-02). Midpoint of each frozen interval.
C_STAR = {name: 0.5 * (lo + hi) for name, (lo, hi) in PARAM_BOX.items()}

# ---- assignment rules -------------------------------------------------------
SEED_FRACTION = 0.10           # 10% of N

# ---- Monte Carlo ------------------------------------------------------------
REPS_ESTIMAND = 200            # reps per arm when evaluating theta(c)
REPS_MOMENT = 30               # reps per arm when evaluating M(c)
REPS_Z = REPS_ESTIMAND          # z := M̂(c*) at estimand precision (AMENDMENT-02)

# ---- World Bank anchors -----------------------------------------------------
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
# API returns percentage points for levels; match in [0,1] (METHODOLOGY §5).
ANCHOR_LEVEL_SCALE = 0.01

# discrepancy budget, same units as z: levels in [0,1], corr unitless
DELTA = {"level_imm": 0.02, "gradient_edu": 0.05, "level_internet": 0.02}
N_MOMENTS = 3
HM_CONFIDENCE = 0.95           # tau quantile of chi2 with df = N_MOMENTS

# ---- history matching ---------------------------------------------------------
WAVE_POINTS = 1000             # LHS points per wave
WAVES = 3
BOX_INFLATION = 0.20           # next-wave box = survivor bbox inflated 20%
THETA_SAMPLE = 400             # survivors sampled for Theta mapping

# ---- diagnostic worlds (functions of I only) --------------------------------
C0_RULES = ("min_I", "median_I")

# ---- measurement layer --------------------------------------------------------
SURVEY_NOISE_SD = 0.15         # m2
BAD_ITEM_X_LOAD = 0.5          # m3 loading on x3 (treatment channel)
BAD_ITEM_NOISE_SD = 0.10
ADMISSION_CORR_THRESHOLD = 0.5 # restriction: |corr(s3, x3)| must be BELOW this

# ---- Foil 1 forest hyperparameters (implementation freeze, before waves) ------
CF_N_ESTIMATORS = 100          # honest forest; N=800 panel
CF_MIN_SAMPLES_LEAF = 5

# ---- Foil 2 exposure map (AMENDMENT-01) --------------------------------------
EXPOSURE_SHARE_CUT = 0.25      # S0b vs S0c
EXPOSURE_SHARE_CUT_APPENDIX = 0.50
STRATUM_MIN_N = 20             # merge S0b into S0c if any cell thinner

# ---- paths -------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[2]   # repo root (src/poc_abm/config.py)
DATA_DIR = ROOT / "data"
RESULTS_DIR = ROOT / "results"
FIGURES_DIR = ROOT / "figures"

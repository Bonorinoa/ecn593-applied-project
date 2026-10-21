"""Load the exogenous parameters from config/world.toml and config/design.toml.

Two kinds of quantity appear in this project:
- EXOGENOUS: chosen by us before any run. They are all in the two TOML files.
  config/world.toml is the simulated village and the policy question.
  config/design.toml is the analyst's choices.
- ENDOGENOUS: computed by the model (z, NROY, the images, the foil intervals,
  the verdicts). They are never in config. They live in data/planted.json
  and results/.

This module only reads the files and names the values. It adds two derived
rules, written here so that they are visible: EDGE_P = edge_rate / N, and the
planted point c* = the center of the box C.
A rerun with the same code, config and environment reproduces every number.
"""
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]   # repo root (src/poc_abm/config.py)
DATA_DIR = ROOT / "data"
RESULTS_DIR = ROOT / "results"
FIGURES_DIR = ROOT / "figures"

with open(ROOT / "config" / "world.toml", "rb") as f:
    WORLD = tomllib.load(f)
with open(ROOT / "config" / "design.toml", "rb") as f:
    DESIGN = tomllib.load(f)

# ---- the world (config/world.toml) -----------------------------------------
N_AGENTS = WORLD["population"]["n_agents"]
EDGE_P = WORLD["population"]["edge_rate"] / N_AGENTS        # derived rule
N_COVARIATES = WORLD["population"]["n_covariates"]
HORIZON = WORLD["dynamics"]["horizon"]
INTERVENTION_TIME = WORLD["dynamics"]["intervention_time"]
ETA_FIXED = tuple(WORLD["dynamics"]["eta_fixed"])
PARAM_BOX = {name: tuple(bounds) for name, bounds in WORLD["param_box"].items()}
C_STAR = {name: 0.5 * (lo + hi) for name, (lo, hi) in PARAM_BOX.items()}   # derived rule
SEED_FRACTION = WORLD["policy"]["seed_fraction"]
SEED_GRAPH = WORLD["seeds"]["graph"]
SEED_X = WORLD["seeds"]["covariates"]

# ---- the design (config/design.toml) ---------------------------------------
REPS_ESTIMAND = DESIGN["monte_carlo"]["reps_estimand"]
REPS_MOMENT = DESIGN["monte_carlo"]["reps_moment"]
REPS_Z = DESIGN["monte_carlo"]["reps_z"]

_hm = DESIGN["history_matching"]
WAVES = _hm["waves"]
WAVE_POINTS = _hm["wave_points"]
BOX_INFLATION = _hm["box_inflation"]
SINGLETON_SPAN_FRACTION = _hm["singleton_span_fraction"]
HM_CONFIDENCE = _hm["confidence"]
SEED_HM = _hm["seed"]
DELTA = dict(_hm["delta"])
N_MOMENTS = len(DELTA)

THETA_SAMPLE = DESIGN["image"]["theta_sample"]
SEED_THETA_SAMPLE = DESIGN["image"]["seed"]
RECHECK_OFFSET = DESIGN["image"]["recheck_offset"]

_foils = DESIGN["foils"]
FOIL_PANEL_OFFSET = _foils["panel_offset"]
EXPOSURE_SHARE_CUT = _foils["exposure_share_cut"]
STRATUM_MIN_N = _foils["stratum_min_n"]
EXPOSURE_MC_DRAWS = _foils["exposure_mc_draws"]
SEED_FOIL2_MC = _foils["exposure_mc_seed"]

FOIL2_CHECK = dict(DESIGN["foil2_check"])   # read by scripts/check_foil2_coverage.py

_wb = DESIGN["worldbank"]
WB_BASE = _wb["base_url"]
ANCHOR_LEVEL_SCALE = _wb["level_scale"]
AGGREGATE_NAMES_EXCLUDED = set(_wb["aggregates_excluded"])
WB_INDICATORS = dict(_wb["indicators"])

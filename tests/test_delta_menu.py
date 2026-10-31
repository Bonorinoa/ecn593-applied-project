"""Tests for the delta argument and the delta menu (amendment A1).

1. The optional `delta` argument defaults to config.DELTA, so every existing call is unchanged.
2. The menu logic, on a tiny design (a few points, a few reps). It checks the wiring and the
   consistency check, not any number from the real run.
"""
import sys
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

from poc_abm import config  # noqa: E402
from poc_abm.history_matching import run_waves  # noqa: E402
from poc_abm.kernel import World  # noqa: E402
from poc_abm.moments import MOMENT_NAMES, discrepancy, load_z, sampling_variances, v_diag_of  # noqa: E402

import delta_menu  # noqa: E402


def _tiny(monkeypatch):
    for name, value in {"WAVE_POINTS": 30, "WAVES": 2, "THETA_SAMPLE": 4,
                        "REPS_MOMENT": 3, "REPS_ESTIMAND": 3}.items():
        monkeypatch.setattr(config, name, value)


def _inputs():
    z, audit = load_z("planted")
    return World(), z, sampling_variances(audit)


# ---- the delta argument: defaults keep the old behavior ----------------------------------

def test_discrepancy_and_v_diag_default_to_config_delta():
    explicit = dict(config.DELTA)
    assert np.array_equal(discrepancy(), discrepancy(explicit))
    sampling, mc = np.full(4, 1e-6), np.full(4, 2e-6)
    assert np.array_equal(v_diag_of(sampling, mc), v_diag_of(sampling, mc, explicit))
    assert np.array_equal(discrepancy(), np.array([config.DELTA[n] ** 2 for n in MOMENT_NAMES]))


def test_discrepancy_hand_arithmetic_for_a_passed_delta():
    """delta 0.5, 0.1, 0.2, 0.5 gives delta^2 = 0.25, 0.01, 0.04, 0.25 (and V adds the variances)."""
    delta = {"sq_level": 0.5, "sq_corr_x1": 0.1, "sq_peer_corr": 0.2, "pilot_level": 0.5}
    np.testing.assert_allclose(discrepancy(delta), [0.25, 0.01, 0.04, 0.25], rtol=0, atol=1e-15)
    np.testing.assert_allclose(v_diag_of(np.full(4, 1.0), np.full(4, 2.0), delta),
                               [3.25, 3.01, 3.04, 3.25], rtol=0, atol=1e-15)


def test_passing_delta_never_changes_config():
    before = dict(config.DELTA)
    delta_menu.delta_for(0.005)
    discrepancy(delta_menu.delta_for(0.005))
    assert config.DELTA == before


def test_run_waves_default_equals_explicit_config_delta(monkeypatch):
    _tiny(monkeypatch)
    world, z, sampling = _inputs()
    a = run_waves(world, z, sampling)
    b = run_waves(world, z, sampling, delta=dict(config.DELTA))
    assert a["wave_kept"] == b["wave_kept"] and a["finding"] == b["finding"]
    assert np.array_equal(a["nroy"], b["nroy"]) and np.array_equal(a["I"], b["I"])


def test_a_larger_delta_keeps_at_least_as_many_points(monkeypatch):
    """Same seed, same points in wave 1; a larger delta shrinks I, so wave 1 keeps a superset."""
    _tiny(monkeypatch)
    world, z, sampling = _inputs()
    tight = run_waves(world, z, sampling, n_waves=1, delta=delta_menu.delta_for(0.005))
    loose = run_waves(world, z, sampling, n_waves=1, delta=delta_menu.delta_for(0.5))
    assert loose["wave_kept"][0] >= tight["wave_kept"][0]


# ---- the menu logic on a tiny design -------------------------------------------------------

def test_delta_for_moves_only_the_two_level_moments():
    d = delta_menu.delta_for(0.01)
    assert d["sq_level"] == d["pilot_level"] == 0.01
    assert d["sq_corr_x1"] == config.DELTA["sq_corr_x1"] and d["sq_peer_corr"] == config.DELTA["sq_peer_corr"]
    assert delta_menu.delta_for(0.02) == config.DELTA
    assert [lvl for _, lvl in delta_menu.MENU] == [0.02, 0.01, 0.005]
    assert delta_menu.MENU[0][1] == config.DELTA["sq_level"]


def test_run_entry_on_a_tiny_design(monkeypatch):
    _tiny(monkeypatch)
    world, z, sampling = _inputs()
    foils = {"foil1_ci": [0.03, 0.04], "foil2_ci": [0.0, 0.001]}
    e = delta_menu.run_entry(world, z, sampling, delta_menu.delta_for(0.5), foils)
    assert e["finding_hm"] != "F-EMPTY" and e["n_nroy"] == sum(e["wave_kept"]) > 0
    assert e["delta"] == [0.5, config.DELTA["sq_corr_x1"], config.DELTA["sq_peer_corr"], 0.5]
    assert e["n_theta_sample"] == min(config.THETA_SAMPLE, e["n_nroy"])
    lo, hi = e["Theta_hm"]
    assert lo <= hi
    # the classification is the pipeline's rule, applied to this entry's images
    from poc_abm.diagnostic import classify_interval
    assert e["foil1_vs_Theta_hm"] == classify_interval(foils["foil1_ci"], e["Theta_hm"])
    assert e["foil2_vs_Theta_exp"] == classify_interval(foils["foil2_ci"], e["Theta_exp"])
    spread = e["nroy_param_spread"]
    assert set(spread["sd_ratio"]) == set(config.PARAM_BOX)
    names = spread["param_names"]
    assert e["alpha_kappa_corr"] == spread["correlation_matrix"][names.index("alpha")][names.index("kappa")]


def test_run_entry_empty_nroy_is_reported_as_found(monkeypatch):
    _tiny(monkeypatch)
    world, z, sampling = _inputs()
    e = delta_menu.run_entry(world, z, sampling, delta_menu.delta_for(1e-9),
                             {"foil1_ci": [0.03, 0.04], "foil2_ci": [0.0, 0.001]})
    assert e["finding_hm"] == "F-EMPTY" and e["n_nroy"] == 0
    assert e["Theta_hm"] is None and e["Theta_exp"] is None and e["nroy_param_spread"] is None
    assert e["foil1_vs_Theta_hm"] is None and e["foil2_vs_Theta_exp"] is None


def _main_like(entry):
    return {k: entry[k] for k in ("delta", "tau", "Theta_hm", "Theta_exp", "n_nroy", "wave_kept",
                                  "nroy_param_spread")}


def test_consistency_check_passes_on_equal_and_exits_nonzero_on_a_difference(monkeypatch):
    _tiny(monkeypatch)
    world, z, sampling = _inputs()
    e = delta_menu.run_entry(world, z, sampling, delta_menu.delta_for(0.5),
                             {"foil1_ci": [0.03, 0.04], "foil2_ci": [0.0, 0.001]})
    main = _main_like(e)
    delta_menu.check_main_entry(e, main)                       # equal: no exit
    for key, bad in (("n_nroy", e["n_nroy"] + 1), ("wave_kept", [0, 0]),
                     ("Theta_hm", [e["Theta_hm"][0], e["Theta_hm"][1] + 1e-12])):
        with pytest.raises(SystemExit) as exc:
            delta_menu.check_main_entry(e, {**main, key: bad})
        assert exc.value.code not in (0, None) and key in str(exc.value.code)


# ---- the macros (scripts/write_numbers.py) ---------------------------------------------------

def test_menu_macros_on_a_made_up_menu():
    """Names follow \\MenuDelta<Entry><Item>. An empty entry writes only Level, Finding, NNroy."""
    from write_numbers import menu_rows
    full = {"delta_level": 0.005, "finding_hm": None, "n_nroy": 7,
            "Theta_hm": [0.1, 0.25], "Theta_exp": [-0.001, 0.002],
            "nroy_param_spread": {"sd_ratio": {"alpha": 0.5, "kappa": 0.25, "gamma": 1.0}},
            "foil1_vs_Theta_hm": "F-OVERCONF", "foil2_vs_Theta_exp": None}
    empty = {"delta_level": 0.02, "finding_hm": "F-EMPTY", "n_nroy": 0, "Theta_hm": None}
    rows = dict(menu_rows({"entries": {"Quarter": full, "Main": empty}}))
    assert rows["MenuDeltaQuarterLevel"] == "0.005" and rows["MenuDeltaQuarterFinding"] == "none"
    assert rows["MenuDeltaQuarterNNroy"] == "7"
    assert (rows["MenuDeltaQuarterThetaHmLo"], rows["MenuDeltaQuarterThetaHmHi"]) == ("0.10000", "0.25000")
    assert (rows["MenuDeltaQuarterThetaExpLo"], rows["MenuDeltaQuarterThetaExpHi"]) == ("-0.001000", "0.002000")
    assert [rows[f"MenuDeltaQuarterSpreadRatio{t}"] for t in ("Alpha", "Kappa", "Gamma")] == ["0.500", "0.250", "1.000"]
    assert rows["MenuDeltaQuarterFoilOneVerdict"] == "F-OVERCONF"
    assert rows["MenuDeltaQuarterFoilTwoVerdict"] == "no verdict"
    assert {k for k in rows if k.startswith("MenuDeltaMain")} == {
        "MenuDeltaMainLevel", "MenuDeltaMainFinding", "MenuDeltaMainNNroy"}
    assert rows["MenuDeltaMainFinding"] == "F-EMPTY"

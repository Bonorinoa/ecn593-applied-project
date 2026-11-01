"""Amendment A2: the three analysts for theta2."""
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

from poc_abm import config  # noqa: E402
from poc_abm.estimand import (  # noqa: E402
    exposure_share,
    hajek_contrasts,
    hajek_linear_contrast,
    stratum_labels,
)
from poc_abm.figures import draw_tradeoff  # noqa: E402
from poc_abm.kernel import World, simulate_panel  # noqa: E402

import interference_tradeoff as tradeoff  # noqa: E402


def _path(n):
    adjacency = np.zeros((n, n))
    for i in range(n - 1):
        adjacency[i, i + 1] = adjacency[i + 1, i] = 1.0
    x = np.random.default_rng(7).random((n, 3))
    return World.from_arrays(adjacency, x)


def _path4():
    return _path(4)


def test_general_contrast_exactly_matches_existing_spill_contrast():
    world = World()
    y, d = simulate_panel(world, config.C_STAR, "random", config.FOIL_PANEL_OFFSET)
    old = hajek_contrasts(world, y, d)
    new = hajek_linear_contrast(
        world,
        y,
        d,
        cells=[{"stratum": "S0c"}, {"stratum": "S0a"}],
        coefficients=[1.0, -1.0],
    )
    assert new["estimate"] == old["delta_spill"]
    assert new["se"] == old["se_spill"]


def test_a1_equals_exact_policy_contrast_when_exposure_map_holds():
    """Path 0-1-2-3; degree seeds node 1 and this pilot seeds node 2.

    With y = b + e_s inside each exposure stratum, every Hajek mean equals
    b + e_s exactly. Under the degree policy the shares are 1/4 S1,
    1/2 S0c and 1/4 S0a, so theta2 is 1/4 e_S1 + 1/2 e_S0c.
    """
    world = _path4()
    d = np.array([0.0, 0.0, 1.0, 0.0])
    labels = stratum_labels(d, exposure_share(world, d), cut=0.25)
    effects = {"S1": 0.4, "S0a": 0.0, "S0b": 0.2, "S0c": 0.1}
    y = np.array([0.3 + effects[label] for label in labels])
    got = tradeoff.analyst_a1(world, y, d, cut=0.25, min_n=0)
    np.testing.assert_allclose(got["estimate"], 0.25 * effects["S1"] + 0.50 * effects["S0c"],
                               rtol=0, atol=1e-15)


def test_a2_is_undefined_when_a_needed_cell_is_empty():
    world = _path4()
    # The degree arm seeds node 1. This random panel seeds node 2, so S1,H is empty.
    d = np.array([0.0, 0.0, 1.0, 0.0])
    y = np.array([0.2, 0.3, 0.4, 0.5])
    got = tradeoff.analyst_a2(world, y, d, cut=0.25, min_n=0)
    assert got["undefined"] is True
    assert np.isnan(got["estimate"])
    assert all(np.isnan(x) for x in got["interval"])


def test_tradeoff_script_logic_smoke_on_tiny_design(monkeypatch):
    world = _path(8)
    monkeypatch.setattr(config, "EXPOSURE_MC_DRAWS", 40)
    main = {
        "Theta_hm": [0.0, 0.2],
        "theta_star": {"theta2": 0.1},
        "findings": {
            key: {"c": dict(config.C_STAR), "theta2_true": truth}
            for key, truth in (("min_I", 0.08), ("median_I", 0.09), ("c_star", 0.1))
        },
    }
    result = tradeoff.build_tradeoff(main, world=world, repetitions=2, offset_base=50)
    assert result["repetitions"] == 2
    assert result["offset_base"] == 50
    assert set(result["points"]) == {"min_I", "median_I", "c_star"}
    for point in result["points"].values():
        assert set(point["one_panel"]) == {"A0", "A1", "A2"}
        assert set(point["repeated"]) == {"A0", "A1", "A2"}
        assert point["repeated"]["A2"]["undefined_count"] >= 0


def test_tradeoff_figure_is_drawn_from_saved_readouts(tmp_path):
    payload = {"theta_hm_width": 0.2, "points": {}}
    for point_index, point in enumerate(("min_I", "median_I", "c_star")):
        payload["points"][point] = {"repeated": {}}
        for analyst_index, analyst in enumerate(("A0", "A1", "A2")):
            payload["points"][point]["repeated"][analyst] = {
                "bias": 0.01 * (analyst_index + 1),
                "mean_width": 0.03 * (point_index + 1),
                "coverage": 0.8 + 0.05 * analyst_index,
            }
    path = tmp_path / "tradeoff.png"
    assert draw_tradeoff(payload, path) == path
    assert path.exists() and path.stat().st_size > 0


def test_tradeoff_macro_scheme_covers_one_panel_and_repeated_cells():
    from write_numbers import tradeoff_rows

    one = {"estimate": 0.1, "se": 0.01, "interval": [0.08, 0.12],
           "covers_truth": True, "covers_planted_truth": False,
           "vs_Theta_hm": "F-OVERCONF", "undefined": False}
    repeated = {"mean": 0.1, "bias": -0.01, "sd": 0.02, "rmse": 0.03,
                "mean_se": 0.025, "se_over_sd": 1.25, "coverage": 0.9,
                "coverage_clopper_pearson_95": [0.8, 0.96], "mean_width": 0.1,
                "width_over_theta_hm": 0.5, "undefined_count": 0, "n_defined": 200}
    payload = {"repetitions": 200, "offset_base": 2_000_000, "theta_hm_width": 0.2,
               "points": {point: {"one_panel": {a: dict(one) for a in ("A0", "A1", "A2")},
                                   "repeated": {a: dict(repeated) for a in ("A0", "A1", "A2")}}
                          for point in ("min_I", "median_I", "c_star")}}
    rows = dict(tradeoff_rows(payload))
    assert rows["TradeoffR"] == "200"
    assert rows["TradeoffMinIAOneOnePanelLo"] == "0.08000"
    assert rows["TradeoffMedIATwoCoverageLo"] == "0.800"
    assert rows["TradeoffStarAZeroUndefinedCount"] == "0"


def test_thesis_figure_set_contains_writeup_figures_and_tradeoff():
    from sync_writeup_figures import THESIS_FIGURES, WRITEUP_FIGURES

    assert set(WRITEUP_FIGURES.items()) < set(THESIS_FIGURES.items())
    assert THESIS_FIGURES["tradeoff.png"] == "figures/planted/tradeoff.png"

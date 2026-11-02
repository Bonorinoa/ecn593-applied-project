"""Addendum A2.1: variance split and fixed-noise design redraw."""
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

from poc_abm import config  # noqa: E402
from poc_abm.kernel import World  # noqa: E402

import a2_variance_split as variance_split  # noqa: E402
from write_numbers import variance_split_rows  # noqa: E402
import replicate  # noqa: E402


def _path(n):
    adjacency = np.zeros((n, n))
    for i in range(n - 1):
        adjacency[i, i + 1] = adjacency[i + 1, i] = 1.0
    x = np.random.default_rng(7).random((n, 3))
    return World.from_arrays(adjacency, x)


def _main_results():
    return {
        "findings": {
            point: {"c": dict(config.C_STAR)}
            for point in ("min_I", "median_I", "c_star")
        }
    }


def test_one_panel_split_sums_exactly_to_reported_variance():
    rows = variance_split.one_panel_splits(World(), dict(config.C_STAR))

    assert set(rows) == {"A1", "A2", "Spill"}
    for row in rows.values():
        assert row["positive_joint_probability_term"] + row["young_bound_term"] == row["reported_variance"]
        assert row["young_share"] == row["young_bound_term"] / row["reported_variance"]


def test_tiny_design_smoke(monkeypatch):
    monkeypatch.setattr(config, "EXPOSURE_MC_DRAWS", 40)
    result = variance_split.build_variance_split(
        _main_results(),
        world=_path(8),
        design_redraws=2,
        offset_base=700,
        v3_probe=None,
    )

    assert result["R_design"] == 2
    assert result["offset_base"] == 700
    assert set(result["points"]) == {"min_I", "median_I", "c_star"}
    for point in result["points"].values():
        assert set(point) == {"A1", "A2", "Spill"}
        for row in point.values():
            assert row["design"]["redraws"] == 2
            assert 0 <= row["design"]["n_defined"] <= 2


def test_variance_split_macros_cover_every_cell_and_required_names():
    analyst = {
        "one_panel": {
            "reported_variance": 0.04,
            "positive_joint_probability_term": 0.01,
            "young_bound_term": 0.03,
            "young_share": 0.75,
        },
        "design": {
            "redraws": 2,
            "n_defined": 2,
            "sd": 0.1,
            "mean_main_term_se2_over_design_variance": 1.0,
            "mean_full_se2_over_design_variance": 4.0,
        },
    }
    payload = {
        "R_design": 2,
        "offset_base": 3_000_000,
        "foil_panel_offset": 0,
        "points": {
            point: {name: analyst for name in ("A1", "A2", "Spill")}
            for point in ("min_I", "median_I", "c_star")
        },
        "v3_c_star_a1_check": {
            "agrees_within_mc_noise": True,
            "ours": {"design_sd": 0.1, "main_term_ratio": 1.0, "full_ratio": 4.0},
            "v3_probe": {"design_sd": 0.11, "main_term_ratio": 0.9, "full_ratio": 4.2},
        },
    }

    rows = dict(variance_split_rows(payload))
    required = {
        "YoungShareAOneStar",
        "YoungShareATwoStar",
        "YoungShareSpillStar",
        "DesignRedrawsAOneStar",
        "DesignMainTermRatioAOneStar",
        "DesignFullRatioAOneStar",
    }
    assert required <= set(rows)
    assert rows["YoungShareAOneStar"] == "0.750"
    assert rows["DesignRedrawsSpillMedI"] == "2"
    assert rows["VarianceMainTermATwoMinI"] == "0.01000000"


def test_replicate_runs_variance_split_after_tradeoff_and_skips_it_when_quick(monkeypatch):
    calls = []
    monkeypatch.setattr(replicate, "step", lambda number, name, command, **kwargs: calls.append(name))
    monkeypatch.setattr(replicate, "report", lambda quick: None)
    monkeypatch.setattr(replicate.shutil, "which", lambda name: None)

    monkeypatch.setattr(replicate.sys, "argv", ["replicate.py"])
    replicate.main()
    assert calls.index("variance split") == calls.index("interference") + 1
    assert "results/interference/variance_split.json" in replicate.RESULT_FILES

    calls.clear()
    monkeypatch.setattr(replicate.sys, "argv", ["replicate.py", "--quick"])
    replicate.main()
    assert "interference" not in calls
    assert "variance split" not in calls

"""End-to-end smoke test: the whole pipeline on a tiny budget, writing to a temp dir.

Not a check of any number. It catches wiring errors (wrong keys, missing
imports, broken figure calls) in seconds instead of after a one-hour run.
"""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from poc_abm import config  # noqa: E402
from poc_abm import pipeline  # noqa: E402


def test_nroy_param_spread_uses_uniform_box_standard_deviation():
    """Two points: alpha -2 and -1, beta 0.1 and 0.3.

    Sample SD (ddof = 1) of alpha: mean -1.5, squares 0.25 + 0.25 = 0.5, over 1, so sqrt(0.5).
    Sample SD of beta: sqrt(2 * 0.1^2 / 1) = 0.2 / sqrt(2).
    The uniform-box SD is span / sqrt(12): spans 2.0 (alpha) and 0.55 (beta).
    The two parameters move together, so their correlation is one.
    """
    points = [{"c": {"alpha": -2.0, "beta": 0.1}},
              {"c": {"alpha": -1.0, "beta": 0.3}}]
    out = pipeline.nroy_param_spread(points, ("alpha", "beta"))
    assert abs(out["sd_ratio"]["alpha"] - np.sqrt(0.5) / (2.0 / np.sqrt(12.0))) < 1e-14
    assert abs(out["sd_ratio"]["beta"] - (0.2 / np.sqrt(2.0)) / (0.55 / np.sqrt(12.0))) < 1e-14
    np.testing.assert_allclose(out["correlation_matrix"], [[1.0, 1.0], [1.0, 1.0]])


def _tiny(monkeypatch, tmp_path):
    for name, value in {
        "WAVE_POINTS": 40, "WAVES": 2, "THETA_SAMPLE": 5, "REPS_MOMENT": 3,
        "REPS_ESTIMAND": 3, "EXPOSURE_MC_DRAWS": 200,
        "ROOT": tmp_path, "RESULTS_DIR": tmp_path / "results", "FIGURES_DIR": tmp_path / "figures",
    }.items():
        monkeypatch.setattr(config, name, value)


def test_planted_run_writes_every_output(monkeypatch, tmp_path):
    _tiny(monkeypatch, tmp_path)
    payload = pipeline.run_poc("planted")
    saved = json.loads((tmp_path / "results/planted/poc_results.json").read_text())
    assert saved["z_source"] == "planted"
    assert (tmp_path / "locks/freeze-planted.txt").exists()
    for fig in saved["figures"]:
        assert (tmp_path / fig).exists()
    if payload["finding_hm"] != "F-EMPTY":
        points = json.loads((tmp_path / "results/planted/image_points.json").read_text())
        rc = saved["endpoint_recheck"]
        assert rc["stream_offsets"][0] == config.RECHECK_OFFSET
        assert {(c["image"], c["endpoint"]) for c in rc["candidates"]} == {
            ("Theta_hm", "lower"), ("Theta_hm", "upper"), ("Theta_exp", "lower"), ("Theta_exp", "upper")}
        assert len(points) == saved["n_theta_sample"]
        assert set(saved["findings"]) == {"min_I", "median_I", "c_star"}
        assert set(saved["nroy_param_spread"]["sd_ratio"]) == set(config.PARAM_BOX)
        for key in ("min_I", "median_I", "c_star"):
            f = saved["findings"][key]
            for k in ("foil1_ci", "foil1_covers_truth", "foil1_covers_planted_truth",
                      "foil1_gap_decomposition", "foil2_ci", "foil2_estimate",
                      "foil2_covers_truth", "foil2_covers_planted_truth"):
                assert k in f
            assert abs(f["foil1_ci"][0] - f["foil1_share"] * f["foil1_ci_beta"][0]) < 1e-15
        c_star = saved["findings"]["c_star"]
        assert c_star["foil1_covers_truth"] == c_star["foil1_covers_planted_truth"]
        assert c_star["foil2_covers_truth"] == c_star["foil2_covers_planted_truth"]
        assert c_star["theta2_true"] == saved["theta_star"]["theta2"]


def test_unknown_source_is_rejected():
    import pytest

    with pytest.raises(ValueError):
        pipeline.run_poc("unknown")

"""End-to-end smoke test: the whole pipeline on a tiny budget, writing to a temp dir.

Not a check of any number. It catches wiring errors (wrong keys, missing
imports, broken figure calls) in seconds instead of after a one-hour run.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from poc_abm import config  # noqa: E402
from poc_abm import pipeline  # noqa: E402


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
        for key in ("min_I", "median_I"):
            f = saved["findings"][key]
            for k in ("foil1_ci", "foil1_covers_truth", "foil1_gap_decomposition",
                      "foil2_ci", "foil2_estimate", "foil2_covers_truth"):
                assert k in f
            assert abs(f["foil1_ci"][0] - f["foil1_share"] * f["foil1_ci_beta"][0]) < 1e-15


def test_worldbank_run_is_f_empty(monkeypatch, tmp_path):
    _tiny(monkeypatch, tmp_path)
    payload = pipeline.run_poc("worldbank")
    assert payload["finding_hm"] == "F-EMPTY"
    assert payload["variance_label"].startswith("legacy heuristic")
    assert (tmp_path / "figures/worldbank/empty.png").exists()

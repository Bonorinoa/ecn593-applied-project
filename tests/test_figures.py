"""Smoke test for the overlay figure — file is produced, nothing scientific."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from poc_abm.figures import draw_overlay  # noqa: E402


def test_overlay_writes_a_png(tmp_path):
    payload = {
        "worlds": {
            "min_I": {
                "Theta_hm": (0.0, 0.2),
                "Theta_exp": (-0.05, 0.15),
                "theta2_true": 0.08,
                "spill_true": 0.04,
                "forest_ci": (0.07, 0.09),
                "e2_ci": (0.02, 0.06),
                "Theta_cv": (0.07, 0.085),
            },
            "median_I": {
                "Theta_hm": (0.0, 0.2),
                "Theta_exp": (-0.05, 0.15),
                "theta2_true": 0.10,
                "spill_true": 0.05,
                "forest_ci": (0.09, 0.12),
                "e2_ci": (0.00, 0.08),
                "Theta_cv": (0.09, 0.11),
            },
        }
    }
    out = tmp_path / "overlay.png"
    p = draw_overlay(payload, out)
    assert p.exists()
    assert p.stat().st_size > 1000

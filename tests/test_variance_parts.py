"""Optional variance parts for the existing exposure estimators."""
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from poc_abm import config  # noqa: E402
from poc_abm.estimand import hajek_linear_contrast, ht_cov  # noqa: E402
from poc_abm.kernel import World, simulate_panel  # noqa: E402


def test_ht_cov_optional_parts_leave_default_output_identical():
    a_k = np.array([0.2, 0.0])
    a_l = np.array([0.0, -0.3])
    p_k = np.array([0.5, 0.5])
    p_l = np.array([0.5, 0.5])
    pi = np.array([[0.5, 0.0], [0.0, 0.5]])

    existing = ht_cov(a_k, a_l, p_k, p_l, pi, same=False)
    parts = ht_cov(a_k, a_l, p_k, p_l, pi, same=False, return_parts=True)

    assert existing == parts["total"]
    assert parts["positive_joint_probability"] + parts["young_bound"] == parts["total"]


def test_linear_contrast_optional_parts_leave_existing_result_identical():
    world = World()
    y, d = simulate_panel(world, config.C_STAR, "random", config.FOIL_PANEL_OFFSET)
    cells = [{"stratum": "S0c"}, {"stratum": "S0a"}]
    coefficients = [1.0, -1.0]

    existing = hajek_linear_contrast(world, y, d, cells, coefficients)
    split = hajek_linear_contrast(
        world,
        y,
        d,
        cells,
        coefficients,
        return_variance_parts=True,
    )

    without_parts = {key: value for key, value in split.items() if key != "variance_parts"}
    assert without_parts == existing
    parts = split["variance_parts"]
    assert parts["positive_joint_probability"] + parts["young_bound"] == parts["reported"]
    assert np.sqrt(parts["reported"]) == existing["se"]

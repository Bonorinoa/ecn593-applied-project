"""Hand-example tests for the moment map and implausibility — METHODOLOGY §5–§6.

Each docstring states the arithmetic. Run: pytest tests/test_moments_hand_examples.py -v
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from poc_abm import config  # noqa: E402
from poc_abm.moments import (  # noqa: E402
    MOMENT_NAMES,
    discrepancy,
    implausibility,
    load_frozen_z,
    sampling_variances,
    simulate_moments,
)


def test_moment_names_are_the_frozen_triple():
    """Order is part of the spec: (level_imm, gradient_edu, level_internet)."""
    assert MOMENT_NAMES == ("level_imm", "gradient_edu", "level_internet")


def test_c_star_is_the_center_of_the_frozen_box():
    """c* midpoints: α = (−2.5 + −0.5)/2 = −1.5; β = (0.05+0.60)/2 = 0.325;
    γ = (0.05+0.80)/2 = 0.425; κ = (0.25+2.50)/2 = 1.375;
    σε = (0.01+0.40)/2 = 0.205. Not chosen by looking at θ.
    """
    assert config.C_STAR["alpha"] == -1.5
    assert abs(config.C_STAR["beta"] - 0.325) < 1e-12
    assert abs(config.C_STAR["gamma"] - 0.425) < 1e-12
    assert abs(config.C_STAR["kappa"] - 1.375) < 1e-12
    assert abs(config.C_STAR["sigma_eps"] - 0.205) < 1e-12


def test_planted_z_is_unit_interval_and_has_sampling_variances():
    """AMENDMENT-02: z comes from data/planted.json, already in [0,1].
    Sampling variances are the stored MC variances of the R_z mean.
    """
    z, audit = load_frozen_z()
    assert z.shape == (3,)
    assert 0.0 < z[0] < 1.0
    assert 0.0 < z[2] < 1.0
    assert -1.0 <= z[1] <= 1.0
    v = sampling_variances(audit)
    assert v.shape == (3,)
    assert np.all(v > 0)
    assert audit["source"] == "planted"
    assert audit["c_star"]["alpha"] == -1.5


def test_discrepancy_budget_is_frozen_delta_squared():
    """δ = (0.02, 0.05, 0.02) in the same units as z; V gets δ² on the diagonal."""
    d2 = discrepancy()
    assert abs(d2[0] - 0.02 ** 2) < 1e-18
    assert abs(d2[1] - 0.05 ** 2) < 1e-18
    assert abs(d2[2] - 0.02 ** 2) < 1e-18


def test_implausibility_of_perfect_match_is_zero():
    """If M̂ = z, then (z−M̂) = 0 so I = 0 regardless of V."""
    z = np.array([0.5, 0.2, 0.4])
    v = np.array([0.01, 0.02, 0.03])
    assert implausibility(z, z, v) == 0.0


def test_implausibility_one_coordinate_hand_arithmetic():
    """z = (0.5, 0.2, 0.4), M̂ = (0.6, 0.2, 0.4), V = diag(0.01, 1, 1).

    diff = (−0.1, 0, 0)
    I = (−0.1)² / 0.01 = 0.01 / 0.01 = 1.
    """
    z = np.array([0.5, 0.2, 0.4])
    m = np.array([0.6, 0.2, 0.4])
    v = np.array([0.01, 1.0, 1.0])
    assert abs(implausibility(z, m, v) - 1.0) < 1e-12


def test_simulate_moments_returns_three_means_and_mc_variances():
    """M(c) is 3-vector; σ²_MC is the variance of the mean of R_m reps.

    At a smoke c we only check shape, finite-ness, and that levels sit in (0,1).
    """
    from poc_abm.kernel import World

    w = World()
    c = {"alpha": -1.0, "beta": 0.3, "gamma": 0.4, "kappa": 1.0, "sigma_eps": 0.05}
    m, mc = simulate_moments(w, c, reps=3)
    assert m.shape == (3,)
    assert mc.shape == (3,)
    assert np.all(np.isfinite(m))
    assert 0.0 < m[0] < 1.0
    assert 0.0 < m[2] < 1.0
    assert -1.0 <= m[1] <= 1.0

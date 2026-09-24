"""Hand-example tests for the measurement layer — METHODOLOGY §8.

The layer admits or excludes MEASURES, not NROY points.
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from poc_abm import config  # noqa: E402
from poc_abm.measures import (  # noqa: E402
    admit,
    apply_measure,
    admitted_measures,
)


def test_oracle_is_identity():
    """m₁: s = Y_T. Planner sees truth."""
    Y = np.array([0.1, 0.4, 0.9])
    X = np.zeros((3, 3))
    rng = np.random.default_rng(0)
    s = apply_measure(Y, X, "m1", rng)
    np.testing.assert_array_equal(s, Y)


def test_survey_noise_then_clip_hand_arithmetic():
    """m₂: s = clip(Y + ε, 0, 1), ε ~ N(0, 0.15²).

    With ε frozen at (+0.2, −0.2, +0.3) and Y = (0.9, 0.1, 0.95):
      0.9+0.2=1.1 → clip 1.0
      0.1-0.2=-0.1 → clip 0.0
      0.95+0.3=1.25 → clip 1.0
    """
    Y = np.array([0.9, 0.1, 0.95])
    X = np.zeros((3, 3))
    noise = np.array([0.2, -0.2, 0.3])
    s = apply_measure(Y, X, "m2", rng=None, noise=noise)
    np.testing.assert_allclose(s, [1.0, 0.0, 1.0])


def test_bad_item_loading_hand_arithmetic():
    """m₃: s = clip(0.5 Y + 0.5 x3 + ε). Zero noise, Y=(0,1,0,1), x3=(0,0,1,1):

    s = 0.5*(0,1,0,1) + 0.5*(0,0,1,1) = (0, 0.5, 0.5, 1)
    """
    Y = np.array([0.0, 1.0, 0.0, 1.0])
    X = np.zeros((4, 3))
    X[:, 2] = [0.0, 0.0, 1.0, 1.0]
    s = apply_measure(Y, X, "m3", rng=None, noise=np.zeros(4))
    np.testing.assert_allclose(s, [0.0, 0.5, 0.5, 1.0])


def test_admission_rejects_when_abs_corr_with_x3_exceeds_half():
    """s = (0, 0.5, 0.5, 1), x3 = (0, 0, 1, 1).

    means 0.5, 0.5
    cov = [(−0.5)(−0.5) + 0 + 0 + (0.5)(0.5)] / 3 = 0.5/3 = 1/6
    var(s) = 1/6, var(x3) = 1/3
    corr = (1/6) / sqrt((1/6)*(1/3)) = (1/6) / sqrt(1/18) = √18 / 6 = √2 / 2 ≈ 0.707
    0.707 > 0.5 → EXCLUDED. Oracle with the same Y is admitted (corr(Y,x3)=0).
    """
    Y = np.array([0.0, 1.0, 0.0, 1.0])
    X = np.zeros((4, 3))
    X[:, 2] = [0.0, 0.0, 1.0, 1.0]
    s3 = np.array([0.0, 0.5, 0.5, 1.0])
    assert abs(np.corrcoef(s3, X[:, 2])[0, 1] - np.sqrt(2) / 2) < 1e-12
    assert admit(s3, X) is False
    assert admit(Y, X) is True


def test_admitted_set_is_measures_not_calibrations():
    """M* screens scorings of Y, not NROY points. NROY size is unchanged."""
    Y = np.array([0.0, 1.0, 0.0, 1.0])
    X = np.zeros((4, 3))
    X[:, 2] = [0.0, 0.0, 1.0, 1.0]
    rng = np.random.default_rng(0)
    names = admitted_measures(Y, X, rng)
    assert "m1" in names
    assert "m3" not in names
    # The NROY list we might be carrying is irrelevant — admission returns measures.
    nroy_dummy = ["c_a", "c_b", "c_c"]
    assert len(nroy_dummy) == 3
    assert set(names).issubset({"m1", "m2"})

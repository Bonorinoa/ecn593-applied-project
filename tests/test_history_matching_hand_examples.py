"""Hand-example tests for history matching — METHODOLOGY §6–§7."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from poc_abm import config  # noqa: E402
from poc_abm.history_matching import (  # noqa: E402
    clip_box,
    latin_hypercube,
    run_waves,
    survivor_bbox,
    tau_threshold,
)


def test_tau_is_chi2_095_with_three_degrees_of_freedom():
    """τ = F^{-1}_{χ²_3}(0.95). scipy.stats.chi2.ppf(0.95, 3) ≈ 7.814727903.

    df = N_MOMENTS = 3, not a magic 7.81.
    """
    from scipy.stats import chi2

    t = tau_threshold()
    assert abs(t - float(chi2.ppf(config.HM_CONFIDENCE, config.N_MOMENTS))) < 1e-12
    assert abs(t - 7.814727903270927) < 1e-9


def test_bbox_inflation_hand_arithmetic():
    """Two points at 0 and 2; inflation 0.20.

    span = 2, pad = 0.20 * 2 / 2 = 0.20
    lo' = 0 - 0.20 = -0.20
    hi' = 2 + 0.20 =  2.20
    """
    pts = np.array([[0.0], [2.0]])
    lo, hi = survivor_bbox(pts, 0.20)
    assert abs(float(lo[0]) + 0.20) < 1e-12
    assert abs(float(hi[0]) - 2.20) < 1e-12


def test_clip_box_does_not_leave_the_frozen_parameter_box():
    """Inflated lo=-3, hi=0 on alpha is clipped to [-2.5, -0.5]."""
    lo = np.array([-3.0, 0.0, 0.0, 0.0, 0.0])
    hi = np.array([0.0, 1.0, 1.0, 3.0, 1.0])
    names = list(config.PARAM_BOX.keys())
    box = clip_box(lo, hi, names)
    assert box["alpha"] == config.PARAM_BOX["alpha"]
    assert box["beta"][0] == config.PARAM_BOX["beta"][0]
    assert box["kappa"][1] == config.PARAM_BOX["kappa"][1]


def test_lhs_puts_one_point_in_each_marginal_stratum():
    """Latin property: for n=4, each axis has exactly one point in
    [0,1/4), [1/4,2/4), [2/4,3/4), [3/4,1] after mapping a [0,1] box.
    """
    rng = np.random.default_rng(0)
    box = {"a": (0.0, 1.0), "b": (0.0, 1.0)}
    samples = latin_hypercube(4, box, rng)
    for name in box:
        u = np.sort(samples[name])
        for k in range(4):
            assert k / 4 <= u[k] < (k + 1) / 4


def test_empty_nroy_is_a_finding_not_a_rescue():
    """If every I(c) > τ, return 0 survivors and F-EMPTY. Do not touch τ.

    Fake moment map: M̂ ≡ (0,0,0), z ≡ (1,1,1), V ≡ I_3 so I = 3 > τ?  Wait:
    I = 1²+1²+1² = 3, and τ ≈ 7.81, so 3 would SURVIVE. Use z=(10,10,10)
    so I = 300 > τ.
    """
    z = np.array([10.0, 10.0, 10.0])
    sampling = np.ones(3)

    def fake_moments(world, c, reps=None):
        m = np.zeros(3)
        mc = np.zeros(3)
        return m, mc

    result = run_waves(
        world=None,
        z=z,
        sampling=sampling,
        n_points=8,
        n_waves=2,
        moment_fn=fake_moments,
    )
    assert result["finding"] == "F-EMPTY"
    assert result["nroy"].shape[0] == 0
    assert abs(result["tau"] - tau_threshold()) < 1e-12


def test_nroy_is_the_union_of_wave_survivors():
    """Wave 1 keeps points with alpha < -1.5; wave 2 draws in the inflated
    bbox of those and keeps the same rule. Union has at least the wave-1 set.
    Fake I uses only alpha so this is arithmetic on the box, not a kernel.
    """
    z = np.zeros(3)
    sampling = np.ones(3)

    def fake_moments(world, c, reps=None):
        # I = ((z0 - m0)^2)/V00 with m0 = 0 if alpha < -1.5 else 10
        m0 = 0.0 if c["alpha"] < -1.5 else 10.0
        return np.array([m0, 0.0, 0.0]), np.zeros(3)

    result = run_waves(
        world=None,
        z=z,
        sampling=sampling,
        n_points=40,
        n_waves=2,
        moment_fn=fake_moments,
    )
    assert result["finding"] != "F-EMPTY"
    assert result["nroy"].shape[0] >= result["wave_kept"][0]
    assert result["nroy"].shape[0] == sum(result["wave_kept"])
    names = result["param_names"]
    i_alpha = names.index("alpha")
    assert np.all(result["nroy"][:, i_alpha] < -1.5)

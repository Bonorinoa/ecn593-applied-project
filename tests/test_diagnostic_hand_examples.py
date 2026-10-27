"""Hand-example tests for the diagnostic overlay (both foils, the verdict rule)."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from poc_abm.diagnostic import (  # noqa: E402
    classify_interval,
    containment_flags,
    covers_truth,
    foil1_policy,
    ols_ate_hc1,
    policy_gap_decomposition,
)
from poc_abm.kernel import World  # noqa: E402


def test_overconf_is_strict_subset_of_the_image_interior():
    """I = [0.10, 0.12], Θ = [0.00, 0.50].

    0.00 < 0.10 and 0.12 < 0.50, so I sits in the interior of Θ → F-OVERCONF.
    """
    assert classify_interval((0.10, 0.12), (0.00, 0.50)) == "F-OVERCONF"


def test_honest_covers_the_whole_image():
    """I = [-1, 1], Θ = [0.00, 0.50]. I covers [L,U] → F-HONEST."""
    assert classify_interval((-1.0, 1.0), (0.00, 0.50)) == "F-HONEST"


def test_neither_label_when_intervals_only_overlap():
    """I = [0.40, 0.60], Θ = [0.00, 0.50]. Overlap, not subset, not cover.

    Only F-OVERCONF and F-HONEST are named; anything else is no verdict.
    """
    assert classify_interval((0.40, 0.60), (0.00, 0.50)) is None


def test_covers_truth_inside_and_outside():
    """CI [0.20, 0.40]: truth 0.25 is inside, truth 0.50 is not, nan is never covered."""
    assert covers_truth((0.20, 0.40), 0.25) is True
    assert covers_truth((0.20, 0.40), 0.50) is False
    assert covers_truth((0.20, 0.40), float("nan")) is False


def test_containment_flags_distinguish_point_and_planted_truths():
    """Foil 1 covers its point truth but misses planted truth; Foil 2 does the reverse."""
    flags = containment_flags(
        foil1_ci=(0.20, 0.40),
        foil2_ci=(-0.10, 0.10),
        theta2_true=0.25,
        spill_true=0.20,
        theta2_planted=0.50,
        spill_planted=0.00,
    )
    assert flags == {
        "foil1_covers_truth": True,
        "foil2_covers_truth": False,
        "foil1_covers_planted_truth": False,
        "foil2_covers_planted_truth": True,
    }


def test_ols_ate_is_difference_in_means_when_X_is_balanced():
    """Four agents: D=(0,0,1,1), Y=(0,0,1,1), one orthogonal covariate.

    Design is 4 × 3 (intercept, D, x). Y = D exactly, x ⟂ D,
    so the D coefficient is 1. Arithmetic: treated mean 1, control mean 0.
    """
    y = np.array([0.0, 0.0, 1.0, 1.0])
    D = np.array([0.0, 0.0, 1.0, 1.0])
    X = np.array([[0.0], [1.0], [0.0], [1.0]])
    out = ols_ate_hc1(y, D, X)
    assert abs(out["ate"] - 1.0) < 1e-12
    assert out["estimator"] == "OLS-HC1"
    assert out["ci"][0] <= 1.0 <= out["ci"][1]


def _small_world(n=20, seed=3):
    """Ring of n people plus 8 random chords: every degree is at least 2."""
    rng = np.random.default_rng(seed)
    adj = np.zeros((n, n))
    for i in range(n):
        adj[i, (i + 1) % n] = adj[(i + 1) % n, i] = 1.0
    for _ in range(8):
        i, j = rng.choice(n, size=2, replace=False)
        adj[i, j] = adj[j, i] = 1.0
    return World.from_arrays(adj, rng.random((n, 3)))


def test_foil1_policy_is_share_times_the_ols_interval():
    """SUTVA bridge: θ₂ = (k/N) × effect on the seeded. N = 20 and 2 people seeded.

    Every number of the policy interval must be exactly 2/20 = 0.1 times
    the OLS number.
    """
    w = _small_world()
    rng = np.random.default_rng(0)
    D = np.zeros(20)
    D[[4, 11]] = 1.0
    y = 0.2 + 0.3 * D + 0.01 * rng.standard_normal(20)
    ols = ols_ate_hc1(y, D, w.X)
    f = foil1_policy(w, y, D)
    assert f["share"] == 0.1
    assert f["beta"] == ols["ate"]
    assert f["estimate"] == 0.1 * ols["ate"]
    assert f["ci"] == (0.1 * ols["ci"][0], 0.1 * ols["ci"][1])


def test_decomposition_parts_add_up_to_theta2():
    """θ₂ = seeded part + unseeded part, at any c (paired streams)."""
    w = _small_world()
    c = {"alpha": -1.0, "beta": 0.3, "gamma": 0.5, "kappa": 1.2, "sigma_eps": 0.1}
    d = policy_gap_decomposition(w, c, reps=10, displayed_beta=0.0)
    assert abs(d["seeded_part"] + d["unseeded_part"] - d["theta2"]) < 1e-12
    assert d["unseeded_part"] > 0.0  # positive peer effect reaches the unseeded


def test_decomposition_unseeded_part_is_zero_without_peer_effects():
    """γ = 0: an unseeded person never feels the campaign.

    Control and degree arms share Y(0) and every shock (paired streams), so an
    unseeded person's path is identical in both arms, bit for bit. The unseeded
    part must be exactly 0, and θ₂ equals the seeded part.
    """
    w = _small_world()
    c = {"alpha": -1.0, "beta": 0.3, "gamma": 0.0, "kappa": 1.2, "sigma_eps": 0.1}
    d = policy_gap_decomposition(w, c, reps=10, displayed_beta=0.0)
    assert d["unseeded_part"] == 0.0
    assert abs(d["theta2"] - d["seeded_part"]) < 1e-15

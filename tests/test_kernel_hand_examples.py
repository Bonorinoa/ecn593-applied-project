"""Hand-example tests: the pedagogical contract.

These tests exist so a reader can VERIFY the kernel by hand before trusting any
wave. Each test states the arithmetic it checks. If any of these fail, nothing
downstream means anything.

Run:  pytest tests/ -v
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from poc_abm.kernel import (  # noqa: E402
    World,
    logistic,
    assign,
    simulate,
    simulate_panel,
    stream_seed,
)
from poc_abm import config  # noqa: E402


def test_logistic_endpoints():
    """Λ(0)=0.5, Λ(∞)=1, Λ(−∞)=0 — the squashing map does what it says."""
    assert abs(logistic(0.0) - 0.5) < 1e-12
    assert logistic(60.0) > 0.999999
    assert logistic(-60.0) < 1e-12


def test_control_arm_is_all_zeros():
    """π₀ assigns no treatment — METHODOLOGY §3."""
    w = World()
    D = assign(w, "control", np.random.default_rng(0))
    assert D.sum() == 0


def test_seed_arms_seed_exactly_ten_percent():
    """π₁ and π₂ each seed ceil(0.1·N) = 80 agents."""
    w = World()
    k = int(np.ceil(config.SEED_FRACTION * config.N_AGENTS))
    assert k == 80
    D_rand = assign(w, "random", np.random.default_rng(1))
    D_deg = assign(w, "degree", np.random.default_rng(2))
    assert D_rand.sum() == k
    assert D_deg.sum() == k


def test_degree_arm_picks_highest_degrees():
    """Every degree-seeded agent has degree >= every non-seeded agent's degree."""
    w = World()
    D = assign(w, "degree", np.random.default_rng(3))
    assert w.degrees[D == 1].min() >= w.degrees[D == 0].max()


def test_kernel_converges_to_hand_computed_fixed_point():
    """With alpha=beta=gamma=kappa=0 and noise ~0, every agent converges to
    its own fixed point Lambda(X_i . eta) — computable by hand from world.X.
    The population mean must match E[Lambda(X . eta)] up to Monte Carlo dust.
    """
    w = World()
    c = {"alpha": 0.0, "beta": 0.0, "gamma": 0.0, "kappa": 0.0, "sigma_eps": 1e-12}
    y, _ = simulate_panel(w, c, "control", seed_offset=0)
    expected_mean = logistic(w.X @ np.asarray(config.ETA_FIXED)).mean()
    assert abs(y.mean() - expected_mean) < 0.005


def test_treatment_raises_outcome():
    """κ > 0 must raise the mean under either seed arm vs control, paired reps.

    This is the sanity check that the intervention channel is wired correctly.
    """
    w = World()
    c = {"alpha": -1.0, "beta": 0.3, "gamma": 0.4, "kappa": 1.5, "sigma_eps": 0.05}
    y0, _ = simulate_panel(w, c, "control", seed_offset=7)
    y2, _ = simulate_panel(w, c, "degree", seed_offset=7)
    assert y2.mean() > y0.mean()


def test_determinism_same_inputs_same_output():
    """Same (rule, seed_offset) -> identical run. Required for paired contrasts."""
    w = World()
    c = {"alpha": -1.0, "beta": 0.3, "gamma": 0.4, "kappa": 1.0, "sigma_eps": 0.1}
    a = simulate(w, c, "random", seed_offset=42)
    b = simulate(w, c, "random", seed_offset=42)
    assert a == b


def test_stream_seed_is_crc32_of_length_prefixed_key():
    """METHODOLOGY §9: never Python hash(); crc32 of a length-prefixed key.

    Arithmetic: key = b'6:random:7' because len('random')=6, rule='random',
    offset=7. zlib.crc32 of that exact byte string is the seed. Two calls
    match; the mapping does not use hash().
    """
    import zlib

    key = f"{len('random')}:random:7".encode("ascii")
    expected = zlib.crc32(key)
    assert stream_seed("random", 7) == expected
    assert stream_seed("random", 7) == stream_seed("random", 7)
    # Different labels must not collide into Python's salted hash path.
    assert stream_seed("random", 7) != stream_seed("degree", 7)


def test_paired_arms_share_initial_state_and_noise():
    """Paired reps: same offset ⇒ same Y(0) and same ε(t); only D differs.

    Construction: zero dynamics (alpha=beta=gamma=kappa=0) and tiny noise
    so Y_T ≈ Λ(Xη) anyway; the stronger check is that control and degree
    panels are identical when kappa=0, which only holds if the noise
    stream does not include the rule name.
    """
    w = World()
    c = {"alpha": 0.0, "beta": 0.0, "gamma": 0.0, "kappa": 0.0, "sigma_eps": 0.05}
    y0, d0 = simulate_panel(w, c, "control", seed_offset=11)
    y2, d2 = simulate_panel(w, c, "degree", seed_offset=11)
    assert d0.sum() == 0
    assert d2.sum() == int(np.ceil(config.SEED_FRACTION * config.N_AGENTS))
    np.testing.assert_allclose(y0, y2, atol=1e-12)


def test_hand_built_world_uses_supplied_graph():
    """World.from_arrays is the hook for N=4 hand examples (path A-B-C-D).

    Adjacency is the 4x4 path; degrees must be (1, 2, 2, 1).
    """
    A = np.array(
        [
            [0, 1, 0, 0],
            [1, 0, 1, 0],
            [0, 1, 0, 1],
            [0, 0, 1, 0],
        ],
        dtype=float,
    )
    X = np.zeros((4, 3))
    w = World.from_arrays(A, X)
    assert w.n == 4
    np.testing.assert_array_equal(w.degrees, np.array([1.0, 2.0, 2.0, 1.0]))

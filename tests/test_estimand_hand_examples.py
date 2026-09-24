"""Hand-example tests for estimands and the exposure map — METHODOLOGY §4, §7, §9."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from poc_abm.kernel import World  # noqa: E402
from poc_abm.estimand import (  # noqa: E402
    diagnostic_worlds,
    exposure_probs,
    exposure_share,
    interval_image,
    stratum_labels,
    thetas_from_means,
    true_spill_from_panel,
)


def test_theta_definitions_are_arm_contrasts():
    """θ₁ = E[Ȳ|π₁]−E[Ȳ|π₀], θ₂ = E[Ȳ|π₂]−E[Ȳ|π₀], τ = θ₂−θ₁.

    Hand numbers: Ȳ(π₀)=0.40, Ȳ(π₁)=0.50, Ȳ(π₂)=0.70
      θ₁ = 0.10, θ₂ = 0.30, targeting premium τ = 0.20.
    """
    t1, t2, prem = thetas_from_means(0.40, 0.50, 0.70)
    assert abs(t1 - 0.10) < 1e-15
    assert abs(t2 - 0.30) < 1e-15
    assert abs(prem - 0.20) < 1e-15


def test_interval_image_is_min_max_not_a_mean():
    """Θ = {θ(c): c ∈ sample} reported as [L,U] = [min, max]. Not a posterior."""
    L, U = interval_image(np.array([0.2, -0.1, 0.4, 0.0]))
    assert L == -0.1
    assert U == 0.4


def test_diagnostic_worlds_are_functions_of_I_only():
    """c0_min = smallest I; c0_med = median I after sorting. Never of θ.

    I = (0.4, 0.1, 0.3) → min index 1, median index 2 (sorted I: 0.1, 0.3, 0.4).
    """
    nroy = np.array([[1.0], [2.0], [3.0]])
    I = np.array([0.4, 0.1, 0.3])
    worlds = diagnostic_worlds(nroy, I)
    assert worlds["min_I"]["index"] == 1
    assert worlds["median_I"]["index"] == 2
    np.testing.assert_array_equal(worlds["min_I"]["c_row"], nroy[1])


def _path_world():
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
    return World.from_arrays(A, X)


def test_path_graph_exposure_share_treat_B():
    """Path A–B–C–D, treat {B}. s_i = (sum_{j~i} D_j) / k_i  (METHODOLOGY §9).

    A~B: k_A=1, neighbour B treated → s_A = 1/1 = 1
    B~A,C: k_B=2, both untreated → s_B = 0
    C~B,D: k_C=2, B treated → s_C = 1/2 = 0.5
    D~C: k_D=1, C untreated → s_D = 0

    Strata at cut 0.25:
      A → S0c (D=0, s=1 ≥ 0.25)
      B → S1  (D=1)
      C → S0c (D=0, s=0.5 ≥ 0.25)
      D → S0a (D=0, s=0)

    Note: AMENDMENT-01 wrote s=(0, ½, ½, 0) and A→S0a; that contradicts
    s_i = neighbour share on a path. The methodology definition wins.
    """
    w = _path_world()
    D = np.array([0.0, 1.0, 0.0, 0.0])
    s = exposure_share(w, D)
    np.testing.assert_allclose(s, [1.0, 0.0, 0.5, 0.0])
    lab = stratum_labels(D, s, cut=0.25)
    # codes: S1=1, S0a=0, S0b=2, S0c=3
    assert lab[0] == "S0c"
    assert lab[1] == "S1"
    assert lab[2] == "S0c"
    assert lab[3] == "S0a"


def test_true_spill_on_path_is_mean_S0c_minus_mean_S0a():
    """Y = (1, 3, 5, 1) on the path, treat {B}.

    S0c = {A,C} → mean (1+5)/2 = 3
    S0a = {D}   → mean 1
    δ_spill = 3 − 1 = 2
    δ_dir   = mean(S1) − mean(S0a) = 3 − 1 = 2
    """
    w = _path_world()
    D = np.array([0.0, 1.0, 0.0, 0.0])
    Y = np.array([1.0, 3.0, 5.0, 1.0])
    d = true_spill_from_panel(w, Y, D, cut=0.25, min_n=1)
    assert abs(d["delta_spill"] - 2.0) < 1e-15
    assert abs(d["delta_dir"] - 2.0) < 1e-15


def test_exposure_probs_path_node_A_hand_arithmetic():
    """N=4, k=1, node A has degree 1. SRSWOR.

    P(D_A=1) = 1/4
    P(D_A=0) = 3/4
    Given untreated, the single treated unit is equally likely among {B,C,D}:
      P(K=1 | D_A=0) = 1/3  (treated is B) → s=1 → S0c
      P(K=0 | D_A=0) = 2/3  → s=0 → S0a
    so p_S0a(A) = (3/4)*(2/3) = 1/2
       p_S0c(A) = (3/4)*(1/3) = 1/4
       p_S0b(A) = 0
    """
    w = _path_world()
    p = exposure_probs(w, k_treat=1, cut=0.25)
    assert abs(p["S1"][0] - 0.25) < 1e-12
    assert abs(p["S0a"][0] - 0.50) < 1e-12
    assert abs(p["S0c"][0] - 0.25) < 1e-12
    assert abs(p["S0b"][0] - 0.00) < 1e-12

"""Hand-example tests for the Foil 2 variance (Aronow and Samii 2017).

The Foil 2 estimate weights each person by 1 / P(exposure). Its variance needs
the JOINT probability that two people have given exposures at the same time,
because people who share treated neighbors move together. These tests check
the joint probabilities by full enumeration, then check the variance estimator
against the exact randomization variance on a graph small enough to list every
assignment.
"""
import itertools
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from poc_abm.kernel import World, assign  # noqa: E402
from poc_abm.estimand import (  # noqa: E402
    exposure_indicators,
    exposure_mc,
    exposure_share,
    ht_cov,
    joint_probs,
    stratum_labels,
)

A, B, C, D = 0, 1, 2, 3


def _path(n):
    adj = np.zeros((n, n))
    for i in range(n - 1):
        adj[i, i + 1] = adj[i + 1, i] = 1.0
    return World.from_arrays(adj, np.zeros((n, 3)))


def _all_assignments(n, k):
    rows = []
    for idx in itertools.combinations(range(n), k):
        d = np.zeros(n)
        d[list(idx)] = 1.0
        rows.append(d)
    return np.array(rows)


def test_path4_joint_probabilities_by_enumeration():
    """Path A-B-C-D, one treated person, cut 0.25. Four equal assignments.

    Treat A: A=S1, B=S0c (share 1/2), C=S0a, D=S0a.
    Treat B: A=S0c, B=S1, C=S0c, D=S0a.
    Treat C: A=S0a, B=S0c, C=S1, D=S0c.
    Treat D: A=S0a, B=S0a, C=S0c, D=S1.
    P(A in S0a) = 2/4 (treat C or D).  P(D in S0a) = 2/4 (treat A or B).
    P(A in S0a and D in S0a) = 0: no assignment leaves both unexposed.
    P(A in S0a and C in S0c) = 1/4: only "treat D".
    """
    w = _path(4)
    ind = exposure_indicators(w, _all_assignments(4, 1), cut=0.25, merged=False)
    jp = joint_probs(ind)
    assert jp["p"]["S0a"][A] == 0.5
    assert jp["p"]["S0a"][D] == 0.5
    assert jp["pi"][("S0a", "S0a")][A, D] == 0.0
    assert jp["pi"][("S0a", "S0c")][A, C] == 0.25
    # a person is never in two exposures at once
    assert jp["pi"][("S0a", "S0c")][A, A] == 0.0


def test_monte_carlo_joint_probabilities_match_enumeration():
    """20,000 simulated assignments reproduce the enumerated numbers above.

    A zero joint probability stays exactly zero: no draw can produce it.
    """
    w = _path(4)
    mc = exposure_mc(w, k_treat=1, cut=0.25, merged=False, draws=20_000, seed=7)
    assert abs(mc["pi"][("S0a", "S0c")][A, C] - 0.25) < 0.015
    assert abs(mc["p"]["S0a"][A] - 0.5) < 0.015
    assert mc["pi"][("S0a", "S0a")][A, D] == 0.0


def test_vectorized_indicators_match_stratum_labels_on_frozen_world():
    """exposure_indicators is the same map as stratum_labels, one row at a time."""
    w = World()
    rng = np.random.default_rng(3)
    rows = np.array([assign(w, "random", rng) for _ in range(25)])
    ind = exposure_indicators(w, rows, cut=0.25, merged=False)
    for r, d in enumerate(rows):
        lab = stratum_labels(d, exposure_share(w, d), 0.25)
        for name in ("S1", "S0a", "S0c"):
            np.testing.assert_array_equal(ind[name][r], lab == name)


def test_variance_estimator_is_conservative_by_full_enumeration():
    """Path of 6 people, 2 treated: 15 equally likely assignments.

    Fixed outcomes y_i = 0.2 + 0.05 i (+0.1 if exposed). For each assignment
    compute the Horvitz-Thompson totals T(S0c), T(S0a) and the contrast
    T(S0c) - T(S0a). Its exact variance is the spread over the 15 assignments.
    The Aronow-Samii estimate V = V(c) + V(a) - 2 Cov(c, a) must be
    conservative on average: mean over the 15 assignments >= exact variance.
    It is not exact because some pairs can never share an exposure
    (joint probability 0); those pairs get the Young-inequality correction.
    """
    n = 6
    w = _path(n)
    rows = _all_assignments(n, 2)
    ind = exposure_indicators(w, rows, cut=0.25, merged=False)
    jp = joint_probs(ind)
    base = 0.2 + 0.05 * np.arange(n)
    totals, v_hat = [], []
    for r in range(rows.shape[0]):
        y = base + 0.1 * ind["S0c"][r]
        a_c = ind["S0c"][r] * y
        a_a = ind["S0a"][r] * y
        t = (a_c / np.where(jp["p"]["S0c"] > 0, jp["p"]["S0c"], 1)).sum() - (
            a_a / np.where(jp["p"]["S0a"] > 0, jp["p"]["S0a"], 1)
        ).sum()
        totals.append(t)
        v = (
            ht_cov(a_c, a_c, jp["p"]["S0c"], jp["p"]["S0c"], jp["pi"][("S0c", "S0c")], same=True)
            + ht_cov(a_a, a_a, jp["p"]["S0a"], jp["p"]["S0a"], jp["pi"][("S0a", "S0a")], same=True)
            - 2 * ht_cov(a_c, a_a, jp["p"]["S0c"], jp["p"]["S0a"], jp["pi"][("S0c", "S0a")], same=False)
        )
        v_hat.append(v)
    exact = float(np.var(totals))  # population variance over equally likely assignments
    assert np.mean(v_hat) >= exact - 1e-12
    assert exact > 0.0


def test_single_total_is_exactly_unbiased_when_all_joint_probabilities_positive():
    """No zero joint probabilities -> the HT variance estimator is exactly unbiased.

    Path of 4 people, 2 treated: 6 equally likely pairs. Exposure S1 (treated).
    p_i = 2/4 = 1/2 and pi_ij = P(both treated) = 1/6 > 0 for every pair.
    Outcomes y = (1, 2, 3, 4). T = sum over treated of y_i / (1/2) = 2 (y_i + y_j).
    The six pair sums are 3, 4, 5, 5, 6, 7, so T = 6, 8, 10, 10, 12, 14.
    Mean 10. Exact variance = (16 + 4 + 0 + 0 + 4 + 16) / 6 = 20/3.
    The estimator averaged over the six assignments must equal 20/3.
    """
    n = 4
    w = _path(n)
    rows = _all_assignments(n, 2)
    ind = exposure_indicators(w, rows, cut=0.25, merged=False)
    jp = joint_probs(ind)
    y = np.arange(1, n + 1, dtype=float)
    totals = [(ind["S1"][r] * y / 0.5).sum() for r in range(rows.shape[0])]
    assert abs(np.var(totals) - 20.0 / 3.0) < 1e-12
    v = [
        ht_cov(ind["S1"][r] * y, ind["S1"][r] * y, jp["p"]["S1"], jp["p"]["S1"], jp["pi"][("S1", "S1")], same=True)
        for r in range(rows.shape[0])
    ]
    assert abs(np.mean(v) - 20.0 / 3.0) < 1e-12


def test_cache_follows_graph_contents_not_object_identity():
    """The joint-probability cache must never serve another graph's numbers.

    Path 0-1-2-3 and star 0-{1,2,3} both have 4 people and 3 edges. Build the
    path, fill the cache, then turn the SAME object into the star (verifier
    finding, t_5dfaef63 item 5). One treated person, cut 0.25.
    On the star, person 0 is in S0c whenever a leaf is treated: P = 3/4 exactly.
    On the path, person 0 is in S0c only when person 1 is treated: P = 1/4.
    """
    from poc_abm.estimand import _exposure_mc_cached

    path = np.zeros((4, 4))
    for i, j in ((0, 1), (1, 2), (2, 3)):
        path[i, j] = path[j, i] = 1.0
    star = np.zeros((4, 4))
    for j in (1, 2, 3):
        star[0, j] = star[j, 0] = 1.0
    w = World.from_arrays(path, np.zeros((4, 3)))
    p_path = _exposure_mc_cached(w, 1, 0.25, False)["p"]["S0c"][0]
    w.adjacency[:] = star
    w.degrees = np.maximum(w.adjacency.sum(axis=1), 1.0)
    p_star = _exposure_mc_cached(w, 1, 0.25, False)["p"]["S0c"][0]
    assert abs(p_path - 0.25) < 0.02
    assert abs(p_star - 0.75) < 0.02

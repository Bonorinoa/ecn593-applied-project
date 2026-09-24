"""Hand-example tests for the diagnostic overlay — METHODOLOGY §9–§10."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from poc_abm.diagnostic import classify_interval, oracle_gate, ols_ate_hc1  # noqa: E402


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

    Spec names only F-OVERCONF and F-HONEST; we do not invent a third finding.
    """
    assert classify_interval((0.40, 0.60), (0.00, 0.50)) is None


def test_oracle_gate_passes_when_truth_is_inside_the_ci():
    """Point 0.30, CI [0.20, 0.40], truth 0.25 → harness OK."""
    assert oracle_gate(0.30, (0.20, 0.40), 0.25) is True


def test_oracle_gate_fails_when_truth_misses_the_ci():
    """Point 0.30, CI [0.20, 0.40], truth 0.50 → harness broken."""
    assert oracle_gate(0.30, (0.20, 0.40), 0.50) is False


def test_ols_ate_is_difference_in_means_when_X_is_balanced():
    """Four agents: D=(0,0,1,1), Y=(0,0,1,1), one orthogonal covariate.

    Design is 4 × 3 (intercept, D, x). Y = D exactly, x ⟂ D,
    so the D coefficient is 1. Arithmetic: treated mean 1, control mean 0.
    """
    import numpy as np

    y = np.array([0.0, 0.0, 1.0, 1.0])
    D = np.array([0.0, 0.0, 1.0, 1.0])
    X = np.array([[0.0], [1.0], [0.0], [1.0]])
    out = ols_ate_hc1(y, D, X)
    assert abs(out["ate"] - 1.0) < 1e-12
    assert out["estimator"] == "OLS-HC1"
    assert out["ci"][0] <= 1.0 <= out["ci"][1]

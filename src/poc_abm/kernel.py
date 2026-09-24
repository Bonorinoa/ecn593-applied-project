"""The ABM kernel — one model structure, many worlds.

This module exists to be READ. Every function is short, commented, and mirrors
METHODOLOGY.md §1–§3 line by line. If you change anything here, you are changing
the specification, not an implementation detail.
"""
import zlib

import numpy as np

from . import config


def stream_seed(label: str, offset: int) -> int:
    """Stable RNG seed from a length-prefixed key (METHODOLOGY §9).

    Never Python's hash() — CPython salts string hashes per process, so
    hash(('random', 7)) is a different integer every session.
    """
    key = f"{len(label)}:{label}:{int(offset)}".encode("ascii")
    return zlib.crc32(key)


def n_treated(n: int | None = None) -> int:
    """ceil(SEED_FRACTION · N). Derived, not a second frozen integer."""
    n = config.N_AGENTS if n is None else n
    return int(np.ceil(config.SEED_FRACTION * n))


class World:
    """A frozen environment: graph + covariates.

    Drawn ONCE with fixed seeds; every simulation run shares this world.
    Only parameters c and noise vary across runs.
    """

    def __init__(self):
        rng = np.random.default_rng(config.SEED_GRAPH)
        n = config.N_AGENTS
        self.n = n
        A = rng.random((n, n)) < config.EDGE_P
        A = A | A.T  # undirected
        np.fill_diagonal(A, False)  # no self-loops
        self.adjacency = A.astype(float)
        self.degrees = np.maximum(self.adjacency.sum(axis=1), 1.0)

        rx = np.random.default_rng(config.SEED_X)
        self.X = rx.random((n, config.N_COVARIATES))  # education, resource, propensity

    @classmethod
    def from_arrays(cls, adjacency: np.ndarray, X: np.ndarray) -> "World":
        """Hand-built world for pedagogical tests. Does not touch frozen seeds."""
        w = cls.__new__(cls)
        A = np.asarray(adjacency, dtype=float)
        np.fill_diagonal(A, 0.0)
        w.adjacency = A
        w.n = A.shape[0]
        w.degrees = np.maximum(A.sum(axis=1), 1.0)
        w.X = np.asarray(X, dtype=float)
        if w.X.shape[0] != w.n:
            raise ValueError("X rows must match adjacency size")
        return w


def logistic(z):
    """Numerically stable squashing map Lambda: R -> (0,1)."""
    return 1.0 / (1.0 + np.exp(-np.clip(z, -60.0, 60.0)))


def assign(world, rule: str, rng) -> np.ndarray:
    """Return the treatment vector D for a named assignment rule.

    rule in {"control", "random", "degree"} — METHODOLOGY §3.
    rng is used only for the random arm (SRSWOR).
    """
    n = world.n
    k = n_treated(n)
    D = np.zeros(n)
    if rule == "control":
        return D
    if rule == "random":
        idx = rng.choice(n, size=k, replace=False)
        D[idx] = 1.0
        return D
    if rule == "degree":
        # ties broken by index: lexsort is last-key-primary
        order = np.lexsort((np.arange(n), -world.degrees))
        D[order[:k]] = 1.0
        return D
    raise ValueError(f"unknown rule: {rule}")


def simulate_panel(world, c: dict, rule: str, seed_offset: int):
    """Run ONE simulation; return (Y_T, D).

    Paired-rep contract: Y(0) and ε(t) come from stream_seed('state', offset)
    and do not depend on the rule. Assignment uses a separate stream so that
    π₁'s SRSWOR draw is part of ω without desynchronizing the dynamics.
    """
    rng_state = np.random.default_rng(stream_seed("state", seed_offset))
    rng_assign = np.random.default_rng(stream_seed(f"assign:{rule}", seed_offset))

    n = world.n
    Y = rng_state.random(n)
    eta = np.asarray(config.ETA_FIXED)
    Xw = world.X @ eta
    D = assign(world, rule, rng_assign)
    sigma = c["sigma_eps"]
    inv_deg = 1.0 / world.degrees

    for t in range(config.HORIZON):
        peer_term = c["gamma"] * (world.adjacency @ Y) * inv_deg
        treat = c["kappa"] * D * (t >= config.INTERVENTION_TIME)
        eps = sigma * rng_state.standard_normal(n)
        z = c["alpha"] + c["beta"] * Y + peer_term + Xw + treat + eps
        Y = logistic(z)

    return Y.copy(), D.copy()


def simulate(world, c: dict, rule: str, seed_offset: int) -> float:
    """Same dynamics as simulate_panel; return the population mean Ȳ_T."""
    Y, _ = simulate_panel(world, c, rule, seed_offset)
    return float(Y.mean())

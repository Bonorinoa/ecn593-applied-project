"""Two-row overlay figure — METHODOLOGY §9, README A7.

Rows: c₀^min (top) and c₀^med (bottom).
Columns: policy contrast θ₂ against Θ_hm | spillover δ_spill against Θ_exp.
Each foil is drawn against ITS OWN image. Not a posterior ribbon.
"""
from pathlib import Path

import numpy as np

from . import config


def _interval_h(ax, y, lo, hi, color, label, lw=2.5):
    ax.hlines(y, lo, hi, colors=color, linewidth=lw, label=label)
    ax.plot([lo, hi], [y, y], "o", color=color, markersize=4)


def draw_overlay(payload: dict, path: Path | None = None) -> Path:
    """payload keys: worlds.min_I / median_I each with
    Theta_hm (L,U), Theta_exp (L,U), theta2_true, spill_true,
    foil1_ci or forest_ci (lo,hi), e2_ci (lo,hi), Theta_cv (L,U) optional.
    foil1_label: legend for the SUTVA interval (this run: OLS-HC1).
    """
    import matplotlib.pyplot as plt

    path = Path(path) if path is not None else config.FIGURES_DIR / "overlay.png"
    path.parent.mkdir(parents=True, exist_ok=True)

    fig, axes = plt.subplots(2, 2, figsize=(9.5, 5.5), sharex=False)
    row_names = (("min_I", r"$c_0^{\min I}$ (best match)"), ("median_I", r"$c_0^{\mathrm{med} I}$"))
    for r, (key, title) in enumerate(row_names):
        w = payload["worlds"][key]
        # left: policy
        ax = axes[r, 0]
        L, U = w["Theta_hm"]
        ax.axvspan(L, U, color="#4C78A8", alpha=0.25, label=r"$\Theta_{\mathrm{hm}}$")
        foil1_ci = w.get("foil1_ci", w["forest_ci"])
        foil1_label = w.get("foil1_label", "OLS-HC1")
        _interval_h(ax, 1, *foil1_ci, "#F58518", foil1_label)
        ax.plot(w["theta2_true"], 0, "k*", markersize=10, label=r"$\theta_2(c_0)$")
        if w.get("theta2_star") is not None:
            ax.plot(w["theta2_star"], 0.35, "k^", markersize=8, label=r"$\theta_2(c^\star)$")
        if w.get("Theta_cv") is not None and np.isfinite(w["Theta_cv"][0]):
            _interval_h(ax, 2, *w["Theta_cv"], "#54A24B", r"$\Theta_{\mathrm{cv}}$", lw=2)
        ax.set_yticks([])
        ax.set_title(f"{title}  —  policy contrast")
        ax.set_xlabel(r"$\theta_2$")
        if r == 0:
            ax.legend(loc="upper right", fontsize=8, frameon=False)

        # right: spillover
        ax = axes[r, 1]
        L, U = w["Theta_exp"]
        ax.axvspan(L, U, color="#72B7B2", alpha=0.25, label=r"$\Theta_{\mathrm{exp}}$")
        _interval_h(ax, 1, *w["e2_ci"], "#E45756", r"$I_{E2}$")
        ax.plot(w["spill_true"], 0, "k*", markersize=10, label=r"$\delta_{\mathrm{spill}}(c_0)$")
        if w.get("spill_star") is not None:
            ax.plot(w["spill_star"], 0.35, "k^", markersize=8, label=r"$\delta_{\mathrm{spill}}(c^\star)$")
        ax.set_yticks([])
        ax.set_title(f"{title}  —  spillover")
        ax.set_xlabel(r"$\delta_{\mathrm{spill}}$")
        if r == 0:
            ax.legend(loc="upper right", fontsize=8, frameon=False)

    fig.suptitle("Not-ruled-out images vs one-world intervals  (two pre-declared $c_0$)", fontsize=11)
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)
    return path


def draw_empty(info: dict, path: Path | None = None) -> Path:
    """F-EMPTY report: z vs closest M, and I against τ. Not an overlay of Θ."""
    import matplotlib.pyplot as plt

    path = Path(path) if path is not None else config.FIGURES_DIR / "overlay.png"
    path.parent.mkdir(parents=True, exist_ok=True)

    z = np.asarray(info["z"], dtype=float)
    closest = info["closest"]
    m = np.asarray(closest["M"], dtype=float)
    tau = float(info["tau"])
    names = ("level (π₂)", "corr(Y, x1)", "level (π₁)")

    fig, axes = plt.subplots(1, 2, figsize=(9.5, 3.8))
    ax = axes[0]
    x = np.arange(3)
    ax.scatter(x, z, marker="D", s=50, color="#4C78A8", label="anchor z (rescaled)")
    ax.scatter(x, m, marker="o", s=50, color="#E45756", label="closest M(c) in C")
    ax.set_xticks(x, names)
    ax.set_ylim(0, 1)
    ax.set_ylabel("moment (unit interval)")
    ax.legend(frameon=False, fontsize=8)
    ax.set_title("anchors vs closest kernel moments")

    ax = axes[1]
    stats = info["wave_I_stats"][0]
    ax.axhline(tau, color="#54A24B", lw=2, label=fr"$\tau = {tau:.3f}$")
    ax.plot([0, 1, 2], [stats["min"], stats["median"], stats["max"]], "o-", color="#E45756")
    ax.set_xticks([0, 1, 2], ["min I", "median I", "max I"])
    ax.set_ylabel("implausibility I(c)")
    ax.set_title("wave-1 I(c) vs frozen τ  (F-EMPTY)")
    ax.legend(frameon=False, fontsize=8)

    fig.suptitle("F-EMPTY: no calibration in C is not-ruled-out  (τ not loosened)", fontsize=11)
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)
    return path

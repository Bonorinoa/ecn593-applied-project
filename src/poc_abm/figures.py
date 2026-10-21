"""Two-row overlay figure.

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


def draw_overlay(payload: dict, path: Path) -> Path:
    """payload keys: worlds.min_I / median_I each with
    Theta_hm (L,U), Theta_exp (L,U), theta2_true, spill_true,
    foil1_ci (lo,hi), foil2_ci (lo,hi), foil1_label (legend text).
    """
    import matplotlib.pyplot as plt

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    fig, axes = plt.subplots(2, 2, figsize=(9.5, 5.5), sharex="col")
    row_names = (("min_I", "min-I point"), ("median_I", "median-I point"))
    for r, (key, title) in enumerate(row_names):
        w = payload["worlds"][key]
        # left: policy
        ax = axes[r, 0]
        L, U = w["Theta_hm"]
        ax.axvspan(L, U, color="#4C78A8", alpha=0.25, label=r"$\Theta_{\mathrm{hm}}$")
        _interval_h(ax, 1, *w["foil1_ci"], "#F58518", w.get("foil1_label", "Foil 1"))
        ax.plot(w["theta2_true"], 0, "k*", markersize=10, label=r"$\theta_2(c_0)$")
        if w.get("theta2_star") is not None:
            ax.plot(w["theta2_star"], 0.35, "k^", markersize=8, label=r"$\theta_2(c^\star)$")
        ax.set_yticks([])
        ax.set_ylim(-0.4, 1.5)
        ax.set_title(f"{title}  —  policy contrast")
        ax.set_xlabel(r"$\theta_2$")
        if r == 0:
            ax.legend(loc="upper right", fontsize=8, frameon=False)

        # right: spillover
        ax = axes[r, 1]
        L, U = w["Theta_exp"]
        ax.axvspan(L, U, color="#72B7B2", alpha=0.25, label=r"$\Theta_{\mathrm{exp}}$")
        _interval_h(ax, 1, *w["foil2_ci"], "#E45756", "Foil 2: Hájek")
        ax.plot(w["spill_true"], 0, "k*", markersize=10, label=r"$\delta_{\mathrm{spill}}(c_0)$")
        if w.get("spill_star") is not None:
            ax.plot(w["spill_star"], 0.35, "k^", markersize=8, label=r"$\delta_{\mathrm{spill}}(c^\star)$")
        ax.set_yticks([])
        ax.set_ylim(-0.4, 1.5)
        ax.set_title(f"{title}  —  spillover")
        ax.set_xlabel(r"$\delta_{\mathrm{spill}}$")
        if r == 0:
            ax.legend(loc="upper right", fontsize=8, frameon=False)

    fig.suptitle("Images over NROY (bands) vs one-world foil intervals (lines), at two diagnostic points", fontsize=10.5)
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)
    return path


def draw_empty(info: dict, path: Path) -> Path:
    """F-EMPTY report: z vs closest M, and I against τ. Not an overlay of Θ."""
    import matplotlib.pyplot as plt

    path = Path(path)
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
    ax.set_yscale("log")
    ax.set_ylabel("implausibility I(c) (log scale)")
    ax.set_title("wave-1 I(c) vs frozen τ  (F-EMPTY)")
    ax.legend(frameon=False, fontsize=8)

    fig.suptitle("F-EMPTY: every point in C is ruled out  (τ not loosened)", fontsize=11)
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)
    return path


def draw_waves(wave_kept, wave_I_stats, tau: float, label: str, path: Path) -> Path:
    """History-matching waves: points kept per wave, and min/median I against tau."""
    import matplotlib.pyplot as plt

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    waves = np.arange(1, len(wave_kept) + 1)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
    bars = ax1.bar(waves, wave_kept, width=0.55, color="#4C78A8")
    for b, v in zip(bars, wave_kept):
        ax1.annotate(str(v), (b.get_x() + b.get_width() / 2, v), xytext=(0, 3),
                     textcoords="offset points", ha="center", va="bottom", fontsize=9)
    ax1.set_xticks(waves)
    ax1.set_xlabel("wave")
    ax1.set_ylabel(f"points kept (of {config.WAVE_POINTS})")
    ax1.set_title(f"{label}: kept per wave (|NROY| = {sum(wave_kept)})")

    mins = [s["min"] for s in wave_I_stats]
    meds = [s["median"] for s in wave_I_stats]
    ax2.axhline(tau, color="#54A24B", lw=2.5, label=fr"$\tau = {tau:.2f}$")
    ax2.plot(waves, mins, "-o", color="#4C78A8", label="min $I$")
    ax2.plot(waves, meds, "-s", color="#F58518", label="median $I$")
    ax2.set_yscale("log")
    ax2.set_xticks(waves)
    ax2.set_xlabel("wave")
    ax2.set_ylabel("$I(c)$ (log scale)")
    ax2.set_title(r"implausibility vs $\tau$ (max $I$ not drawn)")
    ax2.legend(frameon=False, fontsize=9)
    for ax in (ax1, ax2):
        ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)
    return path


def draw_image_points(points: list, Theta_hm, Theta_exp, path: Path) -> Path:
    """The sampled NROY points behind each image, with 95% Monte Carlo error bars.

    x = I(c), y = the estimand at c. The image is [min y, max y]; the error bars
    show how much of each endpoint is Monte Carlo noise.
    """
    import matplotlib.pyplot as plt

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    I = np.array([p["I"] for p in points])
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    for ax, key, se_key, img, color, name in (
        (axes[0], "theta2", "se_theta2", Theta_hm, "#4C78A8", r"$\theta_2(c)$"),
        (axes[1], "delta_spill", "se_spill", Theta_exp, "#72B7B2", r"$\delta_{\mathrm{spill}}(c)$"),
    ):
        y = np.array([p[key] for p in points])
        se = np.array([p[se_key] for p in points])
        ax.errorbar(I, y, yerr=1.96 * se, fmt="o", ms=2.5, color=color,
                    ecolor=color, elinewidth=0.6, alpha=0.6)
        for v in img:
            ax.axhline(v, color="k", lw=0.8, ls="--")
        ax.set_xlabel("$I(c)$")
        ax.set_ylabel(name)
        tiny = bool(np.nanmax(1.96 * se) < 0.005 * (np.nanmax(y) - np.nanmin(y)))
        note = "; bars smaller than the dots" if tiny else ""
        ax.set_title(f"{name}, {len(points)} NROY points (±1.96 MC SE{note})", fontsize=10)
        ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)
    return path

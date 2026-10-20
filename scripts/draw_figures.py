#!/usr/bin/env python
"""Redraw every figure of a finished run from its saved results (no simulation).

Usage:  python scripts/draw_figures.py [planted|worldbank]     (default: planted)
Reads results/S/poc_results.json (+ image_points.json); writes figures/S/*.png.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from poc_abm import config  # noqa: E402
from poc_abm.pipeline import draw_figures  # noqa: E402


def main():
    source = sys.argv[1] if len(sys.argv) > 1 else "planted"
    res = config.RESULTS_DIR / source
    payload = json.loads((res / "poc_results.json").read_text())
    pts_path = res / "image_points.json"
    points = json.loads(pts_path.read_text()) if pts_path.exists() else None
    for f in draw_figures(payload, points, config.FIGURES_DIR / source):
        print(f"wrote {f}")


if __name__ == "__main__":
    main()

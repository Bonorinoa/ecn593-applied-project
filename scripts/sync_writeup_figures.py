"""Copy the figures that the paper uses into writeup/figures/.

writeup/ is a self-contained Overleaf project: main.tex, cover.tex, latexmkrc,
the figures and main.pdf sit in one folder. The figures in figures/ are the
ones the code draws. This script copies them, byte for byte, into writeup/.
tests/test_writeup_figures.py fails if the two copies differ.

Usage: python scripts/sync_writeup_figures.py
"""
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

# The paper's figure name -> the figure that the code draws.
WRITEUP_FIGURES = {
    "waves.png": "figures/planted/waves.png",
    "image_points.png": "figures/planted/image_points.png",
    "overlay.png": "figures/planted/overlay.png",
}
THESIS_FIGURES = {**WRITEUP_FIGURES, "tradeoff.png": "figures/planted/tradeoff.png"}


def main():
    writeup_out = REPO / "writeup" / "figures"
    writeup_out.mkdir(parents=True, exist_ok=True)
    for name, source in WRITEUP_FIGURES.items():
        shutil.copyfile(REPO / source, writeup_out / name)
        print(f"{source} -> writeup/figures/{name}")
    thesis_out = REPO / "thesis" / "figures"
    thesis_out.mkdir(parents=True, exist_ok=True)
    for name, source in THESIS_FIGURES.items():
        shutil.copyfile(REPO / source, thesis_out / name)
        print(f"{source} -> thesis/figures/{name}")


if __name__ == "__main__":
    main()

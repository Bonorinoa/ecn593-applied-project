"""The paper's figures must be the code's figures.

writeup/ is a self-contained Overleaf project, so it holds copies of the
figures. These tests fail if a copy differs from the figure the code drew, or
if main.tex uses a figure that the sync script does not copy.
Fix: python scripts/sync_writeup_figures.py
"""
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
from sync_writeup_figures import WRITEUP_FIGURES  # noqa: E402


def test_writeup_figures_are_byte_identical_to_code_figures():
    for name, source in WRITEUP_FIGURES.items():
        copy = REPO / "writeup" / "figures" / name
        assert copy.exists(), f"missing writeup/figures/{name}"
        assert copy.read_bytes() == (REPO / source).read_bytes(), f"writeup/figures/{name} differs from {source}"


def test_main_tex_uses_only_synced_figures():
    tex = (REPO / "writeup" / "main.tex").read_text() + (REPO / "writeup" / "cover.tex").read_text()
    used = set(re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", tex))
    assert used, "no figures found in main.tex"
    assert used <= set(WRITEUP_FIGURES), f"not synced: {sorted(used - set(WRITEUP_FIGURES))}"

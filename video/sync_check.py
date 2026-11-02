"""Check that sentence cues land on the spoken sentences (see timing.py for the method).

For every sentence start in every scene, compare the cue time with the nearest real sentence
start in the wav (the end of a pause of at least 0.18 s): first for a plain linear map, then for
the anchored map that scenes.py uses.
    env -u PYTHONPATH uv run --project video python video/sync_check.py
"""
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from timing import anchors, char_time, pause_ends, sentence_starts  # noqa: E402

DUR = json.loads((HERE / "build/audio/durations.json").read_text())["seconds"]

worst_lin = worst_anc = 0.0
for key, d in DUR.items():
    text = (HERE / "narration" / f"{key}.txt").read_text().strip()
    wav = HERE / "build/audio" / f"{key}.wav"
    real = pause_ends(wav)
    pts = anchors(text, d, wav)
    starts = sentence_starts(text)
    lin = np.array([np.min(np.abs(real - d * c / len(text))) for c in starts])
    anc = np.array([np.min(np.abs(real - char_time(pts, c))) for c in starts])
    snapped = int(np.sum(anc < 1e-9))
    worst_lin, worst_anc = max(worst_lin, lin.max()), max(worst_anc, anc.max())
    print(f"{key}: {len(starts)} sentences, {snapped} snapped to a pause | linear max {lin.max():.2f} s"
          f" | anchored median {np.median(anc):.2f} s, max {anc.max():.2f} s")
print(f"worst: linear {worst_lin:.2f} s, anchored {worst_anc:.2f} s")

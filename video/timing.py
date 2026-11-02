"""Narration timing: map a character position in a scene's narration to seconds in its wav.

Speech rate is close to constant per character, but not exactly: a plain linear map
(t = D * chars_before / chars_total) drifts by up to about 2 s within a scene. So the map is
anchored at sentence starts: walking through the sentences in order, each start is predicted
from the previous anchor at the scene's mean rate and snapped to the nearest real pause end in
the wav (a pause of at least 0.18 s) if one lies within 0.8 s; a sentence with no such pause is
not an anchor. Between anchors the map is linear.
"""
from __future__ import annotations

import re
import wave
from pathlib import Path

import numpy as np

FRAME, MIN_PAUSE, SNAP = 0.02, 0.18, 0.8


def pause_ends(path: Path) -> np.ndarray:
    with wave.open(str(path)) as w:
        rate = w.getframerate()
        x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(float)
    n = int(rate * FRAME)
    rms = np.sqrt(np.mean(x[: len(x) // n * n].reshape(-1, n) ** 2, axis=1))
    quiet = rms < 0.03 * rms.max()
    ends, run = [], 0
    for i, q in enumerate(quiet):
        if q:
            run += 1
        else:
            if run * FRAME >= MIN_PAUSE:
                ends.append(i * FRAME)
            run = 0
    return np.array(ends)


def sentence_starts(text: str) -> list[int]:
    return [m.end() for m in re.finditer(r"[.?!:]\s+", text)]


def anchors(text: str, seconds: float, wav: Path):
    """(char index, seconds) pairs: start, every snapped sentence start, end."""
    rate = seconds / len(text)
    real = pause_ends(wav)
    pts = [(0, 0.0)]
    for c in sentence_starts(text):
        c0, t0 = pts[-1]
        pred = t0 + (c - c0) * rate
        cand = real[real > t0 + 0.05]
        if len(cand):
            best = cand[np.argmin(np.abs(cand - pred))]
            if abs(best - pred) <= SNAP:
                pts.append((c, float(best)))
    pts.append((len(text), seconds))
    return pts


def char_time(pts, i: int) -> float:
    cs, ts = zip(*pts)
    return float(np.interp(i, cs, ts))

"""Extract stills from rendered scene videos to video/shots/ for checking layout by eye.

    env -u PYTHONPATH uv run --project video python video/stills.py PREFIX MP4 FRACTION [FRACTION ...]
e.g. pilot_s01 build/media/videos/scenes/480p15/S01Question.mp4 0.3 0.6 0.9
"""
import sys
from pathlib import Path

import av

HERE = Path(__file__).resolve().parent


def stills(prefix, mp4, fracs):
    with av.open(str(mp4)) as c:
        s = c.streams.video[0]
        rate = float(s.average_rate)
        frames = [f for f in c.decode(s)]
    out = []
    for i, fr in enumerate(fracs):
        img = frames[min(int(fr * len(frames)), len(frames) - 1)].to_image()
        path = HERE / "shots" / f"{prefix}_{'abcdefgh'[i]}.png"
        path.parent.mkdir(exist_ok=True)
        img.save(path)
        out.append(path)
        print(path, f"t={fr * len(frames) / rate:.1f}s")
    return out


if __name__ == "__main__":
    stills(sys.argv[1], sys.argv[2], [float(x) for x in sys.argv[3:]])

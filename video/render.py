"""Render the lecture: every scene at 1080p30, the narration laid under it, one mp4 + chapters.

Run from the repo root:
    env -u PYTHONPATH uv run --project video python video/render.py            # full, 1080p30
    env -u PYTHONPATH uv run --project video python video/render.py --pilot S01Question S02Config

Steps
  1. manim renders each scene of scenes.SCENES to build/media/.../<Scene>.mp4 (silent).
  2. Each scene's narration wav is padded with silence to the exact length of its picture
     (the picture is always at least the narration plus a short tail: never cut the audio;
     the script stops if a picture is shorter than its narration).
  3. The scene videos are concatenated (stream copy) and muxed once with the joined narration
     (AAC). Muxing once, instead of per scene, avoids an AAC priming gap at every scene joint.
  4. Writes build/ecn593-architecture.mp4 (with chapter metadata) and build/chapters.txt.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import wave
from pathlib import Path

import av

HERE = Path(__file__).resolve().parent
BUILD = HERE / "build"
AUDIO = BUILD / "audio"
MEDIA = BUILD / "media"
FFMPEG = "/Users/bonorinoa/.hermes/tools/ffmpeg-9.0.1-darwin-arm64/ffmpeg"
OUT = BUILD / "ecn593-architecture.mp4"

sys.path.insert(0, str(HERE))
import scenes  # noqa: E402

TITLES = {
    "s01": "The policy question", "s02": "The world and the design",
    "s03": "The kernel and the three arms", "s04": "The estimand theta two",
    "s05": "The targets z", "s06": "History matching", "s07": "The images",
    "s08": "The analysts and the A2 ladder", "s09": "Judging an interval",
    "s10": "One-command replication",
}


def run(cmd):
    print("+", " ".join(str(c) for c in cmd), flush=True)
    subprocess.run([str(c) for c in cmd], check=True)


def render_scene(name, quality):
    flags = ["-qh", "--frame_rate", "30", "-r", "1920,1080"] if quality == "full" else ["-ql"]
    run([sys.executable, "-m", "manim", "render", *flags, "--media_dir", MEDIA,
         "--disable_caching", HERE / "scenes.py", name])
    folder = "1080p30" if quality == "full" else "480p15"
    return MEDIA / "videos" / "scenes" / folder / f"{name}.mp4"


def video_seconds(path):
    with av.open(str(path)) as c:
        s = c.streams.video[0]
        return float(s.frames * 1.0 / s.average_rate) if s.frames else float(c.duration / 1e6)


def padded_wav(key, seconds, out):
    with wave.open(str(AUDIO / f"{key}.wav")) as w:
        rate, ch, sw = w.getframerate(), w.getnchannels(), w.getsampwidth()
        frames = w.readframes(w.getnframes())
        n = w.getnframes()
    total = round(seconds * rate)
    if total < n:
        sys.exit(f"{key}: picture {seconds:.3f}s is shorter than its narration {n / rate:.3f}s")
    return rate, ch, sw, frames + b"\x00" * ((total - n) * ch * sw)


def hms(t):
    t = int(round(t))
    return f"{t // 3600:d}:{t % 3600 // 60:02d}:{t % 60:02d}" if t >= 3600 else f"{t // 60:02d}:{t % 60:02d}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot", nargs="*", help="render only these scenes at low quality; no mux")
    args = ap.parse_args()

    if args.pilot:
        for name in args.pilot:
            print(render_scene(name, "low"))
        return

    parts = []
    for cls in scenes.SCENES:
        mp4 = render_scene(cls.__name__, "full")
        parts.append((cls.key, mp4, video_seconds(mp4)))

    # joined narration, each scene padded to its picture length
    pcm, fmt, starts, t = [], None, [], 0.0
    for key, _, secs in parts:
        rate, ch, sw, data = padded_wav(key, secs, None)
        fmt = (rate, ch, sw)
        pcm.append(data)
        starts.append(t)
        t += secs
    narration = BUILD / "narration_full.wav"
    with wave.open(str(narration), "wb") as w:
        w.setframerate(fmt[0]); w.setnchannels(fmt[1]); w.setsampwidth(fmt[2])
        w.writeframes(b"".join(pcm))

    listing = BUILD / "concat.txt"
    listing.write_text("".join(f"file '{mp4}'\n" for _, mp4, _ in parts))

    meta = [";FFMETADATA1"]
    for (key, _, secs), st in zip(parts, starts):
        meta += ["[CHAPTER]", "TIMEBASE=1/1000", f"START={int(st * 1000)}",
                 f"END={int((st + secs) * 1000)}", f"title={int(key[1:])}. {TITLES[key]}"]
    chap_meta = BUILD / "chapters.ffmeta"
    chap_meta.write_text("\n".join(meta) + "\n")

    run([FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", listing, "-i", narration,
         "-i", chap_meta, "-map", "0:v", "-map", "1:a", "-map_metadata", "2", "-map_chapters", "2",
         "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", OUT])

    lines = [f"{hms(st)} {int(k[1:])}. {TITLES[k]}" for (k, _, _), st in zip(parts, starts)]
    (BUILD / "chapters.txt").write_text("\n".join(lines) + "\n")
    summary = {"mp4": str(OUT), "seconds": round(t, 2), "bytes": OUT.stat().st_size,
               "scenes": {k: round(s, 3) for k, _, s in parts},
               "chapters": lines}
    (BUILD / "render_summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

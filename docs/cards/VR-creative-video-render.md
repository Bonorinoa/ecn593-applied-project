# VR (creative, Claude): lecture video, part 2: Manim scenes and the render

Read `docs/cards/common_rules.md` (below), `video/script.md`, `video/storyboard.md` and
`reviews/video-script.md` (VV's verdict). **First apply every replacement sentence VV lists** to
`video/script.md` and `video/narration/*.txt`, regenerate the affected scenes' audio with the same
voice and the same Phonon command as VS, and update `durations.json`.

**Environment:** a uv project in `video/` (`video/pyproject.toml`, `requires-python = ">=3.14"`,
`uv add --exclude-newer "7 days" manim`, commit `uv.lock`; run with
`env -u PYTHONPATH uv run --project video manim ...`). `pkg-config`, `cairo` and `pango` are
installed (Homebrew); a probe on 2026-11-01 rendered a Manim 0.22.0 scene this way. `dvisvgm` is not
installed: no `Tex`/`MathTex`. For muxing, use ffmpeg at
`/Users/bonorinoa/.hermes/tools/ffmpeg-9.0.1-darwin-arm64/ffmpeg` or PyAV.

**Acceptance:**
1. `video/scenes.py`: one Manim `Scene` per script scene, each timed to its narration duration
   from `durations.json` (`self.wait` pads; never cut the audio). Kaffeehaus palette as the
   storyboard picked. Readable text: nothing under about 28 px at 1080p; at most about 12 words on
   screen at once.
2. `video/render.py` (or a short shell script): renders all scenes at 1080p30, muxes each scene
   with its wav, concatenates, and writes `video/build/ecn593-architecture.mp4` plus chapter
   markers (`video/build/chapters.txt`, one line per scene with its start time).
3. Pilot first: render scenes 1–2 at low quality, extract 3 stills per scene to
   `video/shots/` (tracked), look at them, and fix layout before the full render.
4. Full render. Then extract one still per scene to `video/shots/` and check each by eye: no
   overlapping text, nothing off-frame, audio and visuals in step.
5. Commit `video/` sources, `pyproject.toml`, `uv.lock`, `video/shots/*.png` and a
   `video/README.md` (how to re-render; the voice and its licence: Phonon 31m is Apache-2.0).
   Not `video/build/`. Attach the final mp4 to this card
   (`hermes kanban --board ecn593 attach <this card id> video/build/ecn593-architecture.mp4`).

**Artifact:** the commit sha, the mp4 path, its duration and size, the chapter list, and anything
from VV you did not apply (with the reason). Progress file: `docs/cards/progress/VR.md`.

**Fence:** write only `video/` and your progress file.

# video/: the ECN 593 architecture lecture

A narrated Manim lecture (about ten minutes, ten scenes) that walks the project top-down: the
policy question, the config, the kernel, the estimand, the targets, history matching, the images,
the analysts, interval geometry, and one-command replication. Architecture only: **no result
numbers** are spoken or shown. Every narration claim is sourced in `script.md`.

| File | What it is |
|---|---|
| `script.md` | the lecture: narration (exact TTS input), visual notes, a source for every claim |
| `narration/sNN.txt` | the narration of each scene, byte-identical to the script's blocks |
| `storyboard.md` | palette, type, timing rules and per-scene beats |
| `scenes.py` | one Manim `Scene` per script scene (`S01Question` … `S10Replicate`) |
| `render.py` | renders all scenes at 1080p30, lays the narration under them, writes the mp4 + chapters |
| `stills.py` | pulls stills from a rendered scene into `shots/` |
| `timing.py`, `sync_check.py` | narration time map for the cues, and its check against the wav pauses |
| `shots/` | layout checks: `pilot_*` (low-quality pilot, 3 per scene for scenes 1–2), `final_sNN.png` (one per scene from the 1080p render) |
| `palette_still.py`, `palette-choice.png` | the cream vs deep-ink comparison behind the palette pick |
| `pyproject.toml`, `uv.lock` | the uv project (Manim 0.22.0, PyAV) |

Not tracked: `build/` (audio, renders, the final mp4) and `media/`.

## Re-render

From the repo root. `cairo`, `pango` and `pkg-config` must be installed (Homebrew). No LaTeX is
needed: all text is Manim `Text` (Helvetica Neue).

```sh
# 1. narration audio (only if build/audio/ is missing or a narration file changed)
for s in s01 s02 s03 s04 s05 s06 s07 s08 s09 s10; do
  ~/Hermes/Projects/strudel-kaffeehaus/voice/tts --voice Hadley \
    --text-file video/narration/$s.txt --out video/build/audio/$s.wav
done
#    then rewrite video/build/audio/durations.json (key "seconds": sNN -> wav frames / rate)

# 2. pilot one scene at low quality (480p15), and pull stills to check the layout
env -u PYTHONPATH uv run --project video python video/render.py --pilot S01Question
env -u PYTHONPATH uv run --project video python video/stills.py pilot_s01 \
  video/build/media/videos/scenes/480p15/S01Question.mp4 0.3 0.6 0.9

# 3. full render: all scenes at 1080p30, narration muxed, chapters
env -u PYTHONPATH uv run --project video python video/render.py
```

Outputs: `video/build/ecn593-architecture.mp4` (H.264 + AAC, chapter metadata embedded),
`video/build/chapters.txt` (one line per scene with its start time) and
`video/build/render_summary.json`.

How the timing works: `scenes.py` reads `build/audio/durations.json`. Each scene lasts its
narration plus a 0.4 s tail; beats are cued to sentences of the narration (`self.cue(phrase)`
waits until the phrase is spoken, by `timing.py`: a character-to-seconds map anchored at the
real pauses between sentences in the wav), and `self.wait` pads. `sync_check.py` reports how
well the cues land (linear map vs anchored map).
`render.py` pads each wav with silence to its scene's exact picture length and stops if any
picture is shorter than its narration, so the audio is never cut. It muxes the joined narration
once over the concatenated scenes (rather than per scene) to avoid an AAC gap at every joint.

Editing rule: change the narration in `script.md` and `narration/sNN.txt` together (they must
stay byte-identical), re-voice that scene, update `durations.json`, re-render. Cue phrases in
`scenes.py` must still occur in the narration (a missing phrase stops the render).

## Voice and licence

Narration: **Gradium Phonon 31m** (`hf://gradium/phonon-31m-en`, q8, run locally through
`ptts` by `~/Hermes/Projects/strudel-kaffeehaus/voice/tts`), voice **Hadley**. The Phonon 31m
model is released under the **Apache-2.0** licence. Why Hadley: storyboard section 0.5.

Scenes 1, 2, 4, 7, 8 and 10 were re-voiced after the script review (`reviews/video-script.md`)
replaced nine sentences; scenes 3, 5, 6 and 9 keep the original take. Same voice, same command.

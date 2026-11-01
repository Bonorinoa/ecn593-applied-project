# VS (creative, Claude): lecture video, part 1: script, storyboard and narration

Read `docs/cards/common_rules.md` (below). The owner (Augusto) asked for a lecture video that walks
him through the project's main architecture, top-down: start from the general idea and go deeper.
It is study material for him first. Visuals: Manim. Voice: Gradium Phonon 31m, run locally.

**Sources of truth:** the code (`src/poc_abm/`, `config/`, `scripts/`), `SPECIFICATION.md`,
`docs/preregistration-v2.md` (with A1 and A2), the spine. Never `study/lectures-pre-wave/` (stale).
Describe architecture and design, not results: no result numbers at all (configuration constants
such as N = 800 or k = 80 are fine, with their source).

**Acceptance:**
1. `video/script.md`: 8–10 minutes in about 10 scenes, top-down:
   (1) the policy question and why one calibrated point can mislead; (2) the world vs the design
   (`config/world.toml`, `config/design.toml`); (3) the kernel M(c) and the three arms; (4) the
   estimand theta2 and why a pilot never realizes it; (5) the targets z; (6) history matching:
   I(c), delta, tau, waves, NROY; (7) the images Theta_hm and Theta_exp; (8) the analysts: Foil 1,
   Foil 2, A1, A2 (the ladder); (9) interval geometry and the two layers of evaluation;
   (10) one-command replication and where everything lives.
   Each scene: the narration text (plain spoken English, short sentences), a visual description,
   and a **source line for every factual claim** (file:line or doc section), so a verifier can
   check it. Keep the narration and the sources in separate columns or blocks.
2. `video/storyboard.md`: per scene, the Manim objects and animations, colours from the Kaffeehaus
   palette (oxblood, sand, cream; a cream or deep-ink background, your call; show both in a still
   and pick), sans labels. No LaTeX-rendered math: `dvisvgm` is not installed, so use Manim `Text`
   / `MarkupText` with Unicode (θ, Θ, δ, τ, ≤).
3. Narration audio: the Phonon wrapper (already installed; do not modify that project):
   `~/Hermes/Projects/strudel-kaffeehaus/voice/tts --text-file <scene.txt> --out <scene.wav> --voice <V>`.
   First synthesize one sentence in voices Hadley, Everly and Spencer, pick one and say why. Then
   one wav per scene into `video/build/audio/` (gitignored), and `video/build/audio/durations.json`
   (seconds per scene; measure with Python `wave`, not ffprobe, which is not installed).
   Spell out symbols in the narration text ("theta two", "N R O Y" if it reads better), so the TTS
   says them right; listen-check by transcribing nothing, but keep sentences short.
4. Commit `video/script.md`, `video/storyboard.md`, `video/narration/*.txt` (the exact TTS input
   per scene). Not the audio (`/video/build/`, `/video/media/` and `/video/.venv/` are already
   gitignored; do not edit `.gitignore`).

**Artifact:** the commit sha, the chosen voice, total narration seconds, and the list of claims
you were least sure of. Progress file: `docs/cards/progress/VS.md`.

**Fence:** write only `video/` and your progress file. Do not modify
the strudel-kaffeehaus project or any repo code.

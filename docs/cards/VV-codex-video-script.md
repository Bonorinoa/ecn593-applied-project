# VV (verifier, Codex gpt-5.6-sol, read-only): the lecture video script

Producer: VS (creative, Claude). You are an independent family. Read `docs/cards/common_rules.md`
(below), the VS card, `video/script.md` and `video/narration/*.txt`.

**Write one file:** `reviews/video-script.md`, starting with a verdict line (PASS /
PASS-WITH-WORDING / BLOCK). Commit only that file.

**Check:**
1. Every factual claim in the narration against its cited source and against the code itself
   (file:line). The code wins over any doc. List each false, stale or overstated sentence with an
   exact replacement sentence the narrator can say.
2. No result numbers (configuration constants with a source are fine).
3. The narration files say the same thing as `script.md`.
4. Terms: "image", "NROY", "F-OVERCONF", "coverage" vs "containment" used as the project's
   `GLOSSARY.md` (`~/Hermes/Projects/ecn593/GLOSSARY.md`) defines them; the image is never called an
   identified set; A1 and A2 described as amendment A2 defines them.

Budget: about 40 tool calls. Do not edit any other file.

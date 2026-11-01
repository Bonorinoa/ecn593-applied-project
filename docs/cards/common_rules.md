# Common rules for every card on board ecn593 (v2 sprint, A1, and the A2 sprint)

- **Root:** repo `/Users/bonorinoa/Desktop/Github_Repositories/ecn593-applied-project`, branch `main`.
  Spine (read first): `/Users/bonorinoa/Hermes/Projects/ecn593/STATUS.md`. The design is
  `docs/preregistration-v2.md`, including amendments A1 and A2 at its bottom. It is frozen: if the
  code and it disagree, the code is wrong. If the pre-registration itself looks wrong, say so in
  your report; do not change it.
- **Python:** `env -u PYTHONPATH .venv/bin/python` from the repo root (`.venv` is a symlink to
  `.venv.nosync`; never delete or rebuild it). Tests: `... -m pytest tests -q -p no:warnings`.
  No installs into `.venv`. (The video cards have their own rule for `video/`.)
- **Long commands:** never block a single terminal call for more than about 3 minutes. Run the
  pipeline or `replicate.py` with the terminal tool's background mode and poll it.
  `run_poc.py planted` takes about 4 min; the Foil 2 check about 4 min; `replicate.py` about 30 min.
- **Shared checkout (A2 sprint):** several cards work in this checkout at once, each in its own
  folders (engineer: `src/ scripts/ tests/ results/ figures/ writeup/numbers.tex README.md
  SPECIFICATION.md`; template and paper: `thesis/`; video: `video/`). Write only your own paths.
  Commit only your own files, by explicit path (`git commit -- <paths>`); never `git add -A`,
  `git add .`, `stash`, `reset` or `checkout` of others' files. On an `index.lock` error, wait 15 s
  and retry once. Push to `origin main` (on a non-fast-forward: `git pull --rebase`, then push).
  Put the sha from `git log --oneline -1` in your handoff; never a remembered or guessed sha.
- **Progress:** after each numbered step that passes, append one line to your card's progress
  file under `docs/cards/progress/` (create it), so a retry resumes instead of redoing.
- **Truth:** numbers come only from `results/*.json` or `writeup/numbers.tex` (and its copy in
  `thesis/`). Never type a result number into prose, code, slides or narration.
- **Premise check:** if any instruction looks wrong, say so in the handoff with file:line evidence.

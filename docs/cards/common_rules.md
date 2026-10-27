# Common rules for every v2 sprint card (board ecn593)

- **Root:** repo `/Users/bonorinoa/Desktop/Github_Repositories/ecn593-applied-project`, branch `main`.
  Spine (read first): `/Users/bonorinoa/Hermes/Projects/ecn593/STATUS.md`. The design is
  `docs/preregistration-v2.md`. It is frozen: if the code and it disagree, the code is wrong.
  If the pre-registration itself looks wrong, say so in your report; do not change it.
- **Python:** `env -u PYTHONPATH .venv/bin/python` from the repo root (`.venv` is a symlink to
  `.venv.nosync`; never delete or rebuild it). Tests: `... -m pytest tests -q -p no:warnings`.
  No installs.
- **Long commands:** never block a single terminal call for more than about 3 minutes. Run the
  pipeline or `replicate.py` with the terminal tool's background mode and poll it.
  `run_poc.py planted` takes about 4 min; the Foil 2 check about 4 min; `replicate.py` about 8 min.
- **Git:** commit only the files your card owns, by explicit path (`git commit -- <paths>`); never
  `git add -A`, `stash`, `reset` or `checkout` of others' files. Push to `origin main`. Put the
  sha from `git log --oneline -1` in your handoff; never a remembered or guessed sha.
- **Progress:** after each numbered step that passes, append one line to your card's progress
  file under `docs/cards/progress/` (create it), so a retry resumes instead of redoing.
- **Truth:** numbers come only from `results/*.json` or `writeup/numbers.tex`. Never type a result
  number into prose or code.
- **Premise check:** if any instruction looks wrong, say so in the handoff with file:line evidence.

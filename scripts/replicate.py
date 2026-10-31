"""Replicate every result and the paper with one command.

Usage, from the repo root (after the one-time setup in README.md):
    .venv/bin/python scripts/replicate.py           # full: see README for the measured time
    .venv/bin/python scripts/replicate.py --quick   # skips the Foil 2 check and the delta menu

Steps, in order. The script stops at the first step that fails.
  1. tests                 pytest tests
  2. z check               scripts/plant_z.py         (data/planted.json regenerates byte for byte)
  3. planted run           scripts/run_poc.py planted
  4. Foil 2 check          scripts/check_foil2_coverage.py   (skipped with --quick)
  5. delta menu            scripts/delta_menu.py      (amendment A1; skipped with --quick)
  6. paper figures         scripts/sync_writeup_figures.py
  7. paper numbers         scripts/write_numbers.py   (writes writeup/numbers.tex)
  8. paper PDF             latexmk in writeup/        (skipped if latexmk is not installed)
  9. report                each result file compared with the committed one (git HEAD)

The runs overwrite results/, figures/, locks/ and writeup/. Git keeps the
committed versions: `git diff` shows any change, `git checkout .` restores them.
"""
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable
RESULT_FILES = [
    "results/planted/poc_results.json",
    "results/planted/image_points.json",
    "results/checks/foil2_coverage.json",
    "results/sensitivity/delta_menu.json",
]
RUN_STAMPS = {"ran_at", "git_commit"}   # fields that differ on every run by design


def step(n, name, cmd, cwd=ROOT, live=True):
    """Run one step. Its output streams live (unless live=False), each line prefixed with the seconds
    since the step started; the full text is kept and shown again on failure."""
    shown = " ".join("python" if c == PY else str(c) for c in cmd)
    print(f"[{n}/9] {name:<16} {shown}", flush=True)
    t0 = time.time()
    env = dict(os.environ, PYTHONUNBUFFERED="1")   # children print as they go, not at exit
    proc = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, env=env)
    assert proc.stdout is not None
    out = []
    for line in proc.stdout:
        out.append(line)
        if live and line.strip():
            print(f"      {time.time() - t0:4.0f}s | {line.rstrip()[:110]}", flush=True)
    proc.wait()
    lines = [l for l in "".join(out).strip().splitlines() if l.strip() not in "{}[]"]
    last = lines[-1] if lines else ""
    print(f"      {'ok' if proc.returncode == 0 else 'FAILED'} in {time.time() - t0:.0f} s   {last[:100]}", flush=True)
    if proc.returncode != 0:
        print("".join(out)[-6000:])
        sys.exit(f"stopped at step {n} ({name})")


def strip_stamps(obj):
    if isinstance(obj, dict):
        return {k: strip_stamps(v) for k, v in obj.items() if k not in RUN_STAMPS}
    if isinstance(obj, list):
        return [strip_stamps(v) for v in obj]
    return obj


def report(quick):
    print("[9/9] report           each result file vs the committed version (ignoring ran_at, git_commit)")
    all_same = True
    for path in RESULT_FILES:
        committed = subprocess.run(["git", "show", f"HEAD:{path}"], cwd=ROOT, capture_output=True, text=True)
        if committed.returncode != 0:
            print(f"      new         {path} (not committed yet, so not compared)")
            all_same = False
            continue
        same = strip_stamps(json.loads(committed.stdout)) == strip_stamps(json.loads((ROOT / path).read_text()))
        all_same &= same
        print(f"      {'identical' if same else 'CHANGED':<11} {path}")
    changed = subprocess.run(["git", "status", "--short", "--", "figures", "writeup", "locks"],
                             cwd=ROOT, capture_output=True, text=True).stdout.strip()
    print("      other changed files (figures, writeup, locks):", "none" if not changed else "")
    for line in changed.splitlines():
        print("       ", line)
    if not all_same:
        print("DIFFERENT: see the CHANGED or new files above (git diff shows the details).")
    elif quick:
        print("REPLICATED, except the Foil 2 check and the delta menu, which --quick did not rerun.")
    else:
        print("REPLICATED: every result is identical to the committed one.")


def main():
    quick = "--quick" in sys.argv
    t0 = time.time()
    step(1, "tests", [PY, "-m", "pytest", "tests", "-q", "-p", "no:warnings"])
    step(2, "z check", [PY, "scripts/plant_z.py"])
    step(3, "planted run", [PY, "scripts/run_poc.py", "planted"])
    if quick:
        print("[4/9] Foil 2 check     skipped (--quick): the committed results/checks/foil2_coverage.json is used")
        print("[5/9] delta menu       skipped (--quick): the committed results/sensitivity/delta_menu.json is used")
    else:
        step(4, "Foil 2 check", [PY, "scripts/check_foil2_coverage.py"])
        step(5, "delta menu", [PY, "scripts/delta_menu.py"])
    step(6, "paper figures", [PY, "scripts/sync_writeup_figures.py"])
    step(7, "paper numbers", [PY, "scripts/write_numbers.py"])
    if shutil.which("latexmk"):
        step(8, "paper PDF", ["latexmk", "-g", "-interaction=nonstopmode"], cwd=ROOT / "writeup", live=False)
        subprocess.run(["latexmk", "-c"], cwd=ROOT / "writeup", capture_output=True)
    else:
        print("[8/9] paper PDF        skipped: latexmk not found (or upload writeup/ to Overleaf)")
    report(quick)
    print(f"total {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()

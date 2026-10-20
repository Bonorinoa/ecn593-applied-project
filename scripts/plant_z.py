#!/usr/bin/env python
"""Write data/planted.json: z = M̂(c*) with REPS_Z reps, and its MC variances.

Usage:
  python scripts/plant_z.py           regenerate and compare with data/planted.json (no write)
  python scripts/plant_z.py --write   overwrite data/planted.json

The default only checks: data/planted.json is an input of every result, so
overwriting it is a deliberate act. Exit 1 if the regenerated file differs.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from poc_abm import config  # noqa: E402
from poc_abm.kernel import World  # noqa: E402
from poc_abm.moments import plant_and_freeze  # noqa: E402


def main():
    target = config.DATA_DIR / "planted.json"
    if "--write" in sys.argv:
        plant_and_freeze(World(), target)
        print(f"wrote {target.relative_to(ROOT)}")
        return
    tmp = config.RESULTS_DIR / "checks" / "planted_regenerated.json"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    plant_and_freeze(World(), tmp)
    same = tmp.read_bytes() == target.read_bytes()
    print(f"{target.relative_to(ROOT)} {'reproduces byte for byte' if same else 'DIFFERS'} "
          f"(regenerated copy: {tmp.relative_to(ROOT)})")
    sys.exit(0 if same else 1)


if __name__ == "__main__":
    main()

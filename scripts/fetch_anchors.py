#!/usr/bin/env python
"""Fetch the World Bank anchors and compare with data/anchors.json.

Usage:
  python scripts/fetch_anchors.py           fetch, print, compare (no write)
  python scripts/fetch_anchors.py --write   overwrite data/anchors.json

The API returns the most recent value per country, so a fetch today will not
match the stored file (fetched 2026-08). data/anchors.json is the input of the
archived World Bank run; overwrite it only on purpose.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from poc_abm import config  # noqa: E402
from poc_abm.data_worldbank import build_anchors  # noqa: E402


def main():
    anchors = build_anchors()
    print(json.dumps(anchors, indent=2))
    target = config.DATA_DIR / "anchors.json"
    if "--write" in sys.argv:
        target.write_text(json.dumps(anchors, indent=2))
        print(f"wrote {target.relative_to(ROOT)}")
        return
    stored = json.loads(target.read_text())
    print("matches data/anchors.json" if stored == anchors else
          "differs from data/anchors.json (expected: the API serves the latest values)")


if __name__ == "__main__":
    main()

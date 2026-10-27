#!/usr/bin/env python
"""Run the pipeline.  Usage:  python scripts/run_poc.py [planted]
planted (the default) is the only run.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from poc_abm.pipeline import main  # noqa: E402

if __name__ == "__main__":
    main()

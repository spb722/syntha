#!/usr/bin/env python3
"""Filter evaluation results into passed/failed."""

import sys
from pathlib import Path

# Add src to path for development use
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from syntha.evaluation.filter import main

if __name__ == "__main__":
    sys.exit(main())

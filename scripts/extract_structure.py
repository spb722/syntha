#!/usr/bin/env python3
"""Extract structured data from generated text."""

import sys
from pathlib import Path

# Add src to path for development use
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from syntha.extractor import main

if __name__ == "__main__":
    sys.exit(main())

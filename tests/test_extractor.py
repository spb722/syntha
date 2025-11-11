"""Tests for syntha.extractor module."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_extractor_imports():
    """Test that extractor module can be imported."""
    from syntha import extractor
    assert extractor is not None


# Add more tests here as needed

"""Tests for syntha.evaluation.filter module."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


def test_filter_module_exists():
    """Test that filter module exists."""
    from syntha.evaluation import filter
    assert filter is not None


# Add more tests here as needed

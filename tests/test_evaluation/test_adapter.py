"""Tests for syntha.evaluation.adapter module."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


def test_adapter_module_exists():
    """Test that adapter module exists."""
    from syntha.evaluation import adapter
    assert adapter is not None


# Add more tests here as needed

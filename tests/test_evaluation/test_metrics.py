"""Tests for syntha.evaluation.metrics module."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


def test_metrics_module_exists():
    """Test that metrics module exists."""
    from syntha.evaluation import metrics
    assert metrics is not None


# Add more tests here as needed

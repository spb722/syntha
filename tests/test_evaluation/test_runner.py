"""Tests for syntha.evaluation.runner module."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


def test_runner_module_exists():
    """Test that runner module exists."""
    from syntha.evaluation import runner
    assert runner is not None


# Add more tests here as needed

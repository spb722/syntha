"""Tests for syntha.generator module."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_generator_imports():
    """Test that generator module can be imported."""
    from syntha import generator
    assert generator is not None


# Add more tests here as needed

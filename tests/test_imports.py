"""Test script to verify all imports work correctly after migration."""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_syntha_imports():
    """Test that all syntha modules can be imported."""
    import syntha
    assert syntha.__version__ == "0.1.0"
    print(f"✓ syntha package imported (version {syntha.__version__})")


def test_generator_imports():
    """Test that generator module imports successfully."""
    from syntha import generator
    print("✓ syntha.generator imported")


def test_extractor_imports():
    """Test that extractor module imports successfully."""
    from syntha import extractor
    print("✓ syntha.extractor imported")


def test_evaluation_imports():
    """Test that evaluation submodules import successfully."""
    from syntha.evaluation import adapter
    from syntha.evaluation import metrics
    from syntha.evaluation import runner
    from syntha.evaluation import filter
    print("✓ syntha.evaluation.adapter imported")
    print("✓ syntha.evaluation.metrics imported")
    print("✓ syntha.evaluation.runner imported")
    print("✓ syntha.evaluation.filter imported")


def test_utils_imports():
    """Test that utils module imports successfully."""
    from syntha import utils
    print("✓ syntha.utils imported")


if __name__ == "__main__":
    print("Testing imports after migration...\n")

    test_syntha_imports()
    test_generator_imports()
    test_extractor_imports()
    test_evaluation_imports()
    test_utils_imports()

    print("\n✅ All import tests passed!")

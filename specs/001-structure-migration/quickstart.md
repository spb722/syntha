# Quick Start: Project Structure Migration

**Feature**: 001-structure-migration
**Date**: 2025-11-11
**Purpose**: Step-by-step guide to execute the project structure migration

## Overview

This guide provides concrete commands and procedures to migrate the syntha project from its current flat structure to the organized modular structure defined in the specification. Follow these steps in order to ensure a safe, traceable migration.

## Prerequisites

Before starting the migration:

1. **Clean Working Directory**
   ```bash
   cd /Users/sachinpb/PycharmProjects/syntha
   git status
   ```
   Ensure no uncommitted changes. Commit or stash any work in progress.

2. **Backup** (optional but recommended)
   ```bash
   cd /Users/sachinpb/PycharmProjects/syntha
   git branch backup-before-migration
   ```

3. **Verify Branch**
   ```bash
   git branch
   ```
   Ensure you're on the `001-structure-migration` branch.

4. **Python Environment**
   ```bash
   python --version  # Should show 3.12+
   pip list | grep -E '(pandas|ollama|deepeval)'
   ```
   Verify required packages are installed.

## Migration Steps

### Phase 1: Create Directory Structure

Create all required directories and initialize Python packages.

```bash
# Navigate to project root
cd /Users/sachinpb/PycharmProjects/syntha

# Create source directories
mkdir -p src/syntha/evaluation
mkdir -p src/syntha/utils

# Create supporting directories
mkdir -p tests/test_evaluation
mkdir -p scripts
mkdir -p configs
mkdir -p data
mkdir -p docs

# Create output directories (git-ignored)
mkdir -p outputs/datasets
mkdir -p outputs/structured
mkdir -p outputs/evaluations
mkdir -p outputs/filtered

# Create __init__.py files for Python packages
touch src/syntha/__init__.py
touch src/syntha/evaluation/__init__.py
touch src/syntha/utils/__init__.py
touch tests/__init__.py
touch tests/test_evaluation/__init__.py

# Verify structure
tree -L 3 -I '__pycache__|.git|.idea|.deepeval|syn|specs'
```

**Expected Output**:
```
.
├── configs
├── data
├── docs
├── outputs
│   ├── datasets
│   ├── evaluations
│   ├── filtered
│   └── structured
├── scripts
├── src
│   └── syntha
│       ├── __init__.py
│       ├── evaluation
│       │   └── __init__.py
│       └── utils
│           └── __init__.py
└── tests
    ├── __init__.py
    └── test_evaluation
        └── __init__.py
```

### Phase 2: Initialize Package Metadata

Create `__init__.py` content for version tracking:

```bash
# Add version to main package __init__.py
cat > src/syntha/__init__.py << 'EOF'
"""Syntha: Synthetic data generation and evaluation toolkit."""
__version__ = "0.1.0"
EOF

# Add docstring to evaluation __init__.py
cat > src/syntha/evaluation/__init__.py << 'EOF'
"""Evaluation module for assessing generated data quality."""
EOF

# Add docstring to utils __init__.py
cat > src/syntha/utils/__init__.py << 'EOF'
"""Utility functions for file I/O and common operations."""
EOF

# Verify
cat src/syntha/__init__.py
```

### Phase 3: Migrate Source Files

Move Python source files using `git mv` to preserve history.

```bash
# Migrate main generator and extractor
git mv synthetic_generator.py src/syntha/generator.py
git mv structured_extractor.py src/syntha/extractor.py

# Migrate evaluation files
git mv deepeval_adapter.py src/syntha/evaluation/adapter.py
git mv deepeval_metrics.py src/syntha/evaluation/metrics.py
git mv deepeval_runner.py src/syntha/evaluation/runner.py
git mv filter_eval_results.py src/syntha/evaluation/filter.py

# Verify moves
git status
ls -la src/syntha/
ls -la src/syntha/evaluation/
```

**Expected git status**:
```
renamed: synthetic_generator.py -> src/syntha/generator.py
renamed: structured_extractor.py -> src/syntha/extractor.py
renamed: deepeval_adapter.py -> src/syntha/evaluation/adapter.py
renamed: deepeval_metrics.py -> src/syntha/evaluation/metrics.py
renamed: deepeval_runner.py -> src/syntha/evaluation/runner.py
renamed: filter_eval_results.py -> src/syntha/evaluation/filter.py
```

### Phase 4: Update Import Statements

Update imports in moved files to reflect new structure.

**Check for cross-file imports**:
```bash
# Search for internal imports in evaluation files
grep -n "from deepeval_" src/syntha/evaluation/*.py
grep -n "import deepeval_" src/syntha/evaluation/*.py
```

**If any internal imports are found**, update them to use relative imports:

For example, if `runner.py` imports from `adapter.py`:
```python
# OLD (if it existed)
from deepeval_adapter import create_test_case

# NEW (relative import)
from .adapter import create_test_case
```

**Automated search and replace** (if needed):
```bash
# In evaluation module files, replace old-style imports with relative imports
cd src/syntha/evaluation/
sed -i.bak 's/from deepeval_adapter import/from .adapter import/g' *.py
sed -i.bak 's/from deepeval_metrics import/from .metrics import/g' *.py
sed -i.bak 's/import deepeval_adapter/from . import adapter/g' *.py
sed -i.bak 's/import deepeval_metrics/from . import metrics/g' *.py

# Remove backup files
rm -f *.bak
cd ../../..
```

**Verify imports** by checking syntax:
```bash
python -m py_compile src/syntha/generator.py
python -m py_compile src/syntha/extractor.py
python -m py_compile src/syntha/evaluation/adapter.py
python -m py_compile src/syntha/evaluation/metrics.py
python -m py_compile src/syntha/evaluation/runner.py
python -m py_compile src/syntha/evaluation/filter.py
```

No output = success. If errors appear, manually fix import statements.

### Phase 5: Migrate Data and Documentation Files

Move data files and documentation with consistent naming.

```bash
# Move data file
git mv kpi_profiles.csv data/kpi_profiles.csv

# Move documentation files (with rename for consistency)
git mv AGENTS.md docs/AGENTS.md
git mv "Story 1.1.md" docs/story_1.1.md
git mv "Story 1.2.md" docs/story_1.2.md

# Verify
git status
ls -la data/
ls -la docs/
```

### Phase 6: Organize Output Files

Move existing output files to new structure.

```bash
# Move dataset outputs
git mv campaign_rules_dataset.jsonl outputs/datasets/
git mv campaign_rules_dataset.jsonl.meta.json outputs/datasets/

# Move structured outputs
git mv campaign_rules_structured.jsonl outputs/structured/
git mv campaign_rules_structured.jsonl.meta.json outputs/structured/

# Move evaluation outputs
git mv campaign_rules_eval.jsonl outputs/evaluations/
git mv campaign_rules_eval.jsonl.meta.json outputs/evaluations/

# Move filtered outputs
git mv campaign_rules_passed.jsonl outputs/filtered/
git mv campaign_rules_failed.jsonl outputs/filtered/

# Verify
git status
tree outputs/
```

### Phase 7: Create CLI Scripts

Create thin wrapper scripts for command-line usage.

```bash
# Generate dataset script
cat > scripts/generate_dataset.py << 'EOF'
#!/usr/bin/env python3
"""Generate synthetic dataset from KPI profiles."""

import sys
from pathlib import Path

# Add src to path for development use
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from syntha.generator import main

if __name__ == "__main__":
    sys.exit(main())
EOF

# Extract structure script
cat > scripts/extract_structure.py << 'EOF'
#!/usr/bin/env python3
"""Extract structured data from generated text."""

import sys
from pathlib import Path

# Add src to path for development use
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from syntha.extractor import main

if __name__ == "__main__":
    sys.exit(main())
EOF

# Run evaluation script
cat > scripts/run_evaluation.py << 'EOF'
#!/usr/bin/env python3
"""Run evaluation pipeline on generated data."""

import sys
from pathlib import Path

# Add src to path for development use
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from syntha.evaluation.runner import main

if __name__ == "__main__":
    sys.exit(main())
EOF

# Filter results script
cat > scripts/filter_results.py << 'EOF'
#!/usr/bin/env python3
"""Filter evaluation results into passed/failed."""

import sys
from pathlib import Path

# Add src to path for development use
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from syntha.evaluation.filter import main

if __name__ == "__main__":
    sys.exit(main())
EOF

# Make scripts executable
chmod +x scripts/*.py

# Verify
ls -la scripts/
```

### Phase 8: Create Configuration Files

Create YAML configuration files with reasonable defaults.

```bash
# Generation config
cat > configs/generation_config.yaml << 'EOF'
# Synthetic Data Generation Configuration

model:
  name: "glm-4.6:cloud"
  host: "http://localhost:11434"
  timeout: 60

sampling:
  simple_kpis: 1
  medium_kpis: 3
  complex_kpis: 5

output:
  directory: "outputs/datasets"
  format: "jsonl"
  include_metadata: true

logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
EOF

# Extraction config
cat > configs/extraction_config.yaml << 'EOF'
# Structured Data Extraction Configuration

model:
  name: "glm-4.6:cloud"
  host: "http://localhost:11434"
  timeout: 60

extraction:
  schema_validation: true
  retry_on_failure: true
  max_retries: 3

output:
  directory: "outputs/structured"
  format: "jsonl"
  include_metadata: true

logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
EOF

# Evaluation config
cat > configs/evaluation_config.yaml << 'EOF'
# Evaluation Pipeline Configuration

metrics:
  - name: "answer_relevancy"
    threshold: 0.7
  - name: "faithfulness"
    threshold: 0.8

evaluation:
  batch_size: 10
  parallel: false

output:
  directory: "outputs/evaluations"
  format: "jsonl"
  include_metadata: true

filtering:
  passed_output: "outputs/filtered/campaign_rules_passed.jsonl"
  failed_output: "outputs/filtered/campaign_rules_failed.jsonl"

logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
EOF

# Verify YAML syntax
python -c "import yaml; [print(f'✓ {f}') for f in ['configs/generation_config.yaml', 'configs/extraction_config.yaml', 'configs/evaluation_config.yaml'] if yaml.safe_load(open(f))]"
```

### Phase 9: Create Package Configuration

Create `pyproject.toml` for Python package metadata.

```bash
cat > pyproject.toml << 'EOF'
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "syntha"
version = "0.1.0"
description = "Synthetic data generation and evaluation toolkit"
readme = "README.md"
requires-python = ">=3.12"
authors = [
    {name = "Syntha Team"}
]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.12",
]

dependencies = [
    "pandas>=2.0.0",
    "ollama>=0.1.0",
    "deepeval>=0.20.0",
    "pyyaml>=6.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "black>=23.0.0",
    "mypy>=1.0.0",
]

[project.scripts]
syntha-generate = "syntha.generator:main"
syntha-extract = "syntha.extractor:main"
syntha-evaluate = "syntha.evaluation.runner:main"
syntha-filter = "syntha.evaluation.filter:main"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]

[tool.black]
line-length = 100
target-version = ["py312"]
EOF

# Verify TOML syntax
python -c "import tomllib; print('✓ pyproject.toml is valid TOML') if tomllib.load(open('pyproject.toml', 'rb')) else None"
```

### Phase 10: Create requirements.txt

Extract dependencies to requirements.txt for compatibility.

```bash
cat > requirements.txt << 'EOF'
# Syntha Dependencies
pandas>=2.0.0
ollama>=0.1.0
deepeval>=0.20.0
pyyaml>=6.0

# Development dependencies (optional)
# Uncomment for development:
# pytest>=7.0.0
# pytest-cov>=4.0.0
# black>=23.0.0
# mypy>=1.0.0
EOF

# Verify
cat requirements.txt
```

### Phase 11: Update .gitignore

Update .gitignore to exclude outputs and Python artifacts.

```bash
# Check if .gitignore exists
if [ -f .gitignore ]; then
    echo "# Python artifacts" >> .gitignore
else
    cat > .gitignore << 'EOF'
# Python artifacts
EOF
fi

# Add patterns
cat >> .gitignore << 'EOF'
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
ENV/
env/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Generated outputs
outputs/
*.jsonl
*.jsonl.meta.json

# Exception: Keep directory structure
!outputs/.gitkeep
!outputs/*/.gitkeep

# OS files
.DS_Store
Thumbs.db
EOF

# Add .gitkeep files for empty directories
touch outputs/.gitkeep
touch outputs/datasets/.gitkeep
touch outputs/structured/.gitkeep
touch outputs/evaluations/.gitkeep
touch outputs/filtered/.gitkeep

# Verify
cat .gitignore
```

### Phase 12: Create README.md

Create comprehensive README with project overview.

```bash
cat > README.md << 'EOF'
# Syntha - Synthetic Data Generation and Evaluation Toolkit

A Python toolkit for generating synthetic data using LLMs, extracting structured information, and evaluating data quality.

## Features

- **Synthetic Data Generation**: Generate realistic synthetic data from KPI profiles using Ollama LLMs
- **Structured Extraction**: Extract structured information from generated text
- **Quality Evaluation**: Evaluate generated data using DeepEval metrics
- **Result Filtering**: Automatically filter evaluation results by pass/fail criteria

## Installation

### Prerequisites

- Python 3.12 or higher
- Ollama server running (for LLM operations)

### Install Package

```bash
# Clone repository
git clone <repository-url>
cd syntha

# Install in development mode
pip install -e .

# Or install from requirements.txt
pip install -r requirements.txt
```

## Project Structure

```
syntha/
├── src/syntha/           # Main package
│   ├── generator.py      # Synthetic data generation
│   ├── extractor.py      # Structured data extraction
│   ├── evaluation/       # Evaluation module
│   │   ├── adapter.py    # DeepEval adapter
│   │   ├── metrics.py    # Custom metrics
│   │   ├── runner.py     # Evaluation pipeline
│   │   └── filter.py     # Result filtering
│   └── utils/            # Utility functions
├── scripts/              # CLI entry points
├── configs/              # YAML configuration
├── data/                 # Input data files
├── docs/                 # Documentation
├── tests/                # Test suite
└── outputs/              # Generated outputs (git-ignored)
```

## Quick Start

### 1. Generate Synthetic Dataset

```bash
# Using CLI script
python scripts/generate_dataset.py --input data/kpi_profiles.csv --output outputs/datasets/

# Or using installed command
syntha-generate --input data/kpi_profiles.csv --output outputs/datasets/
```

### 2. Extract Structured Data

```bash
python scripts/extract_structure.py --input outputs/datasets/campaign_rules_dataset.jsonl --output outputs/structured/
```

### 3. Run Evaluation

```bash
python scripts/run_evaluation.py --input outputs/structured/campaign_rules_structured.jsonl --output outputs/evaluations/
```

### 4. Filter Results

```bash
python scripts/filter_results.py --input outputs/evaluations/campaign_rules_eval.jsonl
```

## Configuration

Configuration files are located in `configs/`:

- `generation_config.yaml` - Synthetic data generation settings
- `extraction_config.yaml` - Structured extraction settings
- `evaluation_config.yaml` - Evaluation pipeline settings

Edit these files to customize behavior without changing code.

## Development

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=syntha --cov-report=html
```

### Code Formatting

```bash
# Format code with black
black src/ tests/
```

### Type Checking

```bash
# Check types with mypy
mypy src/
```

## Documentation

- [AGENTS.md](docs/AGENTS.md) - Agent documentation
- [Story 1.1](docs/story_1.1.md) - Story 1.1 documentation
- [Story 1.2](docs/story_1.2.md) - Story 1.2 documentation

## Contributing

Contributions are welcome! Please ensure:

1. All tests pass
2. Code is formatted with black
3. Type hints are included
4. Documentation is updated

## License

[Add license information]

## Contact

[Add contact information]
EOF

# Verify
head -20 README.md
```

### Phase 13: Test Import Paths

Verify that the package can be imported correctly.

```bash
# Test basic imports
python << 'EOF'
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path.cwd() / "src"))

# Test imports
try:
    import syntha
    print(f"✓ syntha package imported successfully (version {syntha.__version__})")

    from syntha import generator
    print("✓ syntha.generator imported")

    from syntha import extractor
    print("✓ syntha.extractor imported")

    from syntha.evaluation import adapter
    print("✓ syntha.evaluation.adapter imported")

    from syntha.evaluation import metrics
    print("✓ syntha.evaluation.metrics imported")

    from syntha.evaluation import runner
    print("✓ syntha.evaluation.runner imported")

    from syntha.evaluation import filter
    print("✓ syntha.evaluation.filter imported")

    print("\n✅ All imports successful!")

except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)
EOF
```

### Phase 14: Commit Migration

Commit all changes in logical groups.

```bash
# Stage structure changes
git add src/ tests/ scripts/ configs/ data/ docs/ outputs/

# Stage moved files (should already be staged from git mv)
git add -u

# Stage new files
git add pyproject.toml requirements.txt README.md .gitignore

# Check what will be committed
git status

# Commit with descriptive message
git commit -m "Migrate project to modular structure

- Create src/syntha/ package with generator, extractor, evaluation modules
- Move all source files to new locations with git mv (preserves history)
- Update import statements to use package imports
- Create CLI scripts in scripts/ directory
- Add YAML configuration files in configs/
- Organize data in data/ directory
- Move documentation to docs/ with consistent naming
- Organize outputs in outputs/ subdirectories
- Create pyproject.toml for package metadata
- Add comprehensive README.md
- Update .gitignore for outputs and Python artifacts

All existing functionality preserved. Migration verified with import tests.

Relates to #001-structure-migration"

# Verify commit
git log -1 --stat
```

## Validation

After completing all phases, validate the migration:

### 1. Structure Validation

```bash
# Verify directory structure
tree -L 3 -I '__pycache__|.git|.idea|.deepeval|syn|specs'

# Check for old files (should be empty)
ls -la *.py 2>/dev/null && echo "⚠️  WARNING: Python files remain in root!" || echo "✓ No Python files in root"
```

### 2. Import Validation

```bash
# Test all imports
python -c "from syntha.generator import *; from syntha.extractor import *; from syntha.evaluation import *; print('✓ All imports successful')"
```

### 3. CLI Scripts Validation

```bash
# Test CLI scripts exist and are executable
for script in scripts/*.py; do
    [ -x "$script" ] && echo "✓ $script is executable" || echo "✗ $script not executable"
done
```

### 4. Configuration Validation

```bash
# Test YAML configs are valid
python << 'EOF'
import yaml
configs = ["configs/generation_config.yaml", "configs/extraction_config.yaml", "configs/evaluation_config.yaml"]
for config in configs:
    try:
        yaml.safe_load(open(config))
        print(f"✓ {config} is valid YAML")
    except Exception as e:
        print(f"✗ {config} error: {e}")
EOF
```

### 5. Package Installation Test

```bash
# Test package can be installed
pip install -e .
python -c "import syntha; print(f'✓ Package installed (version {syntha.__version__})')"
```

## Success Criteria Checklist

Run through the success criteria from the specification:

- [ ] **SC-001**: All Python modules can be successfully imported (verify with import test above)
- [ ] **SC-002**: All existing functionality continues to work (manually test workflows)
- [ ] **SC-003**: Project structure matches proposed structure (verify with tree command)
- [ ] **SC-004**: Zero files remain in old locations (verify with ls command)
- [ ] **SC-005**: All CLI scripts execute successfully (test with --help flags)
- [ ] **SC-006**: All tests pass (when tests are written)
- [ ] **SC-007**: Configuration files are valid YAML (verify with YAML test)
- [ ] **SC-008**: Package metadata allows installation (verify with pip install)
- [ ] **SC-009**: Documentation is accessible (verify docs/ exists with files)
- [ ] **SC-010**: Developers can locate components within 30 seconds (manual verification)

## Troubleshooting

### Import Errors

If you encounter ImportError:
1. Verify `__init__.py` files exist in all package directories
2. Check that `sys.path` includes the src/ directory
3. Ensure no circular imports between modules

### Git History Issues

To verify git history was preserved:
```bash
git log --follow -- src/syntha/generator.py
```
Should show history from original synthetic_generator.py

### YAML Parse Errors

If YAML configs fail to parse:
1. Check indentation (use spaces, not tabs)
2. Verify no special characters in strings
3. Use quotes for strings with colons or special chars

### CLI Scripts Not Executable

Make scripts executable:
```bash
chmod +x scripts/*.py
```

## Rollback Procedure

If migration fails and you need to rollback:

```bash
# Reset to pre-migration state
git reset --hard HEAD~1

# Or use backup branch
git checkout backup-before-migration
```

## Next Steps

After successful migration:

1. **Run `/speckit.tasks`** to generate implementation tasks
2. **Create Tests**: Write unit tests in tests/ directory
3. **Update Code**: Refactor code to use config files instead of hardcoded values
4. **Documentation**: Expand README with more detailed examples
5. **CI/CD**: Set up continuous integration for automated testing

## Summary

This quickstart guide walked through:

- ✅ Creating the complete directory structure
- ✅ Moving all source files with git mv
- ✅ Updating import statements
- ✅ Creating CLI scripts
- ✅ Setting up configuration files
- ✅ Organizing documentation
- ✅ Creating package metadata
- ✅ Validating the migration
- ✅ Committing changes

The project is now organized as a proper Python package with clear module boundaries, reusable components, and professional structure.

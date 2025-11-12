# Research: Project Structure Migration

**Feature**: 001-structure-migration
**Date**: 2025-11-11
**Purpose**: Research best practices and resolve technical decisions for migrating to modular Python package structure

## Overview

This document consolidates research findings for migrating the syntha project from a flat file structure to a well-organized Python package with proper separation of concerns.

## Research Areas

### 1. Python Package Structure Best Practices

**Decision**: Use `src/` layout with `src/syntha/` as the package root

**Rationale**:
- **PEP 420**: Namespace packages - allows for proper Python package imports
- **Isolation**: The `src/` layout prevents accidental imports from the development directory
- **Editable Installs**: Works seamlessly with `pip install -e .` for development
- **Testing**: Clear separation between source code and tests prevents test pollution
- **Distribution**: Standard structure recognized by PyPI and packaging tools
- **IDE Support**: Modern IDEs (PyCharm, VSCode) automatically recognize `src/` layout

**Alternatives Considered**:
- **Flat layout** (package at root): Rejected because it can lead to import ambiguity during development and testing
- **Direct package folder** (syntha/ at root): Rejected because it increases risk of importing from working directory instead of installed package

**References**:
- Python Packaging User Guide: https://packaging.python.org/en/latest/tutorials/packaging-projects/
- PEP 420 (Namespace Packages): https://peps.python.org/pep-0420/

### 2. Package Configuration: setup.py vs pyproject.toml

**Decision**: Use `pyproject.toml` with `setuptools` backend

**Rationale**:
- **Modern Standard**: PEP 517/518 establish pyproject.toml as the standard configuration file
- **Single Source**: Consolidates all configuration (build, dependencies, tools) in one file
- **Future-Proof**: The Python community is moving away from setup.py
- **Tool Integration**: Works with black, pytest, mypy, and other tools in same file
- **Cleaner**: Declarative TOML format is more readable than Python code in setup.py

**Alternatives Considered**:
- **setup.py only**: Rejected as it's the legacy approach, though still widely supported
- **setup.cfg + setup.py**: Rejected as it splits configuration across multiple files
- **Poetry**: Rejected to avoid adding another dependency manager when pip + pyproject.toml is sufficient

**Configuration Template**:
```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "syntha"
version = "0.1.0"
description = "Synthetic data generation and evaluation toolkit"
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
    "pandas>=2.0.0",
    "ollama>=0.1.0",
    "deepeval>=0.20.0",
    "pyyaml>=6.0"
]

[project.optional-dependencies]
dev = ["pytest>=7.0.0", "pytest-cov>=4.0.0", "black>=23.0.0", "mypy>=1.0.0"]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
```

### 3. File Migration Strategy

**Decision**: Git mv for file migration to preserve history

**Rationale**:
- **History Preservation**: `git mv` maintains file history through renames/moves
- **Blame/Log Continuity**: `git log --follow` can track changes across the move
- **Safe**: Git tracks the operation atomically, reducing risk of data loss
- **Review-Friendly**: Changes appear as renames in pull requests, not delete+add

**Migration Order**:
1. Create target directory structure (empty directories and __init__.py files)
2. Move and rename source files using `git mv`
3. Update import statements in moved files
4. Move data and documentation files
5. Create new files (CLI scripts, configs, tests)
6. Update or create .gitignore
7. Test imports and functionality
8. Remove old empty directories

**Alternatives Considered**:
- **Copy then delete**: Rejected because it breaks git history tracking
- **Manual mv then git add**: Rejected because git may not recognize it as a rename
- **Symlinks during transition**: Rejected as it adds complexity and isn't a clean migration

### 4. Import Path Management

**Decision**: Update all imports to use absolute imports from `syntha` package

**Rationale**:
- **Clarity**: Absolute imports are more explicit and easier to understand
- **Refactoring**: Moving files doesn't break imports as much
- **Standard Practice**: PEP 8 recommends absolute imports over relative imports
- **IDE Support**: Better autocomplete and refactoring support

**Import Pattern**:
```python
# Before (flat structure)
import synthetic_generator
from deepeval_metrics import AnswerRelevancyMetric

# After (package structure)
from syntha.generator import generate_dataset
from syntha.evaluation.metrics import AnswerRelevancyMetric
```

**Relative Imports**: Use only within the same subpackage for internal module communication
```python
# Within syntha/evaluation/ modules
from .adapter import DeepEvalAdapter  # Same directory
from ..utils.io import load_jsonl     # Parent package
```

**Alternatives Considered**:
- **All relative imports**: Rejected because it makes refactoring harder and is less explicit
- **Mix of absolute and relative**: Accepted for internal package imports, but primary imports should be absolute

### 5. Configuration Management

**Decision**: YAML configuration files in `configs/` directory

**Rationale**:
- **Human-Readable**: YAML is more readable than JSON and supports comments
- **Flexibility**: Easy to modify without code changes
- **Environment-Specific**: Can have multiple config files (dev, prod, test)
- **Version Control**: Config files should be in git for reproducibility
- **Standard Practice**: Widely used in Python projects

**Configuration Structure**:
```yaml
# configs/generation_config.yaml
model:
  name: "glm-4.6:cloud"
  host: "http://localhost:11434"

sampling:
  simple_kpis: 1
  medium_kpis: 3
  complex_kpis: 5

output:
  directory: "outputs/datasets"
  format: "jsonl"
```

**Loading Pattern**:
```python
import yaml
from pathlib import Path

def load_config(config_name):
    config_path = Path(__file__).parent.parent.parent / "configs" / f"{config_name}.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)
```

**Alternatives Considered**:
- **Environment variables**: Rejected as primary method (too many settings), but can override YAML values
- **JSON**: Rejected because YAML is more readable and supports comments
- **Python files**: Rejected because it mixes configuration with code
- **TOML**: Considered but YAML is more widely adopted for this use case

### 6. CLI Scripts Design

**Decision**: Thin wrapper scripts in `scripts/` that import from package

**Rationale**:
- **Separation**: Business logic stays in library, CLI is just an interface
- **Testability**: Can test library functions without invoking CLI
- **Reusability**: Library can be imported by other projects
- **Consistency**: All CLI scripts follow the same pattern

**CLI Script Pattern**:
```python
#!/usr/bin/env python3
"""Generate synthetic dataset from KPI profiles."""

import sys
from pathlib import Path

# Add src to path for development use
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from syntha.generator import main

if __name__ == "__main__":
    sys.exit(main())
```

**Alternatives Considered**:
- **Heavy CLI scripts with logic**: Rejected because it duplicates logic and isn't reusable
- **setuptools entry_points**: Deferred to future enhancement (requires package installation)
- **Click/Typer framework**: Deferred to avoid adding dependencies during migration

### 7. Testing Strategy

**Decision**: pytest with tests mirroring source structure

**Rationale**:
- **Industry Standard**: pytest is the most widely used Python testing framework
- **Powerful**: Fixtures, parametrization, plugins provide excellent testing capabilities
- **Simple**: Easy to write and understand tests
- **Integration**: Works well with coverage tools, CI/CD

**Test Structure**:
```text
tests/
├── __init__.py
├── test_generator.py          # Tests for syntha.generator
├── test_extractor.py          # Tests for syntha.extractor
├── test_evaluation/
│   ├── __init__.py
│   ├── test_adapter.py        # Tests for syntha.evaluation.adapter
│   ├── test_metrics.py        # Tests for syntha.evaluation.metrics
│   ├── test_runner.py         # Tests for syntha.evaluation.runner
│   └── test_filter.py         # Tests for syntha.evaluation.filter
└── fixtures/                  # Test data and fixtures
    ├── sample_kpis.csv
    └── sample_dataset.jsonl
```

**Alternatives Considered**:
- **unittest**: Rejected because pytest is more concise and powerful
- **nose**: Rejected because it's deprecated
- **Flat test directory**: Rejected because mirroring structure improves organization

### 8. Output Directory Management

**Decision**: Git-ignore `outputs/` but keep structure in documentation

**Rationale**:
- **Version Control**: Generated files should not be in git (too large, change frequently)
- **Reproducibility**: Structure and naming conventions documented
- **Local Development**: Each developer generates their own outputs
- **CI/CD**: Outputs generated during pipeline runs

**.gitignore Entry**:
```
# Generated outputs
outputs/
*.jsonl
*.jsonl.meta.json

# Exception: Keep directory structure documentation
!outputs/.gitkeep
!outputs/*/.gitkeep
```

**Alternatives Considered**:
- **Commit all outputs**: Rejected due to repo bloat and merge conflicts
- **Git LFS**: Rejected as unnecessary complexity for local development artifacts
- **Different directory name**: outputs/ is clear and consistent with convention

### 9. README and Documentation

**Decision**: Create comprehensive README.md with quick start and structure guide

**Rationale**:
- **Onboarding**: New developers need to understand the project quickly
- **Migration Guide**: Existing users need to know what changed
- **Best Practice**: Every project should have a clear README

**README Structure**:
1. Project Overview
2. Features
3. Installation
4. Quick Start
5. Project Structure
6. Configuration
7. Development
8. Testing
9. Contributing

**Alternatives Considered**:
- **Minimal README**: Rejected because the migration changes a lot
- **Separate MIGRATION.md**: Could be added later but README should cover basics

## Summary of Decisions

| Area | Decision | Key Benefit |
|------|----------|-------------|
| Package Layout | src/syntha/ structure | Import isolation and testing clarity |
| Package Config | pyproject.toml with setuptools | Modern, single-file configuration |
| Migration Tool | git mv | Preserves file history |
| Import Style | Absolute imports from syntha | Clarity and refactoring support |
| Configuration | YAML in configs/ | Human-readable, version controlled |
| CLI Scripts | Thin wrappers in scripts/ | Reusability and testability |
| Testing | pytest with mirrored structure | Industry standard, powerful features |
| Outputs | Git-ignored with structure docs | Avoid repo bloat, maintain reproducibility |
| Documentation | Comprehensive README.md | Clear onboarding and migration guide |

## Implementation Risks and Mitigations

### Risk 1: Breaking Existing Workflows
**Mitigation**:
- Create migration checklist to verify all functionality works
- Test each component after moving
- Document import path changes

### Risk 2: Lost Git History
**Mitigation**:
- Use `git mv` exclusively for file moves
- Commit renames separately from content changes
- Use `git log --follow` to verify history is preserved

### Risk 3: Import Errors After Migration
**Mitigation**:
- Update imports immediately after moving files
- Use automated search/replace for common patterns
- Test imports before committing

### Risk 4: Confusion About Old vs New Structure
**Mitigation**:
- Complete migration in single feature branch
- Remove old files only after verifying new ones work
- Update documentation to show new structure

## Next Steps

With research complete, proceed to Phase 1:
1. Generate data-model.md (entity relationships in new structure)
2. Generate contracts/migration-map.yaml (file mapping contract)
3. Generate quickstart.md (step-by-step migration execution guide)
4. Update agent context with technology choices

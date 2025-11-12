# Claude Code Context: Syntha Project

**Last Updated**: 2025-11-11
**Feature**: 001-structure-migration

## Project Overview

Syntha is a synthetic data generation and evaluation toolkit built in Python. It uses LLMs (via Ollama) to generate synthetic datasets from KPI profiles, extracts structured information, and evaluates data quality using DeepEval metrics.

## Technology Stack

<!-- BEGIN AUTO-MANAGED SECTION - DO NOT EDIT MANUALLY -->
<!-- This section is automatically updated by .specify/scripts/bash/update-agent-context.sh -->

### Language/Runtime
- **Python 3.12.2**: Primary development language

### Dependencies
- **pandas >= 2.0.0**: Data manipulation and CSV handling
- **ollama >= 0.1.0**: LLM client for synthetic data generation
- **deepeval >= 0.20.0**: Evaluation metrics framework
- **pyyaml >= 6.0**: Configuration file parsing

### Storage
- **File-based**: CSV inputs, JSONL outputs, YAML configs
- No database - all data is file-based

### Testing
- **pytest >= 7.0.0**: Unit testing framework
- **pytest-cov >= 4.0.0**: Coverage reporting

### Project Type
- **Single project**: Python package with CLI tools
- **Structure**: src/ layout (PEP 420 compliant)

<!-- END AUTO-MANAGED SECTION -->

## Current Architecture

### Module Organization

```
src/syntha/
├── __init__.py           # Package root
├── generator.py          # Synthetic data generation
├── extractor.py          # Structured extraction
├── evaluation/           # Evaluation module
│   ├── __init__.py
│   ├── adapter.py        # DeepEval adapter
│   ├── metrics.py        # Custom metrics
│   ├── runner.py         # Evaluation pipeline
│   └── filter.py         # Result filtering
└── utils/                # Utility functions
    ├── __init__.py
    └── io.py             # File I/O utilities
```

### Key Components

1. **Generator** (`syntha.generator`)
   - Loads KPI profiles from CSV
   - Samples KPIs based on complexity (simple/medium/complex)
   - Uses Ollama LLM to generate synthetic campaign rules
   - Outputs JSONL datasets with metadata

2. **Extractor** (`syntha.extractor`)
   - Reads generated text datasets
   - Extracts structured information using LLM
   - Produces structured JSONL outputs
   - Includes schema validation

3. **Evaluation Module** (`syntha.evaluation`)
   - **Adapter**: Creates DeepEval test cases from data
   - **Metrics**: Defines custom evaluation metrics
   - **Runner**: Executes evaluation pipeline
   - **Filter**: Separates passed/failed results

4. **CLI Scripts** (`scripts/`)
   - Thin wrappers that import from package
   - Provide command-line interface
   - Follow pattern: import → call main()

### Configuration

YAML configuration files in `configs/`:
- `generation_config.yaml`: Model settings, sampling rules, output config
- `extraction_config.yaml`: Extraction parameters, retry logic
- `evaluation_config.yaml`: Metrics, thresholds, filtering rules

### Data Flow

```
KPI Profiles (CSV)
    ↓ generator.py
Synthetic Dataset (JSONL)
    ↓ extractor.py
Structured Data (JSONL)
    ↓ evaluation/runner.py
Evaluation Results (JSONL)
    ↓ evaluation/filter.py
Passed/Failed Results (JSONL)
```

## Development Guidelines

### Import Conventions
- **External packages**: Absolute imports (`import pandas as pd`)
- **Syntha package**: Absolute imports from package root (`from syntha.generator import ...`)
- **Within module**: Relative imports (`from .adapter import ...`)

### File Organization
- **Source code**: `src/syntha/`
- **Tests**: `tests/` (mirrors source structure)
- **CLI scripts**: `scripts/`
- **Config**: `configs/`
- **Data**: `data/` (version controlled inputs)
- **Outputs**: `outputs/` (git-ignored, organized by type)

### Testing Strategy
- Unit tests mirror source structure
- Test files named `test_<module>.py`
- Use pytest fixtures for common test data
- Integration tests for pipeline workflows

### Code Style
- Follow PEP 8 conventions
- Use black for formatting (line length: 100)
- Type hints encouraged
- Docstrings for all public functions

## Common Tasks

### Adding a New Module
1. Create file in appropriate location under `src/syntha/`
2. Add to `__init__.py` if part of public API
3. Create corresponding test file in `tests/`
4. Update imports in dependent modules

### Adding Configuration
1. Add YAML file to `configs/`
2. Create config loading function in module
3. Document config keys and defaults
4. Validate config on load

### Creating a CLI Script
1. Create script in `scripts/`
2. Add shebang: `#!/usr/bin/env python3`
3. Import target function from package
4. Call function in `if __name__ == "__main__"` block
5. Make executable: `chmod +x scripts/<script>.py`

## Migration Context

This project recently underwent a structure migration (feature 001-structure-migration) from a flat file layout to a modular package structure. Key changes:

- **Old**: All files in project root
- **New**: Organized into `src/syntha/` package with submodules
- **Preserved**: Git history maintained via `git mv`
- **Impact**: Import paths changed, but functionality preserved

## Known Patterns

### Ollama LLM Usage
```python
from ollama import Client
client = Client(host="http://localhost:11434")
response = client.chat(model="glm-4.6:cloud", messages=[...])
```

### JSONL Output Pattern
```python
# Write with metadata
output_path = Path("outputs/datasets/data.jsonl")
with open(output_path, "w") as f:
    for item in items:
        f.write(json.dumps(item) + "\n")

# Write metadata
meta_path = output_path.with_suffix(output_path.suffix + ".meta.json")
with open(meta_path, "w") as f:
    json.dump(metadata, f, indent=2)
```

### DeepEval Integration
```python
from deepeval.test_case import LLMTestCase
from deepeval.metrics import AnswerRelevancyMetric

test_case = LLMTestCase(input=input_text, actual_output=output_text)
metric = AnswerRelevancyMetric(threshold=0.7)
metric.measure(test_case)
```

## Important Files

- `pyproject.toml`: Package metadata and configuration
- `requirements.txt`: Dependency list
- `README.md`: Project documentation
- `.gitignore`: Excludes outputs/ and Python artifacts

## Development Setup

```bash
# Clone and install
git clone <repo>
cd syntha
pip install -e .

# Run generation
python scripts/generate_dataset.py

# Run tests
pytest tests/
```

## Questions & Clarifications

When modifying code:
- Preserve existing functionality
- Update tests when changing behavior
- Keep imports organized (external → package → relative)
- Update configs instead of hardcoding values
- Follow existing patterns for consistency

---

**Note**: This file is automatically updated by the speckit workflow. Manual additions should be made outside the AUTO-MANAGED SECTION markers.
- When committing to GitHub, no need to include done by Claude
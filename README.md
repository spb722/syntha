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
│   ├── generate_dataset.py
│   ├── extract_structure.py
│   ├── run_evaluation.py
│   └── filter_results.py
├── configs/              # YAML configuration
│   ├── generation_config.yaml
│   ├── extraction_config.yaml
│   └── evaluation_config.yaml
├── data/                 # Input data files
│   └── kpi_profiles.csv
├── docs/                 # Documentation
│   ├── AGENTS.md
│   ├── story_1.1.md
│   └── story_1.2.md
├── tests/                # Test suite
│   ├── test_generator.py
│   ├── test_extractor.py
│   └── test_evaluation/
└── outputs/              # Generated outputs (git-ignored)
    ├── datasets/
    ├── structured/
    ├── evaluations/
    └── filtered/
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

- **generation_config.yaml** - Synthetic data generation settings
  - Model configuration (name, host, timeout)
  - Sampling rules (KPI complexity levels)
  - Output settings

- **extraction_config.yaml** - Structured extraction settings
  - Model configuration
  - Schema validation options
  - Retry logic

- **evaluation_config.yaml** - Evaluation pipeline settings
  - Metrics and thresholds
  - Batch processing settings
  - Output filtering rules

Edit these files to customize behavior without changing code.

## CLI Scripts

All CLI scripts are located in the `scripts/` directory:

- **generate_dataset.py** - Generate synthetic data from KPI profiles
- **extract_structure.py** - Extract structured data from generated text
- **run_evaluation.py** - Run evaluation pipeline on structured data
- **filter_results.py** - Filter results into passed/failed categories

Each script is a thin wrapper that calls the corresponding module function.

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

Additional documentation is available in the `docs/` directory:

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

# Data Model: Project Structure Migration

**Feature**: 001-structure-migration
**Date**: 2025-11-11
**Purpose**: Define entities, relationships, and state transitions for the migration process

## Overview

This document describes the conceptual entities involved in the project structure migration. Since this is a file migration and reorganization task (not a runtime data model), the "entities" represent file system objects and their relationships in the migration process.

## Core Entities

### 1. SourceFile

Represents a Python source file in the old structure that needs to be migrated.

**Attributes**:
- `old_path`: Absolute path in current structure (e.g., `/syntha/synthetic_generator.py`)
- `new_path`: Target path in new structure (e.g., `/syntha/src/syntha/generator.py`)
- `file_type`: Category of file (`source`, `test`, `doc`, `data`, `config`, `output`)
- `has_imports`: Boolean indicating if file contains import statements
- `import_dependencies`: List of other files this file imports from
- `migration_status`: Current state (`pending`, `moved`, `imports_updated`, `tested`, `completed`)

**Relationships**:
- Has many `ImportStatement` objects (import lines that need updating)
- Belongs to `Module` (the module it will be part of in new structure)
- May reference other `SourceFile` objects through imports

**Validation Rules**:
- `old_path` must exist before migration
- `new_path` must not exist before migration (no overwrites)
- `file_type` must be one of predefined categories
- `migration_status` must follow state transition rules (see State Transitions section)

**State Transitions**:
```
pending → moved → imports_updated → tested → completed
         ↓
      rollback (if errors detected)
```

### 2. Module

Represents a Python module (directory with __init__.py) in the new structure.

**Attributes**:
- `module_path`: Path to module directory (e.g., `src/syntha/evaluation/`)
- `module_name`: Importable name (e.g., `syntha.evaluation`)
- `has_init`: Boolean indicating if __init__.py exists
- `submodules`: List of child modules
- `source_files`: List of Python files in this module

**Relationships**:
- Contains many `SourceFile` objects
- May contain child `Module` objects (submodules)
- Belongs to parent `Module` (or root if top-level)

**Validation Rules**:
- Must have `__init__.py` file to be a valid Python package
- `module_name` must be valid Python identifier
- Path must exist before files are moved into it

### 3. ImportStatement

Represents an import statement that needs to be updated during migration.

**Attributes**:
- `file_path`: Path to file containing this import
- `line_number`: Line number in file
- `old_import`: Original import statement (e.g., `import synthetic_generator`)
- `new_import`: Updated import statement (e.g., `from syntha.generator import ...`)
- `import_type`: Type of import (`absolute`, `relative`, `star`)
- `is_updated`: Boolean indicating if update is complete

**Relationships**:
- Belongs to `SourceFile`
- References target `SourceFile` or `Module`

**Validation Rules**:
- `old_import` must be parseable Python import
- `new_import` must follow package import conventions
- `line_number` must be valid for the file

### 4. Directory

Represents a directory in the new structure that needs to be created.

**Attributes**:
- `dir_path`: Absolute path (e.g., `/syntha/configs/`)
- `purpose`: Description of directory purpose
- `should_be_in_git`: Boolean indicating if directory should be version controlled
- `gitignore_pattern`: Pattern to add to .gitignore if needed
- `creation_status`: State (`not_created`, `created`, `populated`)

**Relationships**:
- May contain `SourceFile` objects
- May contain child `Directory` objects
- May contain `ConfigFile` objects

**Validation Rules**:
- `dir_path` must be under project root
- Parent directory must exist before creating child
- Git-ignored directories should have .gitkeep if structure needs documentation

**Required Directories**:
```
src/
src/syntha/
src/syntha/evaluation/
src/syntha/utils/
tests/
tests/test_evaluation/
scripts/
configs/
data/
docs/
outputs/
outputs/datasets/
outputs/structured/
outputs/evaluations/
outputs/filtered/
```

### 5. ConfigFile

Represents a YAML configuration file to be created.

**Attributes**:
- `config_path`: Path to config file (e.g., `configs/generation_config.yaml`)
- `config_type`: Type of configuration (`generation`, `extraction`, `evaluation`)
- `template_content`: Initial YAML structure
- `extracted_from`: Source file that had hardcoded config (if applicable)
- `creation_status`: State (`not_created`, `created`, `validated`)

**Relationships**:
- Belongs to `Directory` (configs/)
- May be referenced by `SourceFile` objects that read configuration

**Validation Rules**:
- Must be valid YAML format
- Required keys must be present for each config type
- Values must match expected types (strings, numbers, lists, etc.)

### 6. CLIScript

Represents a command-line interface script in scripts/ directory.

**Attributes**:
- `script_path`: Path to script (e.g., `scripts/generate_dataset.py`)
- `script_name`: Name without extension (e.g., `generate_dataset`)
- `target_module`: Module it calls (e.g., `syntha.generator`)
- `target_function`: Function it invokes (e.g., `main`)
- `has_shebang`: Boolean indicating if #!/usr/bin/env python3 present
- `is_executable`: Boolean indicating if execute permission set
- `creation_status`: State (`not_created`, `created`, `tested`)

**Relationships**:
- Imports from `Module`
- Calls function in `SourceFile`

**Validation Rules**:
- Must have shebang line for Unix execution
- Must have executable permission (chmod +x)
- Target module must exist and be importable
- Must follow thin wrapper pattern (minimal logic)

**Required CLI Scripts**:
- `scripts/generate_dataset.py` → calls `syntha.generator.main()`
- `scripts/extract_structure.py` → calls `syntha.extractor.main()`
- `scripts/run_evaluation.py` → calls `syntha.evaluation.runner.main()`
- `scripts/filter_results.py` → calls `syntha.evaluation.filter.main()`

### 7. TestFile

Represents a test file in tests/ directory.

**Attributes**:
- `test_path`: Path to test file (e.g., `tests/test_generator.py`)
- `test_module`: Module being tested (e.g., `syntha.generator`)
- `test_functions`: List of test function names
- `has_fixtures`: Boolean indicating if test fixtures are defined
- `creation_status`: State (`not_created`, `created`, `passing`)

**Relationships**:
- Tests `SourceFile` or `Module`
- May use fixtures from shared location

**Validation Rules**:
- Must follow pytest naming convention (`test_*.py`)
- Test functions must start with `test_`
- Must import from correct module paths
- All tests must pass before migration is complete

### 8. PackageMetadata

Represents the package configuration (pyproject.toml).

**Attributes**:
- `package_name`: Name of package (`syntha`)
- `version`: Semantic version (e.g., `0.1.0`)
- `dependencies`: List of required packages
- `dev_dependencies`: List of development dependencies
- `python_version`: Minimum Python version required
- `creation_status`: State (`not_created`, `created`, `validated`)

**Relationships**:
- Defines `Module` structure
- Lists `SourceFile` dependencies

**Validation Rules**:
- Must be valid TOML format
- Version must follow semantic versioning
- Python version must match actual requirement (3.12+)
- All dependencies must be valid package names

## Entity Relationships Diagram

```
┌─────────────────┐
│ PackageMetadata │
└────────┬────────┘
         │ defines
         ▼
    ┌─────────┐
    │  Module │◄──────────┐
    └────┬────┘           │
         │ contains       │ belongs to
         ▼                │
  ┌──────────────┐        │
  │  SourceFile  │────────┘
  └──────┬───────┘
         │ has
         ▼
  ┌───────────────────┐
  │ ImportStatement   │
  └───────────────────┘

┌───────────┐
│ Directory │
└─────┬─────┘
      │ contains
      ├─────────►┌──────────────┐
      │          │  ConfigFile  │
      │          └──────────────┘
      │
      ├─────────►┌──────────────┐
      │          │  CLIScript   │──────► calls Module/SourceFile
      │          └──────────────┘
      │
      └─────────►┌──────────────┐
                 │  TestFile    │──────► tests Module/SourceFile
                 └──────────────┘
```

## State Transitions

### SourceFile Migration States

```
┌─────────┐
│ pending │  Initial state, file identified for migration
└────┬────┘
     │ git mv executed
     ▼
┌─────────┐
│  moved  │  File physically moved to new location
└────┬────┘
     │ import statements updated
     ▼
┌──────────────────┐
│ imports_updated  │  All import statements corrected
└────┬─────────────┘
     │ functionality verified
     ▼
┌─────────┐
│ tested  │  File works correctly in new location
└────┬────┘
     │ old location removed
     ▼
┌───────────┐
│ completed │  Migration fully complete
└───────────┘
```

### Directory Creation States

```
┌──────────────┐
│ not_created  │  Directory planned but not yet created
└──────┬───────┘
       │ mkdir executed
       ▼
┌──────────┐
│ created  │  Directory exists, may be empty
└────┬─────┘
     │ files added
     ▼
┌────────────┐
│ populated  │  Directory contains expected files
└────────────┘
```

### Configuration File States

```
┌──────────────┐
│ not_created  │  Config file planned
└──────┬───────┘
       │ template written
       ▼
┌──────────┐
│ created  │  YAML file exists with template content
└────┬─────┘
     │ YAML validation passed
     ▼
┌────────────┐
│ validated  │  Config is parseable and has required keys
└────────────┘
```

### CLIScript Creation States

```
┌──────────────┐
│ not_created  │  Script planned
└──────┬───────┘
       │ script written
       ▼
┌──────────┐
│ created  │  Script file exists with import and call
└────┬─────┘
     │ execution test passed
     ▼
┌──────────┐
│  tested  │  Script successfully calls target function
└──────────┘
```

## Migration Dependencies

The order of migration matters due to dependencies:

**Phase 1: Structure Creation**
1. Create all `Directory` objects (directories must exist before files move in)
2. Create `__init__.py` files for all `Module` objects

**Phase 2: File Migration**
3. Move `SourceFile` objects using git mv (preserve history)
4. Update `ImportStatement` objects in moved files
5. Move `DataFile` and `DocFile` objects

**Phase 3: New File Creation**
6. Create `ConfigFile` objects (extract hardcoded config)
7. Create `CLIScript` objects (thin wrappers)
8. Create `TestFile` objects (test infrastructure)
9. Create `PackageMetadata` (pyproject.toml)

**Phase 4: Validation**
10. Verify all imports work
11. Run all tests
12. Execute all CLI scripts
13. Validate all YAML configs

## Data Integrity Constraints

### File Migration Constraints
- **No Overwrites**: New path must not exist before moving file
- **History Preservation**: Use `git mv` to maintain version history
- **Atomicity**: Each file migration should be a distinct operation
- **Rollback Safety**: Original file location known for rollback if needed

### Import Update Constraints
- **Syntax Validity**: All import statements must be valid Python
- **Circular Dependencies**: No circular imports between modules
- **Missing References**: All imported modules/functions must exist

### Configuration Constraints
- **YAML Validity**: All config files must parse without errors
- **Required Keys**: Each config type has mandatory keys that must be present
- **Type Safety**: Config values must match expected types

### Package Structure Constraints
- **Module Hierarchy**: All Python packages must have `__init__.py`
- **Naming Convention**: Module names must be valid Python identifiers
- **Import Paths**: Package must be importable from `src/syntha`

## Summary

This data model defines 8 core entities and their relationships for the migration process. The key entities are:

1. **SourceFile** - Python files being migrated
2. **Module** - Python packages in new structure
3. **ImportStatement** - Import lines needing updates
4. **Directory** - New directories to create
5. **ConfigFile** - YAML configuration files
6. **CLIScript** - Command-line entry points
7. **TestFile** - Test files for validation
8. **PackageMetadata** - Package configuration

Each entity has clear validation rules and state transitions to ensure a safe, traceable migration process.

# Feature Specification: Project Structure Migration

**Feature Branch**: `001-structure-migration`
**Created**: 2025-11-11
**Status**: Draft
**Input**: User description: "Migrate project to proposed modular structure: reorganize source code into src/syntha/ with generator/extractor/evaluation modules, create tests/ directory, add configs/ for YAML configs, establish outputs/ structure for datasets/structured/evaluations/filtered, and create scripts/ for CLI entry points"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Core Structure Setup (Priority: P1)

As a developer working on the project, I need the basic directory structure and module organization in place so that I can easily locate and understand where different components live.

**Why this priority**: This is the foundation for all other migration work. Without the proper directory structure and module organization, no other files can be migrated correctly. This delivers immediate value by establishing clear separation of concerns.

**Independent Test**: Can be fully tested by verifying that all directories exist in the correct locations, that __init__.py files make modules importable, and that the structure matches the specification. Delivers value by providing a clear, navigable project layout.

**Acceptance Scenarios**:

1. **Given** an existing flat project structure, **When** the migration is applied, **Then** a src/syntha/ directory exists with subdirectories for generator, extractor, evaluation, and utils modules
2. **Given** the new structure is in place, **When** importing syntha modules, **Then** Python can successfully import from syntha.generator, syntha.extractor, syntha.evaluation, and syntha.utils
3. **Given** the migration is complete, **When** examining the project root, **Then** separate top-level directories exist for tests/, configs/, scripts/, data/, outputs/, and docs/
4. **Given** the outputs/ directory is created, **When** checking its structure, **Then** subdirectories exist for datasets/, structured/, evaluations/, and filtered/

---

### User Story 2 - File Migration and Renaming (Priority: P2)

As a developer, I need all existing source files to be moved to their correct locations with consistent naming so that the codebase follows a clear naming convention and organizational pattern.

**Why this priority**: This enables the actual code to be accessible in the new structure. Without moving the files, the structure is just empty directories. This builds on P1 and delivers working code in the new locations.

**Independent Test**: Can be fully tested by verifying that specific files (synthetic_generator.py ’ generator.py, structured_extractor.py ’ extractor.py, etc.) exist in their new locations with updated import statements, and that old file locations no longer exist. Delivers value by providing a clean, consistently-named codebase.

**Acceptance Scenarios**:

1. **Given** files in the old structure, **When** migration is complete, **Then** synthetic_generator.py has been moved to src/syntha/generator.py
2. **Given** files in the old structure, **When** migration is complete, **Then** structured_extractor.py has been moved to src/syntha/extractor.py
3. **Given** evaluation-related files, **When** migration is complete, **Then** all evaluation files (adapter, metrics, runner, filter) are in src/syntha/evaluation/ with simplified names
4. **Given** documentation files, **When** migration is complete, **Then** Story 1.1.md and Story 1.2.md have been renamed to story_1.1.md and story_1.2.md in the docs/ directory
5. **Given** the old file locations, **When** migration is complete, **Then** original files no longer exist in their old locations

---

### User Story 3 - Import Path Updates (Priority: P2)

As a developer, I need all import statements across the codebase to be updated to reflect the new module structure so that the code continues to function without import errors.

**Why this priority**: This is critical for the code to actually run after migration. Same priority as P2 because file migration and import updates are interdependent - both must be completed for a working system.

**Independent Test**: Can be fully tested by running all scripts and checking for ImportError exceptions, and by verifying that each import statement follows the new structure (e.g., from syntha.generator import ...). Delivers value by ensuring the migrated code is executable.

**Acceptance Scenarios**:

1. **Given** code that previously imported from flat structure, **When** imports are updated, **Then** all imports use the new module paths (e.g., from syntha.generator import ..., from syntha.evaluation.metrics import ...)
2. **Given** CLI scripts in scripts/, **When** they are executed, **Then** they successfully import from src/syntha modules without errors
3. **Given** test files, **When** they are executed, **Then** they successfully import the modules under test using the new import paths
4. **Given** internal imports within syntha modules, **When** modules import from each other, **Then** they use relative or absolute imports that work correctly in the package structure

---

### User Story 4 - CLI Scripts Creation (Priority: P3)

As a user of the system, I need convenient CLI entry points in the scripts/ directory so that I can easily run common operations without needing to understand the internal module structure.

**Why this priority**: This provides a better user experience but is not required for the core functionality to work. Scripts can be added after the core migration is complete.

**Independent Test**: Can be fully tested by running each script (generate_dataset.py, extract_structure.py, run_evaluation.py, filter_results.py) and verifying they call the correct functions from the syntha modules. Delivers value by providing simple command-line tools.

**Acceptance Scenarios**:

1. **Given** the scripts/ directory exists, **When** a user runs scripts/generate_dataset.py, **Then** it calls functions from syntha.generator
2. **Given** the scripts/ directory exists, **When** a user runs scripts/extract_structure.py, **Then** it calls functions from syntha.extractor
3. **Given** the scripts/ directory exists, **When** a user runs scripts/run_evaluation.py, **Then** it calls functions from syntha.evaluation.runner
4. **Given** the scripts/ directory exists, **When** a user runs scripts/filter_results.py, **Then** it calls functions from syntha.evaluation.filter
5. **Given** each script file, **When** examining the code, **Then** each script is a thin wrapper that primarily imports and calls the appropriate module function

---

### User Story 5 - Configuration Files Migration (Priority: P3)

As a developer, I need configuration files organized in a dedicated configs/ directory so that environment-specific settings are separated from code and easily accessible.

**Why this priority**: Configuration management is important for maintainability but doesn't block core functionality. This can be implemented after the code structure is working.

**Independent Test**: Can be fully tested by verifying that YAML configuration files exist in configs/ directory and that code reads from these locations. Delivers value by centralizing configuration management.

**Acceptance Scenarios**:

1. **Given** configuration needs, **When** configs/ directory is checked, **Then** it contains generation_config.yaml, extraction_config.yaml, and evaluation_config.yaml files
2. **Given** code that needs configuration, **When** it runs, **Then** it reads configuration from the files in configs/ directory
3. **Given** a need to modify behavior, **When** a user updates a YAML file in configs/, **Then** the change is reflected in the system behavior without code changes

---

### User Story 6 - Test Suite Organization (Priority: P4)

As a developer, I need tests organized in a dedicated tests/ directory with clear naming that mirrors the source structure so that I can easily find and run tests for specific modules.

**Why this priority**: Testing is critical for quality, but test organization can be improved after the core migration. Tests can be moved and organized independently of the core functionality.

**Independent Test**: Can be fully tested by running the test suite from the tests/ directory and verifying all tests pass, and by checking that test file names match their corresponding source modules. Delivers value by providing organized, maintainable tests.

**Acceptance Scenarios**:

1. **Given** a tests/ directory, **When** examining its structure, **Then** it contains test files named test_generator.py, test_extractor.py, test_metrics.py that mirror the source structure
2. **Given** test files, **When** they are executed, **Then** they import from the correct syntha modules using the new import paths
3. **Given** a developer needs to test a specific module, **When** looking for tests, **Then** the test file name clearly indicates which module it tests (e.g., test_generator.py tests syntha.generator)
4. **Given** the test suite, **When** running all tests, **Then** all tests pass and produce clear output showing which modules were tested

---

### Edge Cases

- What happens when existing scripts or external tools reference the old file paths?
- How does the system handle if the migration is partially complete (some files moved, others not)?
- What happens when there are circular dependencies between modules during the migration?
- How does the system handle if outputs/ directory already exists with generated files?
- What happens when configuration files are missing or malformed?
- How does the system handle if there are local uncommitted changes in files being moved?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST create a directory structure with src/syntha/ as the root package directory
- **FR-002**: System MUST create subdirectories within src/syntha/ for: generator, extractor, evaluation, and utils modules
- **FR-003**: System MUST create top-level directories for: tests/, scripts/, configs/, data/, docs/, and outputs/
- **FR-004**: System MUST create subdirectories within outputs/ for: datasets/, structured/, evaluations/, and filtered/
- **FR-005**: System MUST move existing source files to their new locations: synthetic_generator.py ’ src/syntha/generator.py, structured_extractor.py ’ src/syntha/extractor.py
- **FR-006**: System MUST move evaluation-related files to src/syntha/evaluation/ with renamed files: deepeval_adapter.py ’ adapter.py, deepeval_metrics.py ’ metrics.py, deepeval_runner.py ’ runner.py, filter_eval_results.py ’ filter.py
- **FR-007**: System MUST create __init__.py files in all Python package directories to enable proper module imports
- **FR-008**: System MUST update all import statements throughout the codebase to reflect the new module structure
- **FR-009**: System MUST create CLI entry point scripts in scripts/ directory that import and call functions from src/syntha modules
- **FR-010**: System MUST preserve existing functionality - all operations that worked before migration must work after migration
- **FR-011**: System MUST move data files (e.g., kpi_profiles.csv) to the data/ directory
- **FR-012**: System MUST move documentation files to docs/ directory with consistent naming (Story X.Y.md ’ story_x.y.md)
- **FR-013**: System MUST update .gitignore to exclude the outputs/ directory from version control
- **FR-014**: System MUST create configuration YAML files in configs/ directory (generation_config.yaml, extraction_config.yaml, evaluation_config.yaml)
- **FR-015**: System MUST create or update setup.py or pyproject.toml to define the syntha package with proper metadata
- **FR-016**: System MUST create a README.md in the project root with overview and quick start instructions
- **FR-017**: System MUST remove old file locations after successful migration to prevent confusion

### Key Entities

- **Source Module**: A Python module within src/syntha/ (generator, extractor, evaluation, utils) that contains core functionality, can be imported by other modules or scripts
- **CLI Script**: An executable Python script in scripts/ directory that provides a command-line interface, imports from source modules, and acts as an entry point for users
- **Configuration File**: A YAML file in configs/ directory that contains environment-specific or behavior-modifying settings, read by source modules at runtime
- **Output Artifact**: A generated file (JSONL or JSON) stored in outputs/ subdirectories, produced by running the system, and excluded from version control
- **Test File**: A Python file in tests/ directory that contains unit tests for specific modules, mirrors the structure of source modules
- **Data File**: An input file (e.g., CSV) stored in data/ directory that is read by the system, and version controlled

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All Python modules can be successfully imported using the new package structure (e.g., from syntha.generator import ...) without ImportError
- **SC-002**: All existing functionality continues to work - any script that ran before migration runs successfully after migration
- **SC-003**: Project structure matches the proposed structure with 7 top-level directories (src/, tests/, scripts/, configs/, data/, outputs/, docs/) and correct subdirectories
- **SC-004**: Zero files remain in old locations after migration is complete (excluding outputs/ which may contain historical generated files)
- **SC-005**: All CLI scripts in scripts/ execute successfully and produce expected results
- **SC-006**: All tests in tests/ directory pass when run from the test suite
- **SC-007**: Configuration files in configs/ are valid YAML and can be parsed without errors
- **SC-008**: Package metadata (setup.py or pyproject.toml) allows the syntha package to be installed and imported
- **SC-009**: Documentation is accessible in docs/ directory and provides clear guidance on the new structure
- **SC-010**: Developers can locate any component within 30 seconds by following the logical structure (e.g., "Where is the synthetic data generator?" ’ src/syntha/generator.py)
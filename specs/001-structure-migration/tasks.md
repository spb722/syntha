# Tasks: Project Structure Migration

**Input**: Design documents from `/specs/001-structure-migration/`
**Prerequisites**: plan.md (✓), spec.md (✓), research.md (✓), data-model.md (✓), contracts/migration-map.yaml (✓), quickstart.md (✓)

**Tests**: Tests are NOT required for this migration feature. Tasks focus on file migration, structure creation, and validation.

**Organization**: Tasks are grouped by user story (priority order from spec.md) to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: Migrating to `src/syntha/`, `tests/`, `scripts/`, `configs/`, `data/`, `docs/`, `outputs/` at repository root
- All paths are absolute from `/Users/sachinpb/PycharmProjects/syntha/`
- Migration uses `git mv` to preserve history per research.md decision

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the complete directory structure and initialize Python packages

- [X] T001 Create src/ root directory at /Users/sachinpb/PycharmProjects/syntha/src/
- [X] T002 Create src/syntha/ package directory with __init__.py containing version metadata
- [X] T003 [P] Create src/syntha/evaluation/ subpackage directory with __init__.py
- [X] T004 [P] Create src/syntha/utils/ subpackage directory with __init__.py
- [X] T005 [P] Create tests/ root directory with __init__.py
- [X] T006 [P] Create tests/test_evaluation/ subdirectory with __init__.py
- [X] T007 [P] Create scripts/ directory for CLI entry points
- [X] T008 [P] Create configs/ directory for YAML configuration files
- [X] T009 [P] Create data/ directory for input data files
- [X] T010 [P] Create docs/ directory for documentation
- [X] T011 [P] Create outputs/ directory structure with subdirectories: datasets/, structured/, evaluations/, filtered/
- [X] T012 Verify all directories exist and Python packages are importable

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core package initialization and git repository setup that MUST be complete before file migration

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T013 Add package version and metadata to src/syntha/__init__.py (__version__ = "0.1.0")
- [X] T014 [P] Add docstring to src/syntha/evaluation/__init__.py describing evaluation module purpose
- [X] T015 [P] Add docstring to src/syntha/utils/__init__.py describing utilities module purpose
- [X] T016 Verify git working directory is clean (no uncommitted changes) before migration
- [X] T017 Create backup branch (git branch backup-before-migration) for safety

**Checkpoint**: Foundation ready - file migration can now begin

---

## Phase 3: User Story 1 - Core Structure Setup (Priority: P1) 🎯 MVP

**Goal**: Establish the basic directory structure and module organization so developers can locate and understand where components live

**Independent Test**: Verify all directories exist, __init__.py files make modules importable, and structure matches specification (tree command validation)

### Implementation for User Story 1

- [X] T018 [US1] Verify src/syntha/ directory structure matches plan.md (src/, syntha/, evaluation/, utils/)
- [X] T019 [US1] Verify tests/ directory structure matches plan.md (tests/, test_evaluation/)
- [X] T020 [US1] Verify supporting directories exist (scripts/, configs/, data/, docs/, outputs/ with subdirectories)
- [X] T021 [US1] Test Python package imports: `python -c "import syntha; from syntha.evaluation import *; from syntha.utils import *"`
- [X] T022 [US1] Run tree command to visualize structure and confirm 7 top-level directories exist
- [X] T023 [US1] Verify outputs/ has 4 subdirectories (datasets/, structured/, evaluations/, filtered/)

**Checkpoint**: At this point, complete directory structure exists and is Python-importable

---

## Phase 4: User Story 2 - File Migration and Renaming (Priority: P2)

**Goal**: Move all existing source files to correct locations with consistent naming so codebase follows clear naming conventions

**Independent Test**: Verify specific files exist in new locations, old locations are empty, and git history is preserved (git log --follow)

### Implementation for User Story 2

- [X] T024 [P] [US2] Move synthetic_generator.py to src/syntha/generator.py using git mv
- [X] T025 [P] [US2] Move structured_extractor.py to src/syntha/extractor.py using git mv
- [X] T026 [P] [US2] Move deepeval_adapter.py to src/syntha/evaluation/adapter.py using git mv
- [X] T027 [P] [US2] Move deepeval_metrics.py to src/syntha/evaluation/metrics.py using git mv
- [X] T028 [P] [US2] Move deepeval_runner.py to src/syntha/evaluation/runner.py using git mv
- [X] T029 [P] [US2] Move filter_eval_results.py to src/syntha/evaluation/filter.py using git mv
- [X] T030 [US2] Verify all 6 source files exist in new locations using ls commands
- [X] T031 [US2] Verify old locations no longer contain .py files (except in __pycache__) using ls *.py
- [X] T032 [P] [US2] Move kpi_profiles.csv to data/kpi_profiles.csv using git mv
- [X] T033 [P] [US2] Move AGENTS.md to docs/AGENTS.md using git mv
- [X] T034 [P] [US2] Move "Story 1.1.md" to docs/story_1.1.md using git mv (rename for consistency)
- [X] T035 [P] [US2] Move "Story 1.2.md" to docs/story_1.2.md using git mv (rename for consistency)
- [X] T036 [US2] Test git history preservation: git log --follow -- src/syntha/generator.py (should show original synthetic_generator.py history)
- [X] T037 [US2] Run git status to review all renames before committing

**Checkpoint**: All files migrated to new locations with git history preserved

---

## Phase 5: User Story 3 - Import Path Updates (Priority: P2)

**Goal**: Update all import statements to reflect new module structure so code continues to function without import errors

**Independent Test**: Run all scripts checking for ImportError exceptions, verify each import follows new package structure

### Implementation for User Story 3

- [ ] T038 [US3] Search for internal imports in evaluation module files: grep -n "from deepeval_\|import deepeval_" src/syntha/evaluation/*.py
- [ ] T039 [P] [US3] Update imports in src/syntha/evaluation/metrics.py to use relative imports (from .adapter import ...)
- [ ] T040 [P] [US3] Update imports in src/syntha/evaluation/runner.py to use relative imports (from .adapter import ..., from .metrics import ...)
- [ ] T041 [P] [US3] Update imports in src/syntha/evaluation/filter.py to use relative imports if needed
- [ ] T042 [US3] Verify no remaining old-style imports exist: grep -r "from deepeval_\|import deepeval_" src/syntha/
- [ ] T043 [P] [US3] Test syntax for src/syntha/generator.py: python -m py_compile src/syntha/generator.py
- [ ] T044 [P] [US3] Test syntax for src/syntha/extractor.py: python -m py_compile src/syntha/extractor.py
- [ ] T045 [P] [US3] Test syntax for src/syntha/evaluation/adapter.py: python -m py_compile src/syntha/evaluation/adapter.py
- [ ] T046 [P] [US3] Test syntax for src/syntha/evaluation/metrics.py: python -m py_compile src/syntha/evaluation/metrics.py
- [ ] T047 [P] [US3] Test syntax for src/syntha/evaluation/runner.py: python -m py_compile src/syntha/evaluation/runner.py
- [ ] T048 [P] [US3] Test syntax for src/syntha/evaluation/filter.py: python -m py_compile src/syntha/evaluation/filter.py
- [ ] T049 [US3] Test all imports work: python -c "from syntha.generator import *; from syntha.extractor import *; from syntha.evaluation import *"
- [ ] T050 [US3] Create test script to verify imports and run it in tests/test_imports.py

**Checkpoint**: All imports updated and validated, code compiles without syntax errors

---

## Phase 6: User Story 4 - CLI Scripts Creation (Priority: P3)

**Goal**: Create convenient CLI entry points so users can run common operations without understanding internal module structure

**Independent Test**: Run each script and verify they call correct functions from syntha modules (test with --help or minimal execution)

### Implementation for User Story 4

- [ ] T051 [P] [US4] Create scripts/generate_dataset.py CLI wrapper calling syntha.generator.main()
- [ ] T052 [P] [US4] Create scripts/extract_structure.py CLI wrapper calling syntha.extractor.main()
- [ ] T053 [P] [US4] Create scripts/run_evaluation.py CLI wrapper calling syntha.evaluation.runner.main()
- [ ] T054 [P] [US4] Create scripts/filter_results.py CLI wrapper calling syntha.evaluation.filter.main()
- [ ] T055 [US4] Add shebang (#!/usr/bin/env python3) to all 4 scripts
- [ ] T056 [US4] Make all scripts executable: chmod +x scripts/*.py
- [ ] T057 [P] [US4] Test scripts/generate_dataset.py imports and runs without errors
- [ ] T058 [P] [US4] Test scripts/extract_structure.py imports and runs without errors
- [ ] T059 [P] [US4] Test scripts/run_evaluation.py imports and runs without errors
- [ ] T060 [P] [US4] Test scripts/filter_results.py imports and runs without errors
- [ ] T061 [US4] Verify all scripts are executable: ls -la scripts/*.py | grep "rwxr"

**Checkpoint**: All CLI scripts created, executable, and successfully call package functions

---

## Phase 7: User Story 5 - Configuration Files Migration (Priority: P3)

**Goal**: Organize configuration files in dedicated configs/ directory so environment-specific settings are separated from code

**Independent Test**: Verify YAML files exist, are valid YAML, and code can read from these locations

### Implementation for User Story 5

- [ ] T062 [P] [US5] Create configs/generation_config.yaml with model settings, sampling rules, output config
- [ ] T063 [P] [US5] Create configs/extraction_config.yaml with extraction parameters, retry logic, output config
- [ ] T064 [P] [US5] Create configs/evaluation_config.yaml with metrics, thresholds, filtering rules, output config
- [ ] T065 [P] [US5] Validate YAML syntax for configs/generation_config.yaml using python -c "import yaml; yaml.safe_load(open('configs/generation_config.yaml'))"
- [ ] T066 [P] [US5] Validate YAML syntax for configs/extraction_config.yaml using python -c "import yaml; yaml.safe_load(open('configs/extraction_config.yaml'))"
- [ ] T067 [P] [US5] Validate YAML syntax for configs/evaluation_config.yaml using python -c "import yaml; yaml.safe_load(open('configs/evaluation_config.yaml'))"
- [ ] T068 [US5] Verify all 3 config files exist and parse without errors

**Checkpoint**: All configuration files created, validated, and ready for use

---

## Phase 8: User Story 6 - Test Suite Organization (Priority: P4)

**Goal**: Organize tests in dedicated tests/ directory with clear naming mirroring source structure

**Independent Test**: Verify test file names match modules, tests directory structure mirrors source structure

### Implementation for User Story 6

- [ ] T069 [P] [US6] Create tests/test_generator.py test file skeleton for syntha.generator module
- [ ] T070 [P] [US6] Create tests/test_extractor.py test file skeleton for syntha.extractor module
- [ ] T071 [P] [US6] Create tests/test_evaluation/test_adapter.py test file skeleton for syntha.evaluation.adapter module
- [ ] T072 [P] [US6] Create tests/test_evaluation/test_metrics.py test file skeleton for syntha.evaluation.metrics module
- [ ] T073 [P] [US6] Create tests/test_evaluation/test_runner.py test file skeleton for syntha.evaluation.runner module
- [ ] T074 [P] [US6] Create tests/test_evaluation/test_filter.py test file skeleton for syntha.evaluation.filter module
- [ ] T075 [US6] Verify all test files exist and follow pytest naming convention (test_*.py)
- [ ] T076 [US6] Verify test imports work: check each test file can import its corresponding module
- [ ] T077 [US6] Add pytest configuration to pyproject.toml (testpaths, python_files, python_functions)

**Checkpoint**: Test suite structure created and ready for test development

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Package metadata, documentation, git configuration, and output file organization

### Package Metadata

- [ ] T078 Create pyproject.toml with package name, version, dependencies, dev dependencies, entry points
- [ ] T079 Create requirements.txt extracting dependencies from pyproject.toml (pandas, ollama, deepeval, pyyaml)
- [ ] T080 Verify pyproject.toml is valid TOML: python -c "import tomllib; tomllib.load(open('pyproject.toml', 'rb'))"
- [ ] T081 Test package installation: pip install -e .
- [ ] T082 Verify package can be imported after installation: python -c "import syntha; print(syntha.__version__)"

### Documentation

- [ ] T083 Create README.md with project overview, features, installation, quick start, structure, configuration, development, testing
- [ ] T084 Add project structure diagram to README.md showing all 7 top-level directories
- [ ] T085 Document CLI usage for all 4 scripts in README.md with examples
- [ ] T086 Add configuration file documentation to README.md explaining each YAML file purpose

### Git Configuration

- [ ] T087 Update .gitignore to exclude __pycache__/, *.py[cod], build/, dist/, *.egg-info/, venv/, .vscode/, .idea/
- [ ] T088 Add outputs/ directory pattern to .gitignore to exclude generated files (*.jsonl, *.jsonl.meta.json)
- [ ] T089 Add .gitkeep files to outputs/ subdirectories to preserve directory structure in git
- [ ] T090 Verify .gitignore works: git status should not show outputs/ contents or Python artifacts

### Output File Organization

- [ ] T091 [P] Move campaign_rules_dataset.jsonl to outputs/datasets/ using git mv
- [ ] T092 [P] Move campaign_rules_dataset.jsonl.meta.json to outputs/datasets/ using git mv
- [ ] T093 [P] Move campaign_rules_structured.jsonl to outputs/structured/ using git mv
- [ ] T094 [P] Move campaign_rules_structured.jsonl.meta.json to outputs/structured/ using git mv
- [ ] T095 [P] Move campaign_rules_eval.jsonl to outputs/evaluations/ using git mv
- [ ] T096 [P] Move campaign_rules_eval.jsonl.meta.json to outputs/evaluations/ using git mv
- [ ] T097 [P] Move campaign_rules_passed.jsonl to outputs/filtered/ using git mv
- [ ] T098 [P] Move campaign_rules_failed.jsonl to outputs/filtered/ using git mv
- [ ] T099 Verify all output files exist in correct subdirectories using tree outputs/

### Agent Context

- [ ] T100 Verify CLAUDE.md agent context file exists with technology stack and architecture documentation

### Final Validation

- [ ] T101 Run complete import validation test from quickstart.md
- [ ] T102 Verify project structure matches proposed structure: tree -L 3 -I '__pycache__|.git|.idea|.deepeval|syn|specs'
- [ ] T103 Confirm zero Python files remain in project root: ls *.py 2>/dev/null (should show no files)
- [ ] T104 Run all success criteria checks from spec.md (SC-001 through SC-010)
- [ ] T105 Validate migration map contract: all files from contracts/migration-map.yaml are in correct locations

### Git Commit

- [ ] T106 Stage all structure and migration changes: git add src/ tests/ scripts/ configs/ data/ docs/ outputs/
- [ ] T107 Stage new files: git add pyproject.toml requirements.txt README.md .gitignore CLAUDE.md
- [ ] T108 Review git status to confirm all changes are staged correctly
- [ ] T109 Commit migration with descriptive message referencing #001-structure-migration
- [ ] T110 Verify commit with: git log -1 --stat

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup (Phase 1) completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational (Phase 2) completion
- **User Story 2 (Phase 4)**: Depends on User Story 1 (Phase 3) completion - cannot migrate files before structure exists
- **User Story 3 (Phase 5)**: Depends on User Story 2 (Phase 4) completion - cannot update imports before files are moved
- **User Story 4 (Phase 6)**: Depends on User Story 3 (Phase 5) completion - CLI scripts need working imports
- **User Story 5 (Phase 7)**: Independent of User Story 4 - can run after Foundational phase
- **User Story 6 (Phase 8)**: Independent of User Stories 4-5 - can run after Foundational phase
- **Polish (Phase 9)**: Depends on all user stories being complete

### User Story Dependencies

```
Setup (Phase 1)
    ↓
Foundational (Phase 2)
    ↓
User Story 1 (Phase 3) - Core Structure Setup
    ↓
User Story 2 (Phase 4) - File Migration
    ↓
User Story 3 (Phase 5) - Import Updates
    ↓
User Story 4 (Phase 6) - CLI Scripts
    ↓ (optional fork)
User Story 5 (Phase 7) - Config Files (can run in parallel with US6)
User Story 6 (Phase 8) - Test Suite (can run in parallel with US5)
    ↓
Polish (Phase 9) - Final validation and commit
```

**Critical Path**: Setup → Foundational → US1 → US2 → US3 → US4 → Polish

**Parallelizable**: US5 and US6 can run in parallel after US3 completes

### Within Each User Story

**User Story 1** (Core Structure):
- All directory creation tasks (T001-T011) can run in parallel
- Verification (T012) depends on all directories being created

**User Story 2** (File Migration):
- All git mv commands (T024-T035) can run in parallel
- Verification tasks (T030-T037) depend on move completion

**User Story 3** (Import Updates):
- Import search (T038) before updates
- Update tasks (T039-T041) can run in parallel
- Syntax tests (T043-T048) can run in parallel after updates
- Final validation (T049-T050) depends on all updates

**User Story 4** (CLI Scripts):
- Script creation (T051-T054) can run in parallel
- Permissions and testing sequential after creation

**User Story 5** (Config Files):
- Config creation (T062-T064) can run in parallel
- YAML validation (T065-T067) can run in parallel after creation

**User Story 6** (Test Suite):
- All test file creation (T069-T074) can run in parallel
- Verification and pytest config sequential after creation

**Polish Phase**:
- Package metadata tasks (T078-T082) sequential
- Documentation tasks (T083-T086) can run in parallel
- Git config tasks (T087-T090) sequential
- Output file moves (T091-T098) can run in parallel
- Validation tasks (T101-T105) sequential
- Git commit tasks (T106-T110) sequential

### Parallel Opportunities

**Phase 1 - Setup**: Tasks T003-T011 (9 tasks) can run in parallel after T001-T002

**Phase 2 - Foundational**: Tasks T014-T015 (2 tasks) can run in parallel after T013

**Phase 4 - User Story 2**: Tasks T024-T029 (source files, 6 tasks) and T032-T035 (data/docs, 4 tasks) can all run in parallel

**Phase 5 - User Story 3**: Tasks T039-T041 (3 tasks) can run in parallel; T043-T048 (6 tasks) can run in parallel

**Phase 6 - User Story 4**: Tasks T051-T054 (4 tasks) can run in parallel; T057-T060 (4 tasks) can run in parallel

**Phase 7 - User Story 5**: Tasks T062-T064 (3 tasks) can run in parallel; T065-T067 (3 tasks) can run in parallel

**Phase 8 - User Story 6**: Tasks T069-T074 (6 tasks) can run in parallel

**Phase 9 - Polish**: Tasks T084-T086 (3 docs tasks) can run in parallel; T091-T098 (8 output moves) can run in parallel

**Total parallel tasks**: 53 tasks marked with [P] can run in parallel within their respective phases

---

## Parallel Example: User Story 2 (File Migration)

When working on User Story 2, you can execute all file migrations in parallel:

```bash
# Launch all source file migrations together:
Task T024: "Move synthetic_generator.py to src/syntha/generator.py using git mv"
Task T025: "Move structured_extractor.py to src/syntha/extractor.py using git mv"
Task T026: "Move deepeval_adapter.py to src/syntha/evaluation/adapter.py using git mv"
Task T027: "Move deepeval_metrics.py to src/syntha/evaluation/metrics.py using git mv"
Task T028: "Move deepeval_runner.py to src/syntha/evaluation/runner.py using git mv"
Task T029: "Move filter_eval_results.py to src/syntha/evaluation/filter.py using git mv"

# Launch all data/doc migrations together:
Task T032: "Move kpi_profiles.csv to data/kpi_profiles.csv using git mv"
Task T033: "Move AGENTS.md to docs/AGENTS.md using git mv"
Task T034: "Move Story 1.1.md to docs/story_1.1.md using git mv"
Task T035: "Move Story 1.2.md to docs/story_1.2.md using git mv"
```

---

## Implementation Strategy

### MVP First (User Stories 1-3 Only)

**Minimum Viable Migration**:
1. Complete Phase 1: Setup (T001-T012) - Directory structure
2. Complete Phase 2: Foundational (T013-T017) - Package initialization
3. Complete Phase 3: User Story 1 (T018-T023) - Structure validation
4. Complete Phase 4: User Story 2 (T024-T037) - File migration
5. Complete Phase 5: User Story 3 (T038-T050) - Import updates
6. **STOP and VALIDATE**: Test imports work, files are in correct locations
7. At this point, core migration is complete - code is reorganized and functional

**Extended MVP** (add CLI and configs):
8. Complete Phase 6: User Story 4 (T051-T061) - CLI scripts
9. Complete Phase 7: User Story 5 (T062-T068) - Config files

**Full Migration**:
10. Complete Phase 8: User Story 6 (T069-T077) - Test suite
11. Complete Phase 9: Polish (T078-T110) - Package metadata, docs, final validation

### Incremental Delivery

**Stage 1: Foundation** (US1-US3)
- Directory structure created
- Files migrated with history preserved
- Imports working
- **Value**: Project is reorganized, more navigable

**Stage 2: User Experience** (US4-US5)
- CLI scripts available
- Configuration externalized
- **Value**: Users can run tools easily, configs are maintainable

**Stage 3: Quality** (US6)
- Test structure established
- **Value**: Ready for test development, clear testing strategy

**Stage 4: Polish** (Phase 9)
- Package installable
- Documentation complete
- Migration validated
- **Value**: Professional package ready for distribution

### Parallel Team Strategy

With multiple developers or parallel AI agents:

**Team A: Critical Path** (must complete first)
1. Phase 1: Setup
2. Phase 2: Foundational
3. Phase 3: User Story 1
4. Phase 4: User Story 2
5. Phase 5: User Story 3

**Team B: User Experience** (can start after Team A completes User Story 3)
1. Phase 6: User Story 4 (depends on US3 imports working)
2. Phase 7: User Story 5 (independent, can start earlier)

**Team C: Quality & Docs** (can start after Foundational)
1. Phase 8: User Story 6 (can work in parallel with Team B)
2. Phase 9 Documentation tasks (can draft early)

**Integration Point**: All teams converge at Phase 9 final validation and commit

---

## Notes

- **[P] tasks** = different files, no dependencies, safe to run in parallel
- **[Story] label** maps task to specific user story for traceability and independent testing
- **Each user story** delivers incremental value and can be validated independently
- **git mv** used throughout to preserve file history (critical for migration)
- **Verification tasks** ensure each phase completes successfully before moving forward
- **Stop at any checkpoint** to validate story independently before continuing
- **Commit strategy**: Can commit after each phase or wait until Phase 9 for single comprehensive commit
- **Avoid**: Modifying file contents during migration (focus on structure), creating files in old locations
- **Follow quickstart.md** for detailed command-line instructions for each task

---

## Success Criteria Mapping

This task list implements all 10 success criteria from spec.md:

- **SC-001**: Achieved by T049, T101 (import validation)
- **SC-002**: Preserved by using git mv and not modifying file logic
- **SC-003**: Achieved by T018-T020, T102 (structure validation)
- **SC-004**: Achieved by T031, T103 (old file cleanup verification)
- **SC-005**: Achieved by T057-T061 (CLI script testing)
- **SC-006**: Set up by Phase 8, will be achieved when tests are written
- **SC-007**: Achieved by T065-T068 (YAML validation)
- **SC-008**: Achieved by T081 (package installation test)
- **SC-009**: Achieved by T033-T035, T083-T086 (docs migration and README)
- **SC-010**: Achieved by T102 (structure clarity verification)

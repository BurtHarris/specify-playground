# Tasks: Generalize File Support and Add Central Database

**Input**: Design documents from `/specs/004-generalize-file-support/`
**Prerequisites**: plan.md (required), research.md, data-model.md, contracts/

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → If not found: ERROR "No implementation plan found"
   → Extract: tech stack, libraries, structure
2. Load optional design documents:
   → data-model.md: Extract entities → model tasks
   → contracts/: Each file → contract test task
   → research.md: Extract decisions → setup tasks
3. Generate tasks by category:
   → Setup: project init, dependencies, linting
   → Tests: contract tests, integration tests
   → Core: models, services, CLI commands
   → Integration: DB, middleware, logging
   → Polish: unit tests, performance, docs
4. Apply task rules:
   → Different files = mark [P] for parallel
   → Same file = sequential (no [P])
   → Tests before implementation (TDD)
5. Number tasks sequentially (T001, T002...)
6. Generate dependency graph
7. Create parallel execution examples
8. Validate task completeness:
   → All contracts have tests?
   → All entities have models?
   → All CLI commands implemented?
9. Return: SUCCESS (tasks ready for execution)
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Path Conventions
- **Single project**: `src/`, `tests/` at repository root
- Paths are absolute for this repository structure

## Phase 3.1: Setup
- [ ] T001 Install new Python dependencies: sqlite3, jsonschema in requirements.txt
- [ ] T002 Create database schema migration system structure in src/lib/migrations/
- [ ] T003 [P] Configure JSON Schema validation files in src/lib/schemas/

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**

### Contract Tests
- [ ] T004 [P] Contract test FileDatabase interface in tests/contract/test_file_database.py
- [ ] T005 [P] Contract test FileScanner interface in tests/contract/test_file_scanner.py
- [ ] T006 [P] Contract test CLI scan command in tests/contract/test_cli_scan.py
- [ ] T007 [P] Contract test CLI config commands in tests/contract/test_cli_config.py
- [ ] T008 [P] Contract test CLI database commands in tests/contract/test_cli_database.py

### Integration Tests
- [ ] T009 [P] Integration test database migration from YAML files in tests/integration/test_yaml_migration.py
- [ ] T010 [P] Integration test cross-scan duplicate detection in tests/integration/test_cross_scan_duplicates.py
- [ ] T011 [P] Integration test backward compatibility with existing CLI in tests/integration/test_backward_compatibility.py
- [ ] T012 [P] Integration test hash caching performance in tests/integration/test_hash_caching.py
- [ ] T013 [P] Integration test file type categorization in tests/integration/test_file_categorization.py

## Phase 3.3: Core Implementation (ONLY after tests are failing)

### Data Models
- [ ] T014 [P] FileInfo model replacing VideoFile in src/models/file_info.py
- [ ] T015 [P] DatabaseFile model for SQLite persistence in src/models/database_file.py
- [ ] T016 [P] ScanSession model for scan metadata in src/models/scan_session.py
- [ ] T017 [P] FileCategory enum and categorization logic in src/models/file_category.py

### Database Layer
- [ ] T018 FileDatabase class implementation in src/services/file_database.py
- [ ] T019 Database schema initialization and migrations in src/lib/database_migrations.py
- [ ] T020 Hash caching logic with size+mtime validation in src/services/hash_cache.py

### Scanner Refactoring
- [ ] T021 Refactor VideoFileScanner to FileScanner in src/services/file_scanner.py
- [ ] T022 Add configurable file pattern filtering to FileScanner
- [ ] T023 Integrate database hash caching into scanning process
- [ ] T024 Add file type categorization to scanning logic

### Configuration System
- [ ] T025 [P] JSON Schema definitions for configuration validation in src/lib/schemas/config_schema.json
- [ ] T026 Configuration manager with schema validation in src/lib/config_manager.py
- [ ] T027 File type configuration and pattern matching in src/lib/file_type_config.py

## Phase 3.4: CLI Integration

### Enhanced Scan Command
- [ ] T028 Update scan command with new filtering options in src/cli/scan_commands.py
- [ ] T029 Add database integration flags to scan command
- [ ] T030 Implement backward compatibility layer for existing scan usage

### New Database Commands
- [ ] T031 [P] Database status command in src/cli/database_commands.py
- [ ] T032 [P] Database migration command for YAML import
- [ ] T033 [P] Database backup and restore commands
- [ ] T034 [P] Database cleanup and optimization commands

### Enhanced Config Commands
- [ ] T035 [P] File type configuration commands in src/cli/config_commands.py
- [ ] T036 [P] Pattern management commands (include/exclude)
- [ ] T037 [P] Performance tuning configuration commands

## Phase 3.5: Integration & Migration

### Backward Compatibility
- [ ] T038 Update existing VideoFile references to use FileInfo in src/models/
- [ ] T039 Ensure existing YAML export format unchanged in src/services/result_exporter.py
- [ ] T040 Add database-less fallback mode for emergency recovery

### Performance Optimization
- [ ] T041 Implement streaming hash computation for large files in src/lib/hash_utils.py
- [ ] T042 Add database query optimization and indexing
- [ ] T043 Implement background hash computation for non-blocking UI

## Phase 3.6: Polish

### Testing & Validation
- [ ] T044 [P] Unit tests for FileInfo model in tests/unit/test_file_info.py
- [ ] T045 [P] Unit tests for FileDatabase in tests/unit/test_file_database.py
- [ ] T046 [P] Unit tests for file categorization in tests/unit/test_file_category.py
- [ ] T047 [P] Performance benchmark tests (<100ms database queries) in tests/performance/
- [ ] T048 [P] Memory usage tests for large file handling in tests/performance/

### Documentation & Final Polish
- [ ] T049 [P] Update README.md with new features and migration guide
- [ ] T050 [P] Update CLI help text and command documentation
- [ ] T051 [P] Create database schema documentation
- [ ] T052 Remove code duplication between old and new implementations
- [ ] T053 Run quickstart.md validation scenarios

## Dependencies

### Critical Path
- Setup (T001-T003) before all other tasks
- Contract tests (T004-T008) before any implementation
- Integration tests (T009-T013) before implementation
- Core models (T014-T017) before services and CLI
- Database layer (T018-T020) before scanner integration
- FileScanner (T021-T024) before CLI integration
- CLI commands (T028-T037) before final integration
- Implementation (T014-T043) before polish (T044-T053)

### Parallel Groups
```
# Setup Phase (can run in parallel)
T001, T002, T003

# Contract Tests (can run in parallel)
T004, T005, T006, T007, T008

# Integration Tests (can run in parallel)
T009, T010, T011, T012, T013

# Data Models (can run in parallel)
T014, T015, T016, T017

# CLI Commands (can run in parallel after core implementation)
T031, T032, T033, T034, T035, T036, T037

# Final Testing (can run in parallel)
T044, T045, T046, T047, T048, T049, T050, T051
```

### Sequential Dependencies
- T018 (FileDatabase) blocks T019, T020, T023
- T021 (FileScanner) blocks T022, T023, T024
- T025 (JSON Schema) blocks T026, T027
- T028 (Enhanced scan) blocks T029, T030
- T038 (VideoFile migration) blocks T039, T040

## Parallel Execution Examples

### Phase 1: Setup and Schema
```bash
# Launch setup tasks together:
Task: "Install new Python dependencies: sqlite3, jsonschema in requirements.txt"
Task: "Create database schema migration system structure in src/lib/migrations/"
Task: "Configure JSON Schema validation files in src/lib/schemas/"
```

### Phase 2: Contract Testing
```bash
# Launch contract tests together:
Task: "Contract test FileDatabase interface in tests/contract/test_file_database.py"
Task: "Contract test FileScanner interface in tests/contract/test_file_scanner.py"
Task: "Contract test CLI scan command in tests/contract/test_cli_scan.py"
Task: "Contract test CLI config commands in tests/contract/test_cli_config.py"
Task: "Contract test CLI database commands in tests/contract/test_cli_database.py"
```

### Phase 3: Core Models
```bash
# Launch model creation together:
Task: "FileInfo model replacing VideoFile in src/models/file_info.py"
Task: "DatabaseFile model for SQLite persistence in src/models/database_file.py"
Task: "ScanSession model for scan metadata in src/models/scan_session.py"
Task: "FileCategory enum and categorization logic in src/models/file_category.py"
```

## Notes
- [P] tasks = different files, no dependencies between them
- Verify ALL tests fail before implementing ANY functionality
- Commit after each completed task for atomic progress
- Database migration must preserve all existing YAML functionality
- Performance targets: <100ms database queries, >80% cache hit rate, 50%+ re-scan improvement
- Maintain 100% backward compatibility with existing CLI commands

## Task Generation Rules
*Applied during task creation*

1. **From Contracts**:
   - file_database.md → T004 (contract test)
   - file_scanner.md → T005 (contract test) 
   - cli_interface.md → T006-T008 (CLI contract tests)

2. **From Data Model**:
   - FileInfo entity → T014 (model creation)
   - DatabaseFile entity → T015 (model creation)
   - ScanSession entity → T016 (model creation)
   - FileCategory → T017 (model creation)

3. **From User Stories** (quickstart.md):
   - YAML migration → T009 (integration test)
   - Cross-scan detection → T010 (integration test)
   - Backward compatibility → T011 (integration test)

4. **Ordering**:
   - Setup → Tests → Models → Services → CLI → Polish
   - Dependencies block parallel execution
   - TDD: All tests before any implementation

## Validation Checklist
- [x] All contracts have corresponding tests (T004-T008)
- [x] All entities have model creation tasks (T014-T017)
- [x] All CLI commands have implementation tasks (T028-T037)
- [x] Backward compatibility preserved (T038-T040)
- [x] Performance requirements addressed (T041-T043, T047-T048)
- [x] Database integration complete (T018-T020, T031-T034)
- [x] Configuration system enhanced (T025-T027, T035-T037)
- [x] Documentation updated (T049-T051)

---
**Total Tasks**: 53 tasks organized in 6 phases
**Estimated Completion**: 35-40 hours of development work
**Critical Path**: Setup → Contract Tests → Models → Database → Scanner → CLI → Polish
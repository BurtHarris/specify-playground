# Tasks: Video Duplicate Scanner CLI

**Input**: Design documents from `/specs/001-build-a-cli/`
**Prerequisites**: plan.md (required), research.md, data-model.md, contracts/

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → SUCCESS: Python 3.12+ CLI tool with Click framework
   → Extract: blake2b hashing, YAML/JSON export, pathlib operations
2. Load optional design documents:
   → data-model.md: VideoFile, DuplicateGroup, PotentialMatchGroup, ScanResult, ScanMetadata
   → contracts/: CLI interface and service APIs
   → research.md: blake2b for performance, fuzzywuzzy for similarity
3. Generate tasks by category:
   → Setup: Python project, dependencies, structure
   → Tests: CLI contract tests, service tests, integration tests
   → Core: data models, scanner service, CLI implementation
   → Integration: export functionality, progress reporting
   → Polish: error handling, validation, documentation
4. Apply task rules:
   → Different files = mark [P] for parallel
   → Same file = sequential (no [P])
   → Tests before implementation (TDD)
5. Number tasks sequentially (T001, T002...)
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Path Conventions
- **Single project**: `src/`, `tests/` at repository root
- Following plan.md structure: `src/models/`, `src/services/`, `src/cli/`, `src/lib/`

## Phase 3.1: Setup
- [ ] T001 Create Python project structure: src/{models,services,cli,lib}/, tests/{unit,integration,contract}/
- [ ] T002 Initialize Python 3.12+ project with dependencies: Click, PyYAML, fuzzywuzzy, blake2b
- [ ] T003 [P] Configure pytest testing framework and project linting tools
- [ ] T004 [P] Create Python version check utility in src/lib/version_check.py

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**
- [ ] T005 [P] CLI contract test for video-dedup command in tests/contract/test_cli_interface.py
- [ ] T006 [P] CLI contract test for export functionality in tests/contract/test_export_contract.py  
- [ ] T007 [P] Service contract test for VideoFileScanner in tests/contract/test_scanner_service.py
- [ ] T008 [P] Service contract test for DuplicateDetector in tests/contract/test_duplicate_detector.py
- [ ] T009 [P] Service contract test for ResultExporter in tests/contract/test_result_exporter.py
- [ ] T010 [P] Integration test for basic duplicate detection in tests/integration/test_basic_duplicate_detection.py
- [ ] T011 [P] Integration test for JSON export in tests/integration/test_json_export.py
- [ ] T012 [P] Integration test for YAML export in tests/integration/test_yaml_export.py
- [ ] T013 [P] Integration test for fuzzy matching in tests/integration/test_fuzzy_matching.py
- [ ] T014 [P] Integration test for progress reporting in tests/integration/test_progress_reporting.py

## Phase 3.3: Core Implementation (ONLY after tests are failing)
- [ ] T015 [P] VideoFile model in src/models/video_file.py
- [ ] T016 [P] DuplicateGroup model in src/models/duplicate_group.py
- [ ] T017 [P] PotentialMatchGroup model in src/models/potential_match_group.py
- [ ] T018 [P] ScanMetadata model in src/models/scan_metadata.py
- [ ] T019 [P] ScanResult model in src/models/scan_result.py
- [ ] T020 [P] VideoFileScanner service in src/services/video_file_scanner.py
- [ ] T021 [P] DuplicateDetector service in src/services/duplicate_detector.py
- [ ] T022 [P] FuzzyMatcher service in src/services/fuzzy_matcher.py
- [ ] T023 [P] HashComputer utility in src/lib/hash_computer.py
- [ ] T024 [P] ProgressReporter utility in src/lib/progress_reporter.py
- [ ] T025 ResultExporter service in src/services/result_exporter.py
- [ ] T026 CLI main command implementation in src/cli/main.py
- [ ] T027 CLI argument parsing and validation in src/cli/arguments.py
- [ ] T028 CLI output formatting in src/cli/formatter.py

## Phase 3.4: Integration
- [ ] T029 Wire services together in main CLI application
- [ ] T030 Implement streaming hash computation for large files
- [ ] T031 Add comprehensive error handling and logging
- [ ] T032 Implement symbolic links handling logic
- [ ] T033 Add file access permission checking

## Phase 3.5: Polish  
- [ ] T034 [P] Unit tests for VideoFile validation in tests/unit/test_video_file.py
- [ ] T035 [P] Unit tests for hash computation in tests/unit/test_hash_computer.py
- [ ] T036 [P] Unit tests for fuzzy matching in tests/unit/test_fuzzy_matcher.py
- [ ] T037 [P] Unit tests for progress reporting in tests/unit/test_progress_reporter.py
- [ ] T038 [P] Performance tests for large file handling in tests/performance/test_large_files.py
- [ ] T039 [P] Cross-platform compatibility tests in tests/integration/test_cross_platform.py
- [ ] T040 [P] Memory usage optimization validation
- [ ] T041 [P] Update CLI documentation and help text
- [ ] T042 Execute quickstart.md validation scenarios

## Dependencies
- Setup (T001-T004) before everything
- Tests (T005-T014) before implementation (T015-T028)
- Models (T015-T019) before services (T020-T025)
- Services before CLI (T026-T028)
- Core implementation before integration (T029-T033)
- Integration before polish (T034-T042)

**Critical Dependencies**:
- T015 (VideoFile) blocks T020 (VideoFileScanner)
- T016,T017 (Groups) block T021 (DuplicateDetector)
- T019 (ScanResult) blocks T025 (ResultExporter)
- T020,T021,T025 block T026 (CLI main)

## Parallel Example
```bash
# Launch T015-T019 together (all models):
Task: "VideoFile model in src/models/video_file.py"
Task: "DuplicateGroup model in src/models/duplicate_group.py"  
Task: "PotentialMatchGroup model in src/models/potential_match_group.py"
Task: "ScanMetadata model in src/models/scan_metadata.py"
Task: "ScanResult model in src/models/scan_result.py"

# Launch T020-T024 together (independent services):
Task: "VideoFileScanner service in src/services/video_file_scanner.py"
Task: "DuplicateDetector service in src/services/duplicate_detector.py"
Task: "FuzzyMatcher service in src/services/fuzzy_matcher.py"
Task: "HashComputer utility in src/lib/hash_computer.py"
Task: "ProgressReporter utility in src/lib/progress_reporter.py"
```

## Notes
- [P] tasks = different files, no dependencies between them
- Verify all tests fail before implementing (TDD requirement)
- Use blake2b for file hashing as specified in research.md
- Implement YAML as primary export with JSON compatibility
- Handle Python 3.12+ version requirement validation
- Stream hash computation for memory efficiency with large video files
- Follow CLI contract specifications exactly for argument parsing
- Implement fuzzy matching with 0.8 default threshold

## Task Generation Rules Applied
1. **From Contracts**: CLI interface → T005-T006, Service APIs → T007-T009
2. **From Data Model**: 5 entities → T015-T019 (models)
3. **From Quickstart**: Test scenarios → T010-T014 (integration tests)
4. **From Research**: Technical decisions → blake2b, fuzzywuzzy, streaming

## Validation Checklist
- [x] All contracts have corresponding tests (T005-T009)
- [x] All entities have model tasks (T015-T019)
- [x] All tests come before implementation (T005-T014 → T015+)
- [x] Parallel tasks truly independent (different files)
- [x] Each task specifies exact file path
- [x] No task modifies same file as another [P] task
- [x] TDD ordering enforced (tests → models → services → CLI)
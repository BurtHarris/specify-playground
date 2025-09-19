# Tasks: OneDrive Integration MVP

**Input**: Design documents from `/specs/003-onedrive-compat-the/`
**Prerequisites**: plan.md (required), research.md, data-model.md, contracts/

## Execution Flow (MVP Focus)
```
1. Load plan.md from feature directory
   → Extract: Python 3.12+, Windows API integration, local detection only
   → MVP scope: Windows file attributes, no Graph API
2. Load design documents:
   → data-model.md: CloudFileStatus enum, VideoFile enhancement
   → contracts/: OneDriveService (local detection), VideoFileScanner enhancement
   → research.md: Windows API decisions, ctypes implementation
3. Generate MVP tasks:
   → Setup: Python version validation, Windows API dependencies
   → Tests: Contract tests for local detection, no API mocking needed
   → Core: CloudFileStatus enum, VideoFile enhancement, Windows API service
   → Integration: Scanner integration, CLI output enhancement
   → Polish: Unit tests, error handling, documentation
4. Apply task rules:
   → Different files = mark [P] for parallel
   → Same file = sequential (no [P])
   → Tests before implementation (TDD)
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions
- MVP scope: Local detection only, no Graph API integration

## Phase 3.1: Setup
- [ ] T001 Add Python 3.12+ version validation to src/cli/main.py startup
- [ ] T002 [P] Add Windows API dependencies (ctypes) to existing project structure
- [ ] T003 [P] Configure MVP-specific linting rules for Windows API code

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**
- [ ] T004 [P] Contract test for CloudFileStatus enum in tests/contract/test_cloud_file_status.py
- [ ] T005 [P] Contract test for OneDriveService.detect_cloud_status in tests/contract/test_onedrive_service_mvp.py
- [ ] T006 [P] Contract test for VideoFileScanner cloud integration in tests/contract/test_scanner_cloud_mvp.py
- [ ] T007 [P] Contract test for VideoFile.cloud_status property in tests/contract/test_video_file_cloud.py
- [ ] T008 [P] Integration test Windows API file detection in tests/integration/test_windows_api_detection.py
- [ ] T009 [P] Integration test mixed OneDrive/local scanning in tests/integration/test_mixed_directory_scan.py
- [ ] T010 [P] Integration test CLI OneDrive indicators in tests/integration/test_cli_onedrive_output.py

## Phase 3.3: Core Implementation (ONLY after tests are failing)
- [ ] T011 [P] CloudFileStatus enum in src/models/cloud_file_status.py
- [ ] T012 [P] Windows API OneDrive detection utility in src/lib/windows_onedrive_api.py
- [ ] T013 Enhance VideoFile model with cloud_status property in src/models/video_file.py
- [ ] T014 [P] OneDriveService MVP implementation in src/services/onedrive_service.py
- [ ] T015 Integrate OneDrive detection in VideoFileScanner.scan_directory in src/services/video_file_scanner.py
- [ ] T016 Add cloud file filtering logic in src/services/duplicate_detector.py
- [ ] T017 Enhance CLI output with OneDrive indicators in src/cli/main.py

## Phase 3.4: Integration
- [ ] T018 Connect OneDriveService to VideoFileScanner dependency injection
- [ ] T019 Add cloud-only file skipping logic throughout scan pipeline
- [ ] T020 Enhance ScanResult with cloud statistics tracking
- [ ] T021 Add graceful degradation for non-Windows platforms

## Phase 3.5: Polish
- [ ] T022 [P] Unit tests for Windows API error handling in tests/unit/test_windows_api_errors.py
- [ ] T023 [P] Unit tests for CloudFileStatus edge cases in tests/unit/test_cloud_file_status.py
- [ ] T024 [P] Performance tests for OneDrive detection overhead in tests/performance/test_onedrive_overhead.py
- [ ] T025 [P] Update COPILOT.md with final implementation notes
- [ ] T026 [P] Add OneDrive section to existing README.md
- [ ] T027 Remove TODO comments and validate MVP completion

## Dependencies
- Python version validation (T001) before all other tasks
- Tests (T004-T010) before implementation (T011-T017)
- CloudFileStatus enum (T011) before VideoFile enhancement (T013)
- Windows API utility (T012) before OneDriveService (T014)
- VideoFile enhancement (T013) before Scanner integration (T015)
- Core models (T011-T014) before integration (T018-T021)
- Implementation complete before polish (T022-T027)

## Parallel Example
```bash
# Launch contract tests together (T004-T007):
Task: "Contract test for CloudFileStatus enum in tests/contract/test_cloud_file_status.py"
Task: "Contract test for OneDriveService.detect_cloud_status in tests/contract/test_onedrive_service_mvp.py" 
Task: "Contract test for VideoFileScanner cloud integration in tests/contract/test_scanner_cloud_mvp.py"
Task: "Contract test for VideoFile.cloud_status property in tests/contract/test_video_file_cloud.py"

# Launch integration tests together (T008-T010):
Task: "Integration test Windows API file detection in tests/integration/test_windows_api_detection.py"
Task: "Integration test mixed OneDrive/local scanning in tests/integration/test_mixed_directory_scan.py"
Task: "Integration test CLI OneDrive indicators in tests/integration/test_cli_onedrive_output.py"

# Launch core models together (T011-T012):
Task: "CloudFileStatus enum in src/models/cloud_file_status.py"
Task: "Windows API OneDrive detection utility in src/lib/windows_onedrive_api.py"
```

## MVP Scope Notes
- **NO Graph API**: This MVP focuses only on local Windows file attribute detection
- **Windows Only**: OneDrive detection works only on Windows, gracefully degrades elsewhere
- **Local Detection**: Uses FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS via ctypes.windll.kernel32
- **Simple Status**: Only LOCAL and CLOUD_ONLY status values, no API-dependent states
- **Backward Compatible**: All existing functionality preserved, OneDrive is pure enhancement
- **Silent Operation**: Cloud-only files are skipped silently, no user notification
- **Performance**: OneDrive detection adds minimal overhead to existing scanning

## Task Generation Rules
- Each contract file → contract test task marked [P]
- Each new entity → model creation task marked [P] 
- VideoFile enhancement → single sequential task (same file)
- Scanner integration → sequential tasks (affects shared pipeline)
- Different files = parallel [P], same file = sequential
- Tests must fail before implementation begins
- MVP scope excludes all Graph API functionality

# Implementation Plan: Generalize File Support and Add Central Database

**Branch**: `004-generalize-file-support` | **Date**: September 19, 2025 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/004-generalize-file-support/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → If not found: ERROR "No feature spec at {path}"
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → Detect Project Type from context (web=frontend+backend, mobile=app+api)
   → Set Structure Decision based on project type
3. Fill the Constitution Check section based on the content of the constitution document.
4. Evaluate Constitution Check section below
   → If violations exist: Document in Complexity Tracking
   → If no justification possible: ERROR "Simplify approach first"
   → Update Progress Tracking: Initial Constitution Check
5. Execute Phase 0 → research.md
   → If NEEDS CLARIFICATION remain: ERROR "Resolve unknowns"
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, agent-specific template file (e.g., `CLAUDE.md` for Claude Code, `.github/copilot-instructions.md` for GitHub Copilot, `GEMINI.md` for Gemini CLI, `QWEN.md` for Qwen Code or `AGENTS.md` for opencode).
7. Re-evaluate Constitution Check section
   → If new violations: Refactor design, return to Phase 1
   → Update Progress Tracking: Post-Design Constitution Check
8. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
9. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 7. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary
Comprehensive refactoring to generalize the video-specific duplicate scanner into a universal file duplicate detection system with SQLite database for cross-scan analysis, hash caching, and persistent file tracking. Includes configurable file type support, database integration, JSON Schema validation, and enhanced CLI commands while maintaining full backward compatibility.

## Technical Context
**Language/Version**: Python 3.12+ (existing requirement)  
**Primary Dependencies**: Click (CLI framework), hashlib (SHA-256 hashing), pathlib (file operations), PyYAML (config/export), sqlite3 (database), json (compatibility), fuzzywuzzy (name similarity), jsonschema (validation)  
**Storage**: SQLite database + existing file system operations  
**Testing**: pytest, pytest-mock for unit testing, database fixtures  
**Target Platform**: Cross-platform (Linux, macOS, Windows)
**Project Type**: Refactoring existing CLI application (single project structure)  
**Performance Goals**: 50%+ reduction in re-scan time via hash caching, <100ms database queries, >80% cache hit rate  
**Constraints**: Maintain backward compatibility, support database-less fallback mode, atomic database operations  
**Scale/Scope**: Handle large mixed file collections (thousands of files), cross-scan duplicate detection, historical tracking

**Dependencies**: Configuration system (PR #4) - SATISFIED ✅

**User-Provided Context**: Generalize from video-only to any file type support, implement SQLite for persistent tracking, add JSON Schema validation, maintain existing CLI behavior.

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Since the constitution file is a template, applying general best practices principles:

- [x] **Library-First**: Core functionality refactored into reusable modules (FileDatabase, FileScanner, etc.) with CLI wrapper
- [x] **CLI Interface**: Text in/out protocol maintained, YAML and human-readable formats preserved  
- [x] **Test-First Development**: TDD approach with tests written before implementation of new components
- [x] **Integration Testing**: Database operations, CLI contracts, cross-scan functionality require integration tests
- [x] **Backward Compatibility**: All existing CLI commands and functionality must continue to work unchanged
- [x] **Error Handling**: Graceful handling of database corruption, file access permissions, invalid configs
- [x] **Simplicity**: Start with core generalization, avoid over-engineering, database-less fallback mode

**No Constitutional Violations Identified** - approach aligns with standard software engineering principles.

## Project Structure

### Documentation (this feature)
```
specs/[###-feature]/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
# Option 1: Single project (DEFAULT)
src/
├── models/      # Data models and domain objects (FileInfo, DuplicateGroup, ScanMetadata)
├── services/    # Core services and business logic (scanners, hashers, database access)
├── cli/         # Click-based command-line entrypoints and argument parsing
└── lib/         # Shared utilities, helpers, and small cross-cutting modules

tests/
├── contract/    # Contract/interface tests ensuring CLI/exports match the spec
├── integration/ # End-to-end tests (database + filesystem + CLI flows)
└── unit/        # Fast unit tests for individual modules and functions

<!-- Alternative project structures removed: this plan targets a single-project layout only. -->
```

**Structure Decision**: Option 1 (single project structure) - Refactoring existing CLI application, no web/mobile components detected

## Phase 0: Outline & Research
1. **No unknowns identified in Technical Context** - all requirements clearly specified in feature spec
2. **Research areas identified from spec requirements**:
   - Database migration strategy for existing users → research task
   - Performance impact assessment for large file sets → benchmarking task
   - JSON Schema design for configuration validation → patterns task
   - File type categorization approach → design task
   - Cross-platform database location strategy → research task
   - Backward compatibility testing approach → strategy task

3. **Research completed** in `research.md` with concrete decisions for all areas

**Output**: research.md with all NEEDS CLARIFICATION resolved

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

1. **Extract entities from feature spec** → `data-model.md`:
   - Entity name, fields, relationships
   - Validation rules from requirements
   - State transitions if applicable

2. **Generate API contracts** from functional requirements:
   - For each user action → endpoint
   - Use standard REST/GraphQL patterns
   - Output OpenAPI/GraphQL schema to `/contracts/`

3. **Generate contract tests** from contracts:
   - One test file per endpoint
   - Assert request/response schemas
   - Tests must fail (no implementation yet)

4. **Extract test scenarios** from user stories:
   - Each story → integration test scenario
   - Quickstart test = story validation steps

5. **Update agent file incrementally** (O(1) operation):
   - Run `.specify/scripts/bash/update-agent-context.sh copilot` for your AI assistant
   - If exists: Add only NEW tech from current plan
   - Preserve manual additions between markers
   - Update recent changes (keep last 3)
   - Keep under 150 lines for token efficiency
   - Output to repository root

**Output**: data-model.md, /contracts/*, failing tests, quickstart.md, agent-specific file

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:

1. **Database Foundation Tasks**:
   - Implement FileDatabase class with SQLite backend
   - Create database schema migration system
   - Add database management CLI commands

2. **Model Refactoring Tasks**:
   - Rename VideoFile → FileInfo with backward compatibility
   - Add file type categorization system
   - Implement configuration schema validation

3. **Service Enhancement Tasks**:
   - Refactor VideoFileScanner → FileScanner
   - Integrate hash caching with database
   - Add configurable file pattern filtering

4. **CLI Integration Tasks**:
   - Extend config commands for file types
   - Add database management commands
   - Update scan command with new options

5. **Testing & Validation Tasks**:
   - Update all existing tests for new models
   - Add database integration tests
   - Create performance benchmark tests
   - Validate backward compatibility

**Ordering Strategy**:
- TDD order: Tests before implementation
- Dependency order: Database → Models → Services → CLI
- Mark [P] for parallel execution (independent files)
- Critical path: FileDatabase → FileInfo → FileScanner → CLI integration

**Estimated Output**: 35-40 numbered, ordered tasks in tasks.md

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)  
**Phase 4**: Implementation (execute tasks.md following constitutional principles)  
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*Fill ONLY if Constitution Check has violations that must be justified*

**No constitutional violations identified** - approach follows standard software engineering principles without requiring complexity justification.


## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command)
- [x] Phase 2: Task planning complete (/plan command - describe approach only)
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved
- [x] Complexity deviations documented (none required)

---
*Based on Constitution v2.1.2 - See `/memory/constitution.md`*

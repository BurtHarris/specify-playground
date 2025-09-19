# Implementation Plan: Generalize File Support and Add Central Database

**Branch**: `004-generalize-file-support` | **Date**: September 19, 2025 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/004-generalize-file-support/spec.md`

## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [ ] Phase 0: Research complete (/plan command)
- [ ] Phase 1: Design complete (/plan command)
- [ ] Phase 2: Task planning complete (/tasks command)
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [ ] Initial Constitution Check: PASS
- [ ] Post-Design Constitution Check: PASS
- [ ] All NEEDS CLARIFICATION resolved
- [ ] Complexity deviations documented (none required)

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → SUCCESS: Feature spec loaded and analyzed
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → Project Type: Refactoring existing CLI application
   → Structure Decision: Option 1 (single project, existing structure)
3. Fill the Constitution Check section based on constitution document
4. Evaluate Constitution Check section below
   → Update Progress Tracking: Initial Constitution Check
5. Execute Phase 0 → research.md
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, agent-specific template file
7. Re-evaluate Constitution Check section
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
**Project Type**: Refactoring existing CLI application  
**Performance Goals**: 50%+ reduction in re-scan time via hash caching, <100ms database queries, >80% cache hit rate  
**Constraints**: Maintain backward compatibility, support database-less fallback mode, atomic database operations  
**Scale/Scope**: Handle large mixed file collections (thousands of files), cross-scan duplicate detection, historical tracking

**Dependencies**: Configuration system (PR #4) - SATISFIED ✅

**User-Provided Context**: Generalize from video-only to any file type support, implement SQLite for persistent tracking, add JSON Schema validation, maintain existing CLI behavior.

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**NEEDS CLARIFICATION** sections to resolve:
- Database migration strategy for existing users
- Performance impact assessment for large file sets
- JSON Schema design for configuration validation
- File type categorization approach (video, document, image, etc.)
- Cross-platform database location strategy
- Backward compatibility testing approach

Since no specific constitution file exists beyond the template, applying general best practices:
- [x] **Test-First Development**: TDD approach with tests written before implementation
- [x] **Clear CLI Interface**: Text in/out protocol with YAML and human-readable formats
- [x] **Library-First**: Core functionality as reusable modules with CLI wrapper
- [x] **Error Handling**: Graceful handling of database, file access, permissions, and invalid inputs
- [x] **Backward Compatibility**: Existing functionality must continue to work unchanged
- [x] **Database Integrity**: ACID transactions, schema migrations, corruption recovery

## Project Structure

### Documentation (this feature)
```
specs/004-generalize-file-support/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
├── spec.md             # Feature specification (existing)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root - existing structure)
```
src/
├── models/              # Add FileInfo, DatabaseFile models
├── services/            # Refactor VideoFileScanner → FileScanner
├── cli/                # Extend config commands, add database commands
└── lib/                # Add file_database.py, schema validation

tests/
├── contract/           # Update CLI contract tests
├── integration/        # Add database integration tests
└── unit/              # Update all tests for new models
```

**Structure Decision**: Option 1 (existing single project structure maintained)

## Phase 0: Outline & Research
1. **Extract unknowns from Technical Context** above:
   - Database migration strategy for existing users → research task
   - Performance impact assessment for large file sets → benchmarking task
   - JSON Schema design for configuration validation → patterns task
   - File type categorization approach → design task
   - Cross-platform database location strategy → research task
   - Backward compatibility testing approach → strategy task

2. **Generate and dispatch research agents**:
   ```
   For each unknown in Technical Context:
     Task: "Research {unknown} for generalized file duplicate detection"
   For each technology choice:
     Task: "Find best practices for {tech} in file management systems"
   ```

3. **Consolidate findings** in `research.md` using format:
   - Decision: [what was chosen]
   - Rationale: [why chosen]
   - Alternatives considered: [what else evaluated]

**Output**: research.md with all NEEDS CLARIFICATION resolved

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

1. **Extract entities from feature spec** → `data-model.md`:
   - FileInfo (replaces VideoFile), DatabaseFile, ScanSession
   - Database schema with files, scans, scan_files tables
   - Configuration schema with file type settings
   - Validation rules and relationships

2. **Define service contracts** → `contracts/`:
   - FileDatabase API contract
   - FileScanner interface contract
   - Configuration schema contract
   - CLI command contracts

3. **Create quickstart guide** → `quickstart.md`:
   - Migration from video-only to generalized usage
   - Database setup and initial configuration
   - New CLI commands and examples

**Outputs**: data-model.md, contracts/, quickstart.md

## Phase 2: Task Planning
*Prerequisites: Phase 1 complete*

**Task Generation Approach**:
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

**Output**: tasks.md with specific, actionable implementation tasks

## Implementation Phases

### Phase 1: Foundation (Critical Priority)
- Database infrastructure (FileDatabase class)
- JSON Schema validation system
- Configuration enhancement for file types
- Core model refactoring (VideoFile → FileInfo)

### Phase 2: Enhanced Scanning (High Priority)
- Remove video-specific constraints
- Database-integrated scanning with hash caching
- File type filtering and categorization
- Cross-scan duplicate detection

### Phase 3: Advanced Features (Medium Priority)
- Enhanced analytics and reporting
- Scan history management
- Global duplicate detection
- Storage optimization insights

## Risk Mitigation

### Technical Risks
- **Database Migration**: Implement backup/restore, test with existing data
- **Performance Regression**: Benchmark against current implementation
- **Cross-Platform Issues**: Test database operations on all platforms

### User Experience Risks
- **Breaking Changes**: Extensive backward compatibility testing
- **Data Loss**: Robust backup before any migrations
- **Complexity Increase**: Keep simple use cases simple

## Success Criteria

### Performance Metrics
- 50%+ reduction in scan time for re-scanned directories
- Hash cache hit rate >80% for stable file sets
- Database query time <100ms for typical operations

### Functionality Metrics
- All existing video duplicate detection functionality preserved
- Cross-scan duplicate detection working correctly
- File type filtering working for at least 5 common types (video, document, image, archive, text)

### User Experience Metrics
- No breaking changes to existing CLI workflows
- New features accessible through intuitive CLI commands
- Clear migration path for existing users
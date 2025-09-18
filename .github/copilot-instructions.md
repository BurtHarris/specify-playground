# GitHub Copilot Instructions: Video Duplicate Scanner CLI# GitHub Copilot Instructions: Video Duplicate Scanner CLI



## Project Context## Project Context

You are working on a CLI tool that scans directories for duplicate video files (mp4, mkv, mov). The tool uses a two-stage detection approach: fast file size comparison followed by hash computation for size-matched files.You are working on a CLI tool that scans directories for duplicate video files (mp4, mkv, mov). The tool uses a two-stage detection approach: fast file size comparison followed by hash computation for size-matched files.



## Technology Stack## Technology Stack

- **Language**: Python 3.12+ (requirement validated at runtime)- **Language**: Python 3.11+

- **CLI Framework**: Click for command-line interface- **CLI Framework**: Click for command-line interface

- **Core Libraries**: pathlib (file operations), hashlib (blake2b hashing), fuzzywuzzy (name similarity), json (export)- **Core Libraries**: pathlib (file operations), hashlib (SHA-256 hashing), fuzzywuzzy (name similarity), PyYAML (YAML output)

- **Testing**: pytest with pytest-mock for file system mocking- **Testing**: pytest with unittest.mock for file system mocking

- **Target**: Cross-platform CLI executable (Linux, macOS, Windows)- **Target**: Cross-platform CLI executable (Linux, macOS, Windows)



## Key Features## Key Features

- Python version check (3.12+ required) at CLI entry point- Recursive directory scanning (with optional disable)

- Recursive directory scanning (with optional disable)- Two-stage duplicate detection (size comparison → hash computation)

- Two-stage duplicate detection (size comparison → blake2b hash computation)- Fuzzy name matching for potential duplicates across extensions

- Fuzzy name matching for potential duplicates across extensions- YAML export capability (default) with JSON backward compatibility

- JSON export capability with structured schema- Progress reporting for long-running scans

- Progress reporting for long-running scans- Graceful error handling for permission issues

- Graceful error handling for permission issues- Memory-efficient processing for large video files

- Memory-efficient streaming hash computation for large video files

## Architecture Decisions

## Architecture Decisions- **Performance**: Streaming hash computation for files >100MB to minimize memory usage

- **Performance**: Blake2b hashing with streaming for files to minimize memory usage- **Error Handling**: Continue processing when individual files can't be accessed

- **Error Handling**: Continue processing when individual files can't be accessed- **Data Model**: Clear separation between confirmed duplicates (identical hashes) and potential matches (similar names)

- **Data Model**: Clear separation between confirmed duplicates (identical hashes) and potential matches (similar names)- **CLI Design**: Follow Unix conventions with clear exit codes and structured output

- **CLI Design**: Follow Unix conventions with clear exit codes and structured output

- **Version Check**: Early validation of Python 3.12+ requirement## Project Structure

```

## Project Structuresrc/

```├── models/          # VideoFile, DuplicateGroup, ScanResult classes

src/├── services/        # VideoFileScanner, hash computation, fuzzy matching

├── models/          # VideoFile, DuplicateGroup, ScanResult classes├── cli/            # Click-based command-line interface

├── services/        # VideoFileScanner, hash computation, fuzzy matching└── lib/            # Utility functions and shared logic

├── cli/            # Click-based command-line interface

└── lib/            # Utility functions and shared logictests/

├── contract/       # CLI interface contract tests

tests/├── integration/    # End-to-end functionality tests

├── contract/       # CLI interface contract tests└── unit/          # Component unit tests

├── integration/    # End-to-end functionality tests```

└── unit/          # Component unit tests

```## Development Guidelines

- **TDD Approach**: Write tests first, then implement functionality

## Development Guidelines- **Memory Efficiency**: Use generators and streaming for large file processing

- **TDD Approach**: Write tests first, then implement functionality- **Cross-Platform**: Ensure file path handling works on Windows, macOS, and Linux

- **Python Version**: Include version check in CLI entry point- **Error Recovery**: Graceful degradation when files are inaccessible

- **Memory Efficiency**: Use generators and streaming for large file processing- **Progress Reporting**: Clear feedback for long-running operations

- **Cross-Platform**: Ensure file path handling works on Windows, macOS, and Linux

- **Error Recovery**: Graceful degradation when files are inaccessible## Key Classes

- **Progress Reporting**: Clear feedback for long-running operations- `VideoFile`: Represents a video file with path, size, hash (computed on demand)

- `DuplicateGroup`: Collection of files with identical content (same hash)

## Key Classes- `PotentialMatchGroup`: Files with similar names but different extensions

- `VideoFile`: Represents a video file with path, size, hash (computed on demand)- `ScanResult`: Complete scan results with metadata and groups

- `DuplicateGroup`: Collection of files with identical content (same hash)- `VideoFileScanner`: Main service class for scanning and duplicate detection

- `PotentialMatchGroup`: Files with similar names but different extensions

- `ScanResult`: Complete scan results with metadata and groups## Testing Strategy

- `ScanMetadata`: Scan process information and timing- Mock file system operations for reliable unit tests

- `VideoFileScanner`: Main service class for scanning and duplicate detection- Create test fixtures with known duplicate/unique files

- Test error conditions (permission denied, corrupted files)

## Testing Strategy- Validate JSON export format and CLI exit codes

- Mock file system operations for reliable unit tests- Performance tests with large file sets

- Create test fixtures with known duplicate/unique files

- Test error conditions (permission denied, corrupted files)## Recent Changes

- Validate JSON export format and CLI exit codes- Completed specification phase with all requirements clarified

- Performance tests with large file sets- Finished implementation planning with research and design artifacts

- Python version requirement testing- Created data model defining core entities and relationships

- Designed CLI interface contract with detailed input/output formats

## Recent Changes- Generated quickstart guide for installation and validation

- Completed specification phase with all requirements clarified

- Finished implementation planning with research and design artifacts## Current Phase

- Created comprehensive data model defining core entities and relationships- Ready for task generation (/tasks command)

- Designed detailed CLI interface contract with input/output formats- All design artifacts completed and reviewed

- Generated service layer contracts for internal APIs- Constitution check passed

- Created quickstart guide for installation and validation- No outstanding clarifications needed

- Added Python 3.12+ version requirement with runtime checking

When implementing:

## Current Phase1. Follow the data model and CLI contracts exactly as specified

- Ready for task generation (/tasks command)2. Implement streaming hash computation for memory efficiency

- All design artifacts completed and reviewed3. Use Click framework for robust CLI argument handling

- Constitution check passed4. Include comprehensive error handling and user feedback

- No outstanding clarifications needed5. Ensure cross-platform compatibility for file operations
- Research completed with technology decisions finalized

When implementing:
1. Include Python version check at CLI entry point (sys.version_info >= (3, 12))
2. Follow the data model and CLI contracts exactly as specified
3. Implement streaming blake2b hash computation for memory efficiency
4. Use Click framework for robust CLI argument handling
5. Include comprehensive error handling and user feedback
6. Ensure cross-platform compatibility for file operations
7. Use pathlib.Path exclusively for file system operations
8. Implement fuzzy matching with configurable threshold (default 0.8)
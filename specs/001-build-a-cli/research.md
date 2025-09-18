# Research: Video Duplicate Scanner CLI

**Date**: September 17, 2025  
**Feature**: Video Duplicate Scanner CLI  
**Research Phase**: Technology decisions and best practices

## Research Questions
1. File hashing algorithm selection for video files
2. Fuzzy string matching approach for filename similarity
3. Click CLI framework patterns and best practices
4. Python packaging for CLI tools
5. Cross-platform file handling considerations
6. Progress reporting implementation for long-running operations

## Research Findings

### 1. File Hashing Algorithm Selection

**Decision**: Use `hashlib.blake2b` for file hashing

**Rationale**: 
- Blake2b provides excellent performance for large files
- Better security than MD5 while being faster than SHA-256
- Native support in Python 3.12 hashlib
- Optimal for file deduplication use cases

**Alternatives considered**:
- MD5: Fast but cryptographically broken
- SHA-256: Secure but slower for large video files
- SHA-1: Faster than SHA-256 but has known vulnerabilities

### 2. Fuzzy String Matching

**Decision**: Use `fuzzywuzzy` library with Levenshtein distance

**Rationale**:
- Mature library with good performance
- Handles filename similarity well across different extensions
- Configurable similarity thresholds
- Good handling of common video filename patterns

**Alternatives considered**:
- `difflib`: Built-in but less sophisticated for filenames
- `jellyfish`: Good performance but less filename-specific features
- Custom implementation: Too much complexity for the benefit

### 3. Click CLI Framework Patterns

**Decision**: Use Click with command groups and decorators

**Rationale**:
- Industry standard for Python CLI applications
- Excellent help generation and argument validation
- Good integration with pytest for testing
- Supports progress bars out of the box

**Best Practices**:
- Use click.echo() for output instead of print()
- Implement --verbose flag for detailed output
- Use click.ProgressBar for long operations
- Separate CLI logic from business logic

### 4. Python Packaging

**Decision**: Use `pyproject.toml` with setuptools build backend

**Rationale**:
- Modern Python packaging standard
- Better dependency management
- Supports entry points for CLI commands
- Compatible with pip and other tools

**Entry Point Configuration**:
```toml
[project.scripts]
video-dedup = "video_duplicate_scanner.cli:main"
```

### 5. Cross-Platform File Handling

**Decision**: Use `pathlib.Path` exclusively

**Rationale**:
- Object-oriented path handling
- Cross-platform compatibility built-in
- Better than os.path for modern Python
- Integrates well with file operations

**Considerations**:
- Handle case-insensitive filesystems (Windows, macOS)
- Proper symbolic link detection across platforms
- Unicode filename handling

### 6. Progress Reporting

**Decision**: Use Click's ProgressBar with file count and current file display

**Rationale**:
- Integrated with Click framework
- Handles terminal width automatically
- Good user experience for long operations

**Implementation Pattern**:
```python
with click.progressbar(files, label='Scanning') as bar:
    for file in bar:
        # Process file
        bar.update(1)
```

## Python Version Check Implementation

**Decision**: Check Python version at CLI entry point

**Implementation**:
```python
import sys

def check_python_version():
    if sys.version_info < (3, 12):
        click.echo("Error: Python 3.12 or higher is required", err=True)
        sys.exit(1)
```

**Rationale**:
- Early validation prevents confusing errors later
- Clear error message for users
- Consistent with project requirements

## Dependencies Summary

**Core Dependencies**:
- `click>=8.0.0` - CLI framework
- `fuzzywuzzy>=0.18.0` - Fuzzy string matching
- `python-Levenshtein>=0.20.0` - Performance backend for fuzzywuzzy

**Development Dependencies**:
- `pytest>=7.0.0` - Testing framework
- `pytest-mock>=3.10.0` - Mocking for tests
- `pytest-cov>=4.0.0` - Coverage reporting

## Performance Considerations

1. **Memory Usage**: 
   - Hash files in chunks to avoid loading entire files into memory
   - Use generators for file discovery to handle large directory trees

2. **I/O Optimization**:
   - Size comparison before hashing to minimize expensive operations
   - Batch file operations where possible

3. **User Experience**:
   - Progress reporting for operations taking >2 seconds
   - Graceful handling of permission errors
   - Clear error messages with suggested actions

## Security Considerations

1. **File Access**: 
   - Validate directory paths to prevent directory traversal
   - Handle permission errors gracefully
   - Don't follow symbolic links by default (configurable)

2. **Input Validation**:
   - Validate file extensions against whitelist
   - Handle malformed filenames
   - Sanitize output file paths

---

**Research Complete**: All technology decisions resolved, ready for Phase 1 Design
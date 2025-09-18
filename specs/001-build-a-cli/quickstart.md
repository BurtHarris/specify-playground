# Quickstart: Video Duplicate Scanner CLI

**Date**: September 17, 2025  
**Feature**: Video Duplicate Scanner CLI  
**Purpose**: Quick validation and testing guide

## Prerequisites

1. **Python Version**: Ensure Python 3.12+ is installed
   ```bash
   python3 --version  # Should show 3.12.0 or higher
   ```

2. **Install Dependencies**: Install the project in development mode
   ```bash
   pip install -e .
   ```

## Quick Test Scenarios

### Scenario 1: Basic Functionality Test

**Setup**: Create test directory with sample files
```bash
mkdir -p /tmp/video-test/{original,backup,downloads}
# Create dummy video files for testing
touch /tmp/video-test/original/movie1.mp4
touch /tmp/video-test/backup/movie1.mp4  
touch /tmp/video-test/downloads/video.mkv
touch /tmp/video-test/original/video.mkv
```

**Test Command**:
```bash
video-dedup /tmp/video-test
```

**Expected Result**:
- Should detect duplicate video files
- Should show progress bar
- Should display grouped duplicates
- Exit code: 0

### Scenario 2: JSON Export Test

**Test Command**:
```bash
video-dedup --export /tmp/results.json /tmp/video-test
```

**Expected Result**:
- Creates valid JSON file at `/tmp/results.json`
- JSON contains metadata, duplicate_groups, and statistics
- Exit code: 0

**Validation**:
```bash
python3 -m json.tool /tmp/results.json > /dev/null && echo "Valid JSON" || echo "Invalid JSON"
```

### Scenario 3: Error Handling Test

**Setup**: Test with non-existent directory
```bash
video-dedup /path/that/does/not/exist
```

**Expected Result**:
- Clear error message about directory not found
- Exit code: 1

### Scenario 4: Help and Version Test

**Test Commands**:
```bash
video-dedup --help
video-dedup --version
```

**Expected Result**:
- Help shows all available options
- Version shows current version number
- Exit code: 0 for both

### Scenario 5: Python Version Check Test

**Setup**: Test Python version requirement (if possible to simulate)
```bash
# This would need to be tested with Python < 3.12 if available
python3.10 -m video_duplicate_scanner.cli --help  # Should fail gracefully
```

**Expected Result**:
- Clear error message about Python version requirement
- Exit code: 3

## Automated Test Validation

### Unit Tests
```bash
pytest tests/unit/ -v
```

**Expected**: All unit tests pass

### Contract Tests  
```bash
pytest tests/contract/ -v
```

**Expected**: All CLI contract tests pass

### Integration Tests
```bash
pytest tests/integration/ -v
```

**Expected**: All end-to-end scenarios pass

## Manual Validation Checklist

### CLI Interface
- [ ] Basic scanning works with default options
- [ ] Recursive scanning can be disabled with `--no-recursive`
- [ ] JSON export creates valid output file
- [ ] Progress bar displays during long operations
- [ ] Help text is clear and complete
- [ ] Version information is accurate

### Error Handling
- [ ] Invalid directory shows appropriate error
- [ ] Permission errors are handled gracefully
- [ ] Python version check works correctly
- [ ] Malformed arguments show helpful error messages

### Output Quality
- [ ] Duplicate groups are clearly presented
- [ ] File sizes are shown in human-readable format
- [ ] Potential matches are clearly marked for review
- [ ] Summary statistics are accurate

### Performance
- [ ] Large directories scan in reasonable time
- [ ] Memory usage remains stable during scanning
- [ ] Progress reporting is responsive and accurate

## Development Workflow Validation

### 1. Code Quality
```bash
# Run linting
flake8 src/ tests/

# Run type checking  
mypy src/

# Check test coverage
pytest --cov=src tests/ --cov-report=html
```

### 2. Build and Package
```bash
# Build distribution
python -m build

# Install from built package
pip install dist/video_duplicate_scanner-*.whl
```

### 3. Documentation
- [ ] README.md includes installation and usage instructions
- [ ] CLI help text matches documented interface
- [ ] Example outputs are current and accurate

## Troubleshooting Common Issues

### Issue: Command not found after installation
**Solution**: Ensure `~/.local/bin` is in PATH, or use full path:
```bash
python -m video_duplicate_scanner.cli --help
```

### Issue: Permission denied on directories
**Solution**: Use directories the user has read access to, or run with appropriate permissions.

### Issue: No duplicates found in test data
**Solution**: Ensure test files are actually identical (same size and content), not just same names.

### Issue: JSON export fails
**Solution**: Check write permissions in target directory and available disk space.

## Performance Benchmarks

### Expected Performance Metrics
- **Small collections** (< 100 files): Complete scan in < 5 seconds
- **Medium collections** (100-1000 files): Complete scan in < 30 seconds  
- **Large collections** (1000+ files): Progress reporting active, reasonable completion time

### Memory Usage
- **Baseline**: < 50 MB for application overhead
- **Per file**: < 1 MB additional memory per 1000 files
- **Hash computation**: Streaming, no full file loading

## Success Criteria

✅ **Quickstart Complete** when:
1. All test scenarios pass
2. Manual validation checklist complete
3. No critical performance issues
4. Documentation matches actual behavior
5. Error messages are helpful and actionable

---

**Ready for Production**: CLI tool validated and ready for end-user testing
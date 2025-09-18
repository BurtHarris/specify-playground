# CLI Interface Contract

**Date**: September 17, 2025  
**Feature**: Video Duplicate Scanner CLI  
**Contract Type**: Command Line Interface

## Command Specification

### Primary Command: `video-dedup`

```bash
video-dedup [OPTIONS] DIRECTORY
```

### Required Arguments

- `DIRECTORY`: Path to directory to scan for duplicate videos
  - Type: Path
  - Required: Yes
  - Validation: Must exist and be readable

### Options

#### Core Functionality
- `--recursive / --no-recursive`: Scan subdirectories recursively (default: True)
- `--output FORMAT`: Output format (choices: json, text) (default: text)
- `--export PATH`: Export results to JSON file at specified path
- `--threshold FLOAT`: Fuzzy matching threshold (0.0-1.0) (default: 0.8)

#### Display Options
- `--verbose / --quiet`: Verbose output with detailed progress
- `--progress / --no-progress`: Show progress bar (default: True for TTY)
- `--color / --no-color`: Colorized output (default: auto-detect)

#### System Options
- `--help`: Show help message and exit
- `--version`: Show version information and exit

## Exit Codes

- `0`: Success - scan completed successfully
- `1`: Error - invalid arguments or directory not found
- `2`: Error - permission denied or file access error
- `3`: Error - Python version requirement not met
- `4`: Error - insufficient disk space for export

## Output Formats

### Text Format (Default)

```
Video Duplicate Scanner v1.0.0
Scanning: /path/to/videos (recursive)

Progress: [████████████████████████████████] 100% (150/150 files)

DUPLICATE GROUPS FOUND: 2

Group 1 (3 files, 1.5 GB total):
  /path/to/movie1.mp4 (1.5 GB, 2025-09-15 10:00:00)
  /path/to/backup/movie1.mp4 (1.5 GB, 2025-09-15 10:00:00)
  /path/to/archive/movie1_copy.mp4 (1.5 GB, 2025-09-15 10:05:00)
  → Potential savings: 3.0 GB

Group 2 (2 files, 800 MB total):
  /path/to/video.mkv (800 MB, 2025-09-10 14:30:00)
  /path/to/downloads/video.mkv (800 MB, 2025-09-10 14:30:00)
  → Potential savings: 800 MB

POTENTIAL MATCHES: 1

Similar names (85% match):
  /path/to/movie_title.mp4 (2.0 GB)
  /path/to/movie_title.mkv (1.8 GB)
  → Manual review recommended

SUMMARY:
- Total files scanned: 150
- Unique files: 145
- Duplicate files: 5 (in 2 groups)
- Potential matches: 2 (requires review)
- Total space wasted: 3.8 GB
- Scan duration: 45.2 seconds

Errors encountered: 1
- Could not read: /path/to/protected/file.mp4 (Permission denied)
```

### JSON Format (--output json)

```json
{
  "version": "1.0.0",
  "metadata": {
    "scan_date": "2025-09-17T15:30:00Z",
    "scanned_directory": "/path/to/videos",
    "duration_seconds": 45.2,
    "total_files_found": 150,
    "total_files_processed": 149,
    "recursive": true,
    "errors": ["Could not read /path/to/protected/file.mp4: Permission denied"]
  },
  "results": {
    "duplicate_groups": [...],
    "potential_matches": [...],
    "statistics": {...}
  }
}
```

## Error Handling

### Invalid Directory
```
Error: Directory '/invalid/path' does not exist or is not accessible.
Use --help for usage information.
```

### Permission Errors
```
Warning: Could not read 3 files due to permission restrictions.
Use --verbose to see detailed error list.
Continuing with accessible files...
```

### Python Version Error
```
Error: Python 3.12 or higher is required.
Current version: Python 3.10.12
Please upgrade Python to continue.
```

### Insufficient Space for Export
```
Error: Cannot write export file '/path/to/output.json'
Insufficient disk space (need 150 MB, have 50 MB available)
```

## Usage Examples

### Basic Usage
```bash
# Scan current directory
video-dedup .

# Scan specific directory
video-dedup /path/to/videos

# Scan without recursion
video-dedup --no-recursive /path/to/videos
```

### Export Results
```bash
# Export to JSON file
video-dedup --export results.json /path/to/videos

# JSON output to stdout
video-dedup --output json /path/to/videos > results.json
```

### Advanced Options
```bash
# Verbose output with custom threshold
video-dedup --verbose --threshold 0.9 /path/to/videos

# Quiet mode with no progress bar
video-dedup --quiet --no-progress /path/to/videos
```

## Contract Tests

The following test scenarios must pass:

1. **Valid directory scanning**: Returns 0 exit code and proper output
2. **Invalid directory**: Returns 1 exit code with error message
3. **Permission denied**: Returns 2 exit code with specific error
4. **Help display**: Returns 0 exit code and shows usage
5. **Version display**: Returns 0 exit code and shows version
6. **JSON export**: Creates valid JSON file with correct schema
7. **Output format validation**: Rejects invalid format options
8. **Threshold validation**: Rejects values outside 0.0-1.0 range
9. **Python version check**: Returns 3 exit code if Python < 3.12

---

**CLI Contract Complete**: Interface specification ready for implementation
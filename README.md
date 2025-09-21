# Video Duplicate Scanner CLI

A Python CLI tool that scans directories for duplicate video files (mp4, mkv, mov) with OneDrive cloud file detection and filtering capabilities. The tool uses a two-stage detection approach: fast file size comparison followed by hash computation for size-matched files.

## Features

- **OneDrive Integration**: Detects cloud-only files and local files automatically on Windows
- **Multi-format Support**: Handles MP4, MKV, and MOV video files
- **Two-stage Detection**: Fast size comparison followed by hash computation
- **Cloud Status Filtering**: Filter scans by local files, cloud-only files, or all files
- **Fuzzy Name Matching**: Identifies potential duplicates across different extensions
- **Progress Reporting**: Real-time feedback for long-running scans
- **YAML Export**: Structured output format with cloud status information
- **Cross-platform**: Works on Windows, macOS, and Linux (OneDrive detection Windows-only)

## OneDrive Cloud File Detection

The scanner automatically detects OneDrive cloud file status on Windows platforms:

- **Local Files**: Fully downloaded and available for processing
- **Cloud-Only Files**: OneDrive stubs that exist in the cloud but not locally downloaded

### Windows Requirement

OneDrive detection requires Windows and uses Windows API file attributes for cloud status detection. On non-Windows platforms, all files are treated as local.

## Installation

1. Ensure Python 3.12+ is installed
2. Clone the repository
3. Install dependencies: `pip install -r requirements.txt`

## Usage

### Basic Scanning

```bash
# Scan current directory for duplicate videos
python -m src

# Scan specific directory
python -m src /path/to/videos

# Recursive scan (default)
python -m src /path/to/videos --recursive

# Non-recursive scan (current directory only)
python -m src /path/to/videos --no-recursive
```

### CLI: logging and examples

The CLI exposes `--debug` and `--warning` flags which control the logging verbosity for the CLI and any injected components (for example, the scanner and detector). `--debug` enables DEBUG output; `--warning` reduces output to warnings and errors. If neither flag is provided, INFO is the default.

Examples:

```bash
# Scan a folder with debug logging enabled
python -m src /path/to/videos --debug

# Scan and export results to YAML
python -m src /path/to/videos --export results.yaml
```

### Cloud Status Filtering

Filter scans based on OneDrive cloud status:

```bash
# Scan only local files (skip cloud-only files)
python -m src /path/to/videos --cloud-status local

# Scan only cloud-only files
python -m src /path/to/videos --cloud-status cloud-only

# Scan all files (default)
python -m src /path/to/videos --cloud-status all
```

### Output Formats

```bash
# YAML output (default)
python -m src /path/to/videos --output results.yaml

# JSON output
python -m src /path/to/videos --output results.json

# Display results in terminal
python -m src /path/to/videos
```

## Output Format

The tool outputs structured data including cloud status information:

```yaml
metadata:
  scan_time: "2025-09-18T10:30:00Z"
  directory: "/path/to/videos"
  total_files: 150
  local_files: 120
  cloud_only_files: 30
  
duplicate_groups:
  - files:
    - path: "/path/video1.mp4"
      size: 1048576
      cloud_status: "local"
    - path: "/path/video1_copy.mp4" 
      size: 1048576
      cloud_status: "cloud_only"
      
potential_matches:
  - files:
    - path: "/path/movie.mp4"
      cloud_status: "local" 
    - path: "/path/movie.mkv"
      cloud_status: "cloud_only"
```

## Architecture

- **Two-stage Detection**: Size comparison → Hash computation for efficiency
- **OneDrive Integration**: Windows API detection for cloud file status
- **Memory Efficient**: Streaming hash computation for large files
- **Error Resilient**: Graceful handling of inaccessible files and permissions

## Performance Impact

OneDrive cloud status detection adds minimal overhead to scanning operations. The detection uses efficient Windows API calls and results are cached per file.

## Error Handling

- **Non-Windows Platforms**: OneDrive detection gracefully degrades to treating all files as local
- **Permission Errors**: Files that cannot be accessed are skipped with logging
- **API Failures**: Cloud status detection failures default to treating files as local

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines including Windows testing requirements for OneDrive features.

## Technical Implementation

OneDrive detection uses Windows FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS via ctypes to identify cloud-only files without triggering downloads. This enables efficient scanning of large OneDrive video collections.
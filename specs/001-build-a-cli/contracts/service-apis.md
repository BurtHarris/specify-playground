# Service Layer Contracts

**Date**: September 17, 2025  
**Feature**: Video Duplicate Scanner CLI  
**Contract Type**: Internal Service APIs

## VideoFileScanner Service

### Interface: `VideoFileScanner`

Responsible for discovering and processing video files in directories.

#### Methods

##### `scan_directory(directory: Path, recursive: bool = True) -> Iterator[VideoFile]`
Discovers video files in the specified directory.

**Parameters**:
- `directory`: Root directory to scan
- `recursive`: Whether to scan subdirectories

**Returns**: Iterator of VideoFile instances

**Raises**:
- `DirectoryNotFoundError`: If directory doesn't exist
- `PermissionError`: If directory is not accessible

**Contract**:
- MUST yield only files with video extensions (.mp4, .mkv, .mov)
- MUST handle symbolic links according to configuration
- MUST skip files that cannot be accessed
- MUST preserve relative order for deterministic results

##### `validate_file(file_path: Path) -> bool`
Checks if a file is a valid video file that can be processed.

**Parameters**:
- `file_path`: Path to file to validate

**Returns**: True if file is valid and accessible

**Contract**:
- MUST check file existence
- MUST check read permissions
- MUST validate file extension
- MUST NOT raise exceptions for invalid files

## DuplicateDetector Service

### Interface: `DuplicateDetector`

Responsible for identifying duplicate and similar video files.

#### Methods

##### `find_duplicates(files: List[VideoFile]) -> List[DuplicateGroup]`
Identifies duplicate files using size and hash comparison.

**Parameters**:
- `files`: List of video files to analyze

**Returns**: List of duplicate groups

**Contract**:
- MUST group files by size first (performance optimization)
- MUST compute hashes only for files with matching sizes
- MUST group files with identical hashes
- MUST return groups with at least 2 files
- MUST preserve file order within groups

##### `find_potential_matches(files: List[VideoFile], threshold: float = 0.8) -> List[PotentialMatchGroup]`
Identifies files with similar names that might be duplicates.

**Parameters**:
- `files`: List of video files to analyze
- `threshold`: Similarity threshold (0.0-1.0)

**Returns**: List of potential match groups

**Contract**:
- MUST use fuzzy string matching on filenames
- MUST ignore file extensions in comparison
- MUST only group files above threshold similarity
- MUST calculate accurate similarity scores
- MUST handle Unicode filenames correctly

## ResultExporter Service

### Interface: `ResultExporter`

Responsible for exporting scan results in various formats.

#### Methods

##### `export_json(result: ScanResult, output_path: Path) -> None`
Exports scan results to JSON format.

**Parameters**:
- `result`: Complete scan results
- `output_path`: Path where JSON file should be written

**Raises**:
- `PermissionError`: If cannot write to output path
- `DiskSpaceError`: If insufficient disk space

**Contract**:
- MUST create valid JSON according to schema
- MUST handle Unicode characters in paths
- MUST include all result data (metadata, duplicates, matches)
- MUST format file sizes in human-readable form
- MUST use ISO 8601 format for timestamps

##### `format_text_output(result: ScanResult, verbose: bool = False) -> str`
Formats scan results as human-readable text.

**Parameters**:
- `result`: Complete scan results
- `verbose`: Whether to include detailed information

**Returns**: Formatted text string

**Contract**:
- MUST include summary statistics
- MUST group duplicates clearly
- MUST show potential space savings
- MUST list errors if any occurred
- MUST format file sizes in human-readable units

## ProgressReporter Service

### Interface: `ProgressReporter`

Responsible for reporting progress during long-running operations.

#### Methods

##### `start_progress(total_items: int, label: str) -> None`
Initializes progress tracking.

**Parameters**:
- `total_items`: Total number of items to process
- `label`: Description of the operation

**Contract**:
- MUST display progress bar if stdout is a TTY
- MUST respect --no-progress CLI option
- MUST handle terminal resize gracefully

##### `update_progress(current_item: int, current_file: str = None) -> None`
Updates progress display.

**Parameters**:
- `current_item`: Current item number (1-based)
- `current_file`: Optional current file being processed

**Contract**:
- MUST update display without excessive CPU usage
- MUST truncate long filenames to fit terminal width
- MUST show percentage and estimated time remaining

##### `finish_progress() -> None`
Completes progress tracking.

**Contract**:
- MUST clear progress bar when complete
- MUST restore normal output mode

## Error Handling Contracts

### Exception Hierarchy

```python
class VideoDedupError(Exception):
    """Base exception for video deduplication errors"""

class DirectoryNotFoundError(VideoDedupError):
    """Directory does not exist or is not accessible"""

class InvalidFileError(VideoDedupError):
    """File is not a valid video file"""

class PermissionError(VideoDedupError):
    """Insufficient permissions to access file or directory"""

class DiskSpaceError(VideoDedupError):
    """Insufficient disk space for operation"""

class HashingError(VideoDedupError):
    """Error occurred during file hashing"""
```

### Error Recovery Contracts

- **File Access Errors**: Log error and continue with remaining files
- **Hashing Errors**: Mark file as inaccessible and continue
- **Export Errors**: Fail fast with clear error message
- **Directory Errors**: Fail fast if root directory inaccessible

## Performance Contracts

### Memory Usage
- MUST NOT load entire files into memory for hashing
- MUST use streaming/chunked reading for large files
- MUST limit concurrent hash operations to prevent memory exhaustion

### I/O Efficiency
- MUST minimize file system calls
- MUST batch operations where possible
- MUST provide accurate progress reporting for operations >2 seconds

### Scalability
- MUST handle directories with thousands of files
- MUST handle individual files up to multiple GB
- MUST provide responsive progress updates

---

**Service Contracts Complete**: Internal API specifications ready for implementation
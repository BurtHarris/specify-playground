# Data Model: Video Duplicate Scanner CLI

**Date**: September 17, 2025  
**Feature**: Video Duplicate Scanner CLI  
**Phase**: Design - Data Model Definition

## Core Entities

### VideoFile
Represents a single video file in the filesystem.

**Fields**:
- `path`: `pathlib.Path` - Absolute path to the video file
- `size`: `int` - File size in bytes
- `hash`: `Optional[str]` - Blake2b hash (computed lazily)
- `extension`: `str` - File extension (lowercase)
- `last_modified`: `datetime` - File modification timestamp

**Validation Rules**:
- Path must exist and be readable
- Size must be non-negative
- Extension must be one of: .mp4, .mkv, .mov
- Hash is computed only when needed (performance optimization)

**Methods**:
- `compute_hash()`: Computes and caches the file hash
- `is_accessible()`: Checks if file can be read
- `get_filename_without_extension()`: Returns filename for fuzzy matching

### DuplicateGroup
Collection of VideoFile instances that are identical (same hash).

**Fields**:
- `files`: `List[VideoFile]` - List of duplicate video files
- `hash`: `str` - Common hash of all files in group
- `total_size`: `int` - Combined size of all files
- `file_count`: `int` - Number of files in group

**Validation Rules**:
- Must contain at least 2 files
- All files must have the same hash
- Hash must be non-empty

**Methods**:
- `get_size_wasted()`: Returns total size minus one file (space that could be reclaimed)
- `get_oldest_file()`: Returns file with earliest modification date
- `get_newest_file()`: Returns file with latest modification date

### PotentialMatchGroup
Collection of VideoFile instances with similar names but potentially different content.

**Fields**:
- `files`: `List[VideoFile]` - List of potentially matching video files
- `similarity_score`: `float` - Fuzzy matching score (0.0-1.0)
- `base_name`: `str` - Common base name pattern

**Validation Rules**:
- Must contain at least 2 files
- Similarity score must be between 0.0 and 1.0
- Files must have different extensions or paths

**Methods**:
- `get_name_variants()`: Returns list of different filename patterns
- `requires_manual_review()`: Returns True if similarity score is borderline

### ScanMetadata
Information about the scanning process and results.

**Fields**:
- `start_time`: `datetime` - When scan started
- `end_time`: `Optional[datetime]` - When scan completed
- `scanned_directory`: `pathlib.Path` - Root directory that was scanned
- `total_files_found`: `int` - Total video files discovered
- `total_files_processed`: `int` - Files successfully processed
- `total_size_scanned`: `int` - Total bytes of video files scanned
- `errors`: `List[str]` - List of error messages encountered
- `recursive`: `bool` - Whether scan was recursive

**Validation Rules**:
- Start time must be set
- End time must be after start time if set
- File counts must be non-negative
- Scanned directory must be valid path

**Methods**:
- `get_duration()`: Returns scan duration as timedelta
- `get_success_rate()`: Returns ratio of processed to found files
- `add_error(message: str)`: Adds error message to list

### ScanResult
Complete results of a duplicate detection scan.

**Fields**:
- `metadata`: `ScanMetadata` - Information about the scan process
- `duplicate_groups`: `List[DuplicateGroup]` - Groups of identical files
- `potential_matches`: `List[PotentialMatchGroup]` - Groups of similar files
- `unique_files`: `List[VideoFile]` - Files with no duplicates found

**Validation Rules**:
- Metadata must be present
- No file should appear in multiple duplicate groups
- No file should appear in both duplicates and unique files

**Methods**:
- `get_total_duplicates()`: Returns count of all duplicate files
- `get_space_wasted()`: Returns total space that could be reclaimed
- `get_statistics()`: Returns summary statistics dict
- `to_json()`: Exports results to JSON format

## Data Relationships

```
ScanResult (1) → ScanMetadata (1)
ScanResult (1) → DuplicateGroup (0..n)
ScanResult (1) → PotentialMatchGroup (0..n)
ScanResult (1) → VideoFile (0..n) [unique files]

DuplicateGroup (1) → VideoFile (2..n)
PotentialMatchGroup (1) → VideoFile (2..n)
```

## State Transitions

### VideoFile States
1. **Discovered**: File found during directory scan
2. **Validated**: File accessibility and format confirmed
3. **Sized**: File size computed
4. **Hashed**: File hash computed (if needed for duplicate detection)

### ScanResult States
1. **Initializing**: Scan metadata created, no files processed
2. **Scanning**: Files being discovered and processed
3. **Analyzing**: Duplicate detection and grouping in progress
4. **Complete**: All processing finished, results available

## JSON Export Schema

```json
{
  "metadata": {
    "scan_date": "2025-09-17T15:30:00Z",
    "scanned_directory": "/path/to/videos",
    "duration_seconds": 45.2,
    "total_files_found": 150,
    "total_files_processed": 148,
    "total_size_scanned": 52428800000,
    "recursive": true,
    "errors": ["Could not read /path/to/protected/file.mp4"]
  },
  "duplicate_groups": [
    {
      "hash": "blake2b:abc123...",
      "file_count": 3,
      "total_size": 1048576000,
      "files": [
        {
          "path": "/path/to/video1.mp4",
          "size": 1048576000,
          "last_modified": "2025-09-15T10:00:00Z"
        }
      ]
    }
  ],
  "potential_matches": [
    {
      "similarity_score": 0.85,
      "base_name": "movie_title",
      "files": [
        {
          "path": "/path/to/movie_title.mp4",
          "size": 2097152000
        },
        {
          "path": "/path/to/movie_title.mkv", 
          "size": 1887436800
        }
      ]
    }
  ],
  "statistics": {
    "unique_files": 142,
    "duplicate_files": 6,
    "potential_matches": 4,
    "space_wasted_bytes": 3145728000,
    "space_wasted_human": "2.93 GB"
  }
}
```

## Implementation Notes

1. **Lazy Loading**: File hashes are computed only when needed for duplicate detection
2. **Memory Efficiency**: Use generators for large file collections
3. **Error Handling**: Each entity should handle and report its own validation errors
4. **Type Safety**: Use type hints throughout for better IDE support and runtime validation
5. **Immutability**: Consider making entities immutable after creation for thread safety

---

**Data Model Complete**: Core entities defined with validation rules and relationships
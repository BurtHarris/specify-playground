# FileScanner API Contract

**Version**: 1.0.0  
**Purpose**: Enhanced file scanning with database integration and configurable filtering

## Interface Definition

```python
from typing import List, Optional, Set, Generator
from pathlib import Path
from dataclasses import dataclass

@dataclass
class ScanConfiguration:
    """Configuration for file scanning operations."""
    include_patterns: List[str]     # Glob patterns to include
    exclude_patterns: List[str]     # Glob patterns to exclude
    min_size: Optional[int]         # Minimum file size in bytes
    max_size: Optional[int]         # Maximum file size in bytes
    recursive: bool                 # Scan subdirectories
    use_database: bool              # Enable database integration
    file_type_filter: Optional[List[str]]  # File type categories to include

class FileScanner:
    """Enhanced file scanner with database integration and filtering."""
    
    def __init__(self, 
                 config: ScanConfiguration,
                 database: Optional[FileDatabase] = None,
                 progress_callback: Optional[Callable[[int, int], None]] = None):
        """Initialize scanner with configuration.
        
        Args:
            config: Scanning configuration
            database: Optional database for hash caching
            progress_callback: Optional progress reporting function
        """
        
    def scan_directory(self, 
                      directory: Path, 
                      scan_id: Optional[str] = None) -> ScanResult:
        """Scan directory and return results.
        
        Args:
            directory: Root directory to scan
            scan_id: Optional custom scan identifier
            
        Returns:
            Complete scan results with duplicates and metadata
        """
        
    def find_files(self, directory: Path) -> Generator[Path, None, None]:
        """Find files matching scan configuration.
        
        Yields:
            File paths that match the configured filters
        """
        
    def create_file_info(self, path: Path) -> FileInfo:
        """Create FileInfo instance with metadata.
        
        Args:
            path: File path to process
            
        Returns:
            FileInfo with computed hash and metadata
        """
        
    def matches_filters(self, path: Path) -> bool:
        """Check if file matches configured filters.
        
        Args:
            path: File path to check
            
        Returns:
            True if file should be included in scan
        """
        
    def group_duplicates(self, files: List[FileInfo]) -> List[DuplicateGroup]:
        """Group files by hash to identify duplicates.
        
        Args:
            files: List of files to analyze
            
        Returns:
            Groups of files with identical content
        """
        
    def find_potential_matches(self, files: List[FileInfo]) -> List[PotentialMatchGroup]:
        """Find files with similar names using fuzzy matching.
        
        Args:
            files: List of files to analyze
            
        Returns:
            Groups of files with similar names
        """
        
    def compute_statistics(self, 
                          duplicates: List[DuplicateGroup],
                          potential_matches: List[PotentialMatchGroup],
                          total_files: int) -> ScanStatistics:
        """Compute scan statistics and insights.
        
        Args:
            duplicates: Confirmed duplicate groups
            potential_matches: Potential match groups
            total_files: Total files scanned
            
        Returns:
            Statistical summary of scan results
        """
```

## Enhanced Filtering System

```python
class FileFilter:
    """Advanced file filtering with pattern matching."""
    
    def __init__(self, config: ScanConfiguration):
        """Initialize filter with configuration."""
        
    def matches_pattern(self, path: Path, patterns: List[str]) -> bool:
        """Check if path matches any of the given patterns."""
        
    def matches_size_range(self, size: int) -> bool:
        """Check if file size is within configured range."""
        
    def matches_file_type(self, extension: str) -> bool:
        """Check if file type is in configured categories."""
        
    def is_excluded(self, path: Path) -> bool:
        """Check if path should be excluded from scan."""
```

## Database Integration

```python
class DatabaseIntegratedScanner(FileScanner):
    """Scanner with enhanced database integration."""
    
    def process_file_with_cache(self, path: Path) -> FileInfo:
        """Process file using database cache for hash lookup."""
        
    def update_scan_progress(self, scan_id: str, files_processed: int) -> None:
        """Update scan progress in database."""
        
    def detect_cross_scan_duplicates(self, current_files: List[FileInfo]) -> List[DuplicateGroup]:
        """Find duplicates across multiple scans."""
        
    def mark_orphaned_files(self, scan_id: str) -> List[Path]:
        """Identify files that no longer exist."""
```

## Progress Reporting

```python
from typing import Protocol

class ProgressReporter(Protocol):
    """Protocol for progress reporting during scans."""
    
    def on_scan_started(self, directory: Path, estimated_files: int) -> None:
        """Called when scan begins."""
        
    def on_file_processed(self, path: Path, current: int, total: int) -> None:
        """Called for each file processed."""
        
    def on_hash_computed(self, path: Path, hash: str, cache_hit: bool) -> None:
        """Called when file hash is computed or retrieved."""
        
    def on_duplicates_found(self, group_count: int, file_count: int) -> None:
        """Called when duplicate analysis completes."""
        
    def on_scan_completed(self, result: ScanResult) -> None:
        """Called when scan finishes."""
```

## Usage Examples

### Basic Scanning

```python
# Configure scanner
config = ScanConfiguration(
    include_patterns=["*.mp4", "*.pdf"],
    exclude_patterns=["*.tmp", "*.log"],
    min_size=1024,  # 1KB minimum
    recursive=True,
    use_database=True
)

# Create scanner with database
database = FileDatabase()
scanner = FileScanner(config, database)

# Scan directory
result = scanner.scan_directory(Path("/path/to/scan"))
print(f"Found {len(result.confirmed_duplicates)} duplicate groups")
```

### Advanced Filtering

```python
# File type specific scanning
config = ScanConfiguration(
    include_patterns=["*"],  # All files
    exclude_patterns=["*.tmp", "*.cache"],
    file_type_filter=["video", "document"],  # Only these categories
    min_size=10_000_000,  # 10MB minimum
    recursive=True,
    use_database=True
)

scanner = FileScanner(config, database)
result = scanner.scan_directory(directory)
```

### Progress Monitoring

```python
def progress_callback(current: int, total: int) -> None:
    percent = (current / total) * 100
    print(f"Progress: {current}/{total} ({percent:.1f}%)")

scanner = FileScanner(config, database, progress_callback)
result = scanner.scan_directory(directory)
```

## Performance Requirements

- File filtering: >10,000 files/second
- Hash computation: >100MB/second for large files
- Database lookups: >1000 queries/second
- Memory usage: <100MB for typical scans
- Progress updates: <10ms overhead per file

## Error Handling

```python
class ScanError(Exception):
    """Base exception for scanning operations."""

class FileAccessError(ScanError):
    """File cannot be read or accessed."""

class FilterError(ScanError):
    """Invalid filter configuration."""

class HashComputationError(ScanError):
    """Hash computation failed."""
```

## Thread Safety

- Scanner instances are NOT thread-safe
- Database operations use connection pooling
- Progress callbacks may be called from worker threads
- File system operations handle concurrent access gracefully

## Backward Compatibility

- Maintains VideoFileScanner interface compatibility
- Existing scan result formats remain valid
- Progressive enhancement of features
- Graceful degradation when database unavailable
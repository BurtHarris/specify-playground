# Data Model: Generalize File Support and Add Central Database

**Generated**: September 19, 2025  
**Purpose**: Define entities, relationships, and data structures for universal file duplicate detection

## Core Entities

### FileInfo (replaces VideoFile)

**Purpose**: Represents any file with metadata for duplicate detection

```python
class FileInfo:
    """Universal file representation for duplicate detection."""
    
    # Core Properties
    path: Path                          # Absolute file path
    size: int                          # File size in bytes
    hash: Optional[str]                # SHA-256 hash (computed on demand)
    modified_time: datetime            # Last modification timestamp
    
    # Categorization
    extension: str                     # File extension (without dot)
    file_type_category: Optional[str]  # Category: video, document, image, etc.
    
    # Database Integration
    database_id: Optional[int]         # Primary key in database (if persisted)
    first_seen: Optional[datetime]     # When first encountered
    last_seen: Optional[datetime]      # When last seen in a scan
    scan_count: int                    # Number of scans containing this file
    
    # Methods
    def compute_hash(self) -> str:
        """Compute SHA-256 hash using streaming for large files."""
        
    def get_category(self) -> str:
        """Determine file category based on extension and configuration."""
        
    def is_large_file(self, threshold: int = 100_000_000) -> bool:
        """Check if file exceeds large file threshold."""
        
    @property
    def relative_name(self) -> str:
        """Filename without extension for fuzzy matching."""
```

### DatabaseFile

**Purpose**: Database representation of files with persistence metadata

```python
class DatabaseFile:
    """Database entity for persistent file tracking."""
    
    id: int                           # Primary key
    path: str                         # Unique file path
    size: int                         # File size in bytes
    hash: Optional[str]               # SHA-256 hash
    file_extension: str               # File extension
    modified_time: str                # ISO timestamp
    first_seen: str                   # ISO timestamp
    last_seen: str                    # ISO timestamp
    scan_count: int                   # Number of scans
    
    def to_file_info(self) -> FileInfo:
        """Convert database record to FileInfo instance."""
        
    @classmethod
    def from_file_info(cls, file_info: FileInfo) -> 'DatabaseFile':
        """Create database record from FileInfo instance."""
```

### ScanSession

**Purpose**: Represents a single scan operation with metadata

```python
class ScanSession:
    """Metadata and configuration for a scan operation."""
    
    # Identity
    scan_id: str                      # Unique identifier (timestamp-based)
    timestamp: datetime               # Scan start time
    
    # Configuration
    directory: Path                   # Root directory scanned
    recursive: bool                   # Whether subdirectories included
    include_patterns: List[str]       # File patterns to include
    exclude_patterns: List[str]       # File patterns to exclude
    min_size: Optional[int]           # Minimum file size filter
    max_size: Optional[int]           # Maximum file size filter
    
    # Results
    total_files_scanned: int          # Number of files processed
    total_size_bytes: int             # Total size of all files
    scan_duration_seconds: float      # Time taken for scan
    duplicate_groups: int             # Number of duplicate groups found
    
    # Database Integration
    database_id: Optional[int]        # Primary key in database
    file_types: List[str]            # Extensions found during scan
```

### DuplicateGroup (enhanced)

**Purpose**: Collection of files with identical content

```python
class DuplicateGroup:
    """Group of files with identical hashes."""
    
    group_id: int                     # Unique group identifier
    hash: str                         # SHA-256 hash shared by all files
    files: List[FileInfo]            # Files in the group
    total_size: int                   # Size of each file
    
    # Analytics
    cross_scan: bool                  # Whether duplicates span multiple scans
    directories: Set[str]             # Unique directories containing duplicates
    
    def wasted_space(self) -> int:
        """Calculate wasted space (total - largest file)."""
        
    def recommended_action(self) -> str:
        """Suggest user action based on file locations."""
```

### PotentialMatchGroup (enhanced)

**Purpose**: Files with similar names but different content

```python
class PotentialMatchGroup:
    """Group of files with similar names but different hashes."""
    
    group_id: int                     # Unique group identifier
    similarity_score: float           # Fuzzy matching score (0.0-1.0)
    files: List[FileInfo]            # Files in the group
    
    # Enhanced Analysis
    name_pattern: str                 # Common name pattern
    size_variance: float              # Size difference percentage
    
    def likely_versions(self) -> bool:
        """Check if files appear to be different versions."""
```

### ScanResult (enhanced)

**Purpose**: Complete results of a scan operation

```python
class ScanResult:
    """Complete scan results with metadata and findings."""
    
    # Metadata
    metadata: ScanSession             # Scan configuration and timing
    schema_version: str               # Result format version
    scanner_version: str              # Application version
    
    # Results
    confirmed_duplicates: List[DuplicateGroup]
    potential_matches: List[PotentialMatchGroup]
    
    # Statistics
    statistics: ScanStatistics        # Aggregated statistics
    
    # Database Integration
    scan_id: str                      # Links to database scan record
    
    def to_yaml(self) -> str:
        """Serialize to YAML format."""
        
    def to_json(self) -> str:
        """Serialize to JSON format (backward compatibility)."""
        
    @classmethod
    def from_yaml(cls, yaml_content: str) -> 'ScanResult':
        """Deserialize from YAML format."""
```

### ScanStatistics

**Purpose**: Aggregated statistics and insights

```python
class ScanStatistics:
    """Statistical summary of scan results."""
    
    # Basic Counts
    duplicate_groups: int             # Number of duplicate groups
    potential_match_groups: int       # Number of potential match groups
    total_duplicate_files: int        # Total files that are duplicates
    total_wasted_space_bytes: int     # Total space that could be reclaimed
    
    # Advanced Analytics
    largest_duplicate_group: int      # Size of largest duplicate group
    most_common_extensions: List[Tuple[str, int]]  # Extension frequency
    directory_with_most_duplicates: str            # Hotspot analysis
    
    # Performance Metrics
    cache_hit_rate: float            # Hash cache effectiveness
    files_processed_per_second: float # Scan performance
    
    def efficiency_report(self) -> str:
        """Generate human-readable efficiency summary."""
```

## Database Schema

### Files Table

```sql
CREATE TABLE files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT UNIQUE NOT NULL,
    size INTEGER NOT NULL,
    hash TEXT,
    file_extension TEXT NOT NULL,
    modified_time TEXT NOT NULL,        -- ISO 8601 format
    first_seen TEXT NOT NULL,           -- ISO 8601 format
    last_seen TEXT NOT NULL,            -- ISO 8601 format
    scan_count INTEGER DEFAULT 1,
    
    -- Indexes for performance
    INDEX idx_files_path ON files(path),
    INDEX idx_files_hash ON files(hash),
    INDEX idx_files_size ON files(size),
    INDEX idx_files_extension ON files(file_extension),
    INDEX idx_files_composite ON files(size, hash)
);
```

### Scans Table

```sql
CREATE TABLE scans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_id TEXT UNIQUE NOT NULL,
    directory TEXT NOT NULL,
    timestamp TEXT NOT NULL,            -- ISO 8601 format
    file_count INTEGER NOT NULL,
    duplicate_groups INTEGER NOT NULL,
    total_size INTEGER NOT NULL,
    scan_duration REAL NOT NULL,        -- Seconds
    file_types TEXT,                    -- JSON array of extensions
    
    -- Configuration
    recursive BOOLEAN NOT NULL DEFAULT 1,
    include_patterns TEXT,              -- JSON array
    exclude_patterns TEXT,              -- JSON array
    min_size INTEGER,
    max_size INTEGER,
    
    INDEX idx_scans_timestamp ON scans(timestamp),
    INDEX idx_scans_directory ON scans(directory)
);
```

### Scan Files Junction Table

```sql
CREATE TABLE scan_files (
    scan_id TEXT NOT NULL,
    file_id INTEGER NOT NULL,
    hash_at_scan TEXT,                  -- Hash at time of scan
    
    FOREIGN KEY (file_id) REFERENCES files(id),
    FOREIGN KEY (scan_id) REFERENCES scans(scan_id),
    PRIMARY KEY (scan_id, file_id),
    
    INDEX idx_scan_files_scan ON scan_files(scan_id),
    INDEX idx_scan_files_file ON scan_files(file_id)
);
```

## Configuration Schema

### File Type Categories

```yaml
file_type_settings:
  video:
    extensions: ["mp4", "mkv", "avi", "mov", "wmv", "flv"]
    large_file_threshold: 500000000  # 500MB
    description: "Video files"
    
  document:
    extensions: ["pdf", "doc", "docx", "txt", "rtf", "odt"]
    large_file_threshold: 50000000   # 50MB
    description: "Document files"
    
  image:
    extensions: ["jpg", "jpeg", "png", "gif", "bmp", "tiff"]
    large_file_threshold: 10000000   # 10MB
    description: "Image files"
    
  archive:
    extensions: ["zip", "rar", "7z", "tar", "gz", "bz2"]
    large_file_threshold: 100000000  # 100MB
    description: "Archive files"
    
  text:
    extensions: ["txt", "md", "rst", "log", "csv", "json"]
    large_file_threshold: 1000000    # 1MB
    description: "Plain text files"
```

## Validation Rules

### File Path Validation

- Must be absolute path
- Must exist on filesystem (for current scans)
- Must be readable by current user
- Path length < 4096 characters (cross-platform limit)

### Hash Validation

- Must be valid SHA-256 hex string (64 characters)
- Computed using streaming algorithm for files >100MB
- Cached in database with file size + modification time composite key

### Configuration Validation

- File patterns must be valid glob expressions
- Size limits must be positive integers
- Similarity thresholds must be 0.0-1.0
- Extensions must not include leading dot

### Database Integrity

- Foreign key constraints enforced
- Unique constraints on file paths and scan IDs
- Timestamps must be valid ISO 8601 format
- File sizes must be non-negative

## State Transitions

### File Lifecycle

```
NEW → SCANNED → CACHED → STALE → REMOVED
  ↓      ↓        ↓       ↓
  └─── DATABASE_TRACKED ──┘
```

### Scan Lifecycle

```
INITIATED → SCANNING → PROCESSING → COMPLETED → STORED
    ↓          ↓           ↓           ↓         ↓
    └─────── ERROR_RECOVERY ──────────┘         └─→ EXPORTED
```

## Performance Considerations

### Indexing Strategy

- Composite indexes on (size, hash) for duplicate detection
- Path index for file lookup and existence checking
- Timestamp indexes for historical queries
- Extension index for file type filtering

### Memory Management

- Streaming hash computation for large files
- Lazy loading of file content
- Batch database operations
- Generator-based file iteration

### Caching Strategy

- Hash caching based on size + modification time
- Configuration caching for repeated scans
- Database connection pooling
- File metadata caching during scan

---

**Data Model Complete**: All entities, relationships, and schemas defined for implementation.
# FileDatabase API Contract

**Version**: 1.0.0  
**Purpose**: SQLite-backed persistent file tracking and hash caching

## Interface Definition

```python
from typing import List, Optional, Tuple
from pathlib import Path
from datetime import datetime

class FileDatabase:
    """SQLite database for persistent file tracking and cross-scan analysis."""
    
    def __init__(self, db_path: Optional[Path] = None):
        """Initialize database connection.
        
        Args:
            db_path: Custom database file path (None uses platform default)
        """
        
    def initialize_schema(self) -> None:
        """Create database tables and indexes if they don't exist."""
        
    def migrate_schema(self, target_version: str) -> None:
        """Migrate database schema to target version."""
        
    # File Operations
    def get_file_by_path(self, path: Path) -> Optional[DatabaseFile]:
        """Retrieve file record by path."""
        
    def add_or_update_file(self, file_info: FileInfo) -> int:
        """Insert new file or update existing record.
        
        Returns:
            Database ID of the file record
        """
        
    def get_cached_hash(self, path: Path, size: int, modified_time: datetime) -> Optional[str]:
        """Get cached hash if file hasn't changed."""
        
    def update_hash(self, file_id: int, hash: str) -> None:
        """Update hash for existing file record."""
        
    def mark_file_seen(self, file_id: int, scan_id: str) -> None:
        """Mark file as seen in current scan."""
        
    # Scan Operations
    def create_scan_record(self, scan_session: ScanSession) -> None:
        """Create new scan record in database."""
        
    def get_scan_history(self, directory: Path, limit: int = 10) -> List[ScanSession]:
        """Get recent scans for a directory."""
        
    def get_scan_by_id(self, scan_id: str) -> Optional[ScanSession]:
        """Retrieve scan record by ID."""
        
    # Cross-Scan Analysis
    def find_global_duplicates(self, hash: str) -> List[DatabaseFile]:
        """Find all files with the same hash across all scans."""
        
    def find_orphaned_files(self, current_scan_id: str) -> List[DatabaseFile]:
        """Find files that exist in database but not in current scan."""
        
    def get_file_movement_history(self, hash: str) -> List[Tuple[str, Path, datetime]]:
        """Track file movements across scans."""
        
    # Statistics and Analytics
    def get_storage_statistics(self) -> Dict[str, Any]:
        """Get storage usage and duplicate statistics."""
        
    def get_cache_hit_rate(self) -> float:
        """Calculate hash cache effectiveness."""
        
    def get_scan_performance_metrics(self, scan_id: str) -> Dict[str, float]:
        """Get performance metrics for a scan."""
        
    # Maintenance
    def cleanup_old_records(self, older_than_days: int) -> int:
        """Remove old scan records and orphaned files."""
        
    def vacuum_database(self) -> None:
        """Reclaim space from deleted records."""
        
    def backup_database(self, backup_path: Path) -> None:
        """Create database backup."""
        
    def verify_integrity(self) -> List[str]:
        """Check database integrity and return any issues."""
```

## Error Handling

```python
class DatabaseError(Exception):
    """Base exception for database operations."""
    
class SchemaVersionError(DatabaseError):
    """Database schema version incompatibility."""
    
class DatabaseCorruptionError(DatabaseError):
    """Database file is corrupted or unreadable."""
    
class MigrationError(DatabaseError):
    """Schema migration failed."""
```

## Usage Examples

### Basic File Tracking

```python
# Initialize database
db = FileDatabase()
db.initialize_schema()

# Check for cached hash
cached_hash = db.get_cached_hash(file_path, file_size, modified_time)
if cached_hash:
    file_info.hash = cached_hash
else:
    file_info.hash = file_info.compute_hash()
    db.update_hash(file_id, file_info.hash)

# Track file in current scan
file_id = db.add_or_update_file(file_info)
db.mark_file_seen(file_id, scan_id)
```

### Cross-Scan Duplicate Detection

```python
# Find global duplicates for a hash
global_duplicates = db.find_global_duplicates(file_hash)
if len(global_duplicates) > 1:
    print(f"File exists in {len(global_duplicates)} locations")
    
# Track file movements
movements = db.get_file_movement_history(file_hash)
for scan_id, path, timestamp in movements:
    print(f"{timestamp}: {path} (scan {scan_id})")
```

## Performance Requirements

- Database initialization: <1 second
- File lookup by path: <10ms
- Hash cache lookup: <5ms
- Batch file operations: >1000 files/second
- Cross-scan queries: <100ms for typical datasets

## Data Integrity

- Foreign key constraints enforced
- Atomic transactions for multi-table operations
- Automatic rollback on constraint violations
- Regular integrity checks during maintenance

## Compatibility

- SQLite 3.35+ required
- WAL mode for concurrent read access
- Platform-agnostic file paths (using pathlib)
- UTF-8 encoding for all text data
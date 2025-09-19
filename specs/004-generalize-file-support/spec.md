# Spec 004: Generalize File Support and Add Central Database

**Type:** Technical Refactoring  
**Priority:** High  
**Status:** Planning  
**Dependencies:** Config System (PR #4)

## Problem Statement

The current system is hard-coded for video files only, limiting its utility and market appeal. Additionally, each scan is isolated with no memory of previous scans, missing opportunities for cross-scan duplicate detection and performance optimization through hash caching.

## Technical Motivation

1. **Limited Scope**: Video-specific naming and logic restricts the tool to a niche use case
2. **Performance Issues**: Re-computing hashes for unchanged files across scans is inefficient
3. **Missed Duplicates**: Files moved between directories won't be detected as duplicates across different scans
4. **No Historical Context**: Users can't track file movement or build insights over time

## Goals

### Primary Objectives

- **Generalize Architecture**: Remove video-specific constraints to support any file type
- **Implement Central Database**: Add SQLite database for cross-scan file tracking and hash caching
- **Enhance Performance**: Cache computed hashes to avoid recomputation
- **Enable Cross-Scan Analysis**: Detect duplicates across different scan sessions

### Secondary Objectives

- **Improve User Experience**: Add file type filtering and size-based constraints
- **Add Analytics**: Provide insights on storage usage and duplicate patterns
- **Maintain Backward Compatibility**: Ensure existing functionality continues to work

## Solution Architecture

### Core Component Refactoring

**Current Architecture:**

```text
VideoFile → VideoFileScanner → DuplicateDetector → ResultExporter
```

**Target Architecture:**

```text
FileItem → FileScanner → DuplicateDetector → ResultExporter
                ↓               ↓
            FileDatabase ← ConfigManager
```

### Database Schema Design

```sql
-- Central file tracking
CREATE TABLE files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT UNIQUE NOT NULL,
    size INTEGER NOT NULL,
    hash TEXT,
    file_extension TEXT,
    modified_time TEXT NOT NULL,
    first_seen TEXT NOT NULL,
    last_seen TEXT NOT NULL,
    scan_count INTEGER DEFAULT 1
);

-- Scan metadata
CREATE TABLE scans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_id TEXT UNIQUE NOT NULL,
    directory TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    file_count INTEGER NOT NULL,
    duplicate_groups INTEGER NOT NULL,
    total_size INTEGER NOT NULL,
    scan_duration REAL NOT NULL,
    file_types TEXT  -- JSON array of extensions
);

-- Many-to-many relationship
CREATE TABLE scan_files (
    scan_id TEXT NOT NULL,
    file_id INTEGER NOT NULL,
    FOREIGN KEY (file_id) REFERENCES files(id),
    FOREIGN KEY (scan_id) REFERENCES scans(scan_id),
    PRIMARY KEY (scan_id, file_id)
);
```

### Configuration Enhancement

```yaml
# ~/.config/duplicate-scanner/config.yaml
default_file_patterns:
  - "*.mp4"  # videos
  - "*.pdf"  # documents  
  - "*.jpg"  # images

exclude_patterns:
  - "*.tmp"
  - "*.log"
  - "*.cache"

file_type_settings:
  video:
    extensions: ["mp4", "mkv", "avi", "mov"]
    large_file_threshold: 500000000  # 500MB
  documents:
    extensions: ["pdf", "doc", "docx", "txt"] 
    large_file_threshold: 50000000   # 50MB
  images:
    extensions: ["jpg", "jpeg", "png", "gif"]
    large_file_threshold: 10000000   # 10MB

# Database settings
database:
  enabled: true
  cache_hashes: true
  max_cache_age_days: 30
```

## Implementation Plan

### Phase 1: Foundation (Critical Priority)

1. **Rename Core Components**
   - `VideoFile` → `FileItem`
   - `VideoFileScanner` → `FileScanner`
   - Update all imports and references
   - Update class documentation and comments

2. **Create JSON Schema Definitions**
   - Define JSON Schema for configuration YAML format
   - Define JSON Schema for scan result YAML format  
   - Add schema validation to YAML loading/saving operations
   - Generate documentation from schemas

3. **Implement Database Infrastructure**
   - Create `FileDatabase` class with SQLite backend
   - Implement schema initialization and migrations
   - Add core CRUD operations for files and scans
   - Create database management CLI commands

4. **Integrate Configuration System** *(depends on PR #4)*
   - Extend config to include database settings
   - Add file type configuration support
   - Implement platform-specific database location

### Phase 2: Enhanced Scanning (High Priority)

1. **Remove Video-Specific Constraints**
   - Generalize file extension handling
   - Remove hard-coded video extensions
   - Update CLI help text and documentation

2. **Add File Type Filtering**
   - Implement `--include` and `--exclude` patterns
   - Add `--min-size` and `--max-size` options
   - Create file type categorization system

3. **Database-Integrated Scanning**
   - Modify `FileScanner` to check database for cached hashes
   - Implement incremental scanning logic
   - Store scan results in database
   - Add cross-scan duplicate detection

### Phase 3: Advanced Features (Medium Priority)

1. **Per-Scan Result Files**
   - Design YAML schema for individual scan results
   - Implement result persistence in config directory
   - Add scan history management

2. **Enhanced Analytics and Reporting**
   - Implement global duplicate detection
   - Add file movement tracking
   - Create storage optimization insights
   - Add scan comparison functionality

## Technical Specifications

### API Changes

**FileItem Class (formerly VideoFile):**

```python
class FileItem:
    """Represents any file with metadata for duplicate detection."""
    
    def __init__(self, path: Path, file_type_category: Optional[str] = None):
        self.path = path
        self.file_type_category = file_type_category  # 'video', 'document', 'image', etc.
        # ... existing properties
    
    @property
    def extension(self) -> str:
        """File extension without the dot."""
        return self.path.suffix.lower().lstrip('.')
```

**FileScanner Class (formerly VideoFileScanner):**

```python
class FileScanner:
    """Scans directories for files with configurable filtering."""
    
    def __init__(self, 
                 include_patterns: List[str] = None,
                 exclude_patterns: List[str] = None,
                 min_size: Optional[int] = None,
                 max_size: Optional[int] = None,
                 use_database: bool = True):
        # ... initialization
    
    def scan_directory(self, directory: Path, scan_id: str) -> ScanResult:
        """Scan directory with database integration and filtering."""
        # ... implementation
```

**New CLI Commands:**

```bash
# Enhanced scanning with filtering
duplicate-scanner scan /path --include "*.pdf,*.doc" --min-size 1MB

# Database management
duplicate-scanner database stats
duplicate-scanner database history /path/to/file.pdf
duplicate-scanner database find-global-duplicates
duplicate-scanner database cleanup --older-than 30d

# Scan history
duplicate-scanner results list
duplicate-scanner results show scan_20250919_143022
duplicate-scanner results diff scan_A scan_B
```

## Migration Strategy

### Backward Compatibility

- Existing CLI commands continue to work unchanged
- Default file patterns include video extensions for seamless transition
- Existing scan results remain valid

### Data Migration

- First run creates database and populates from existing scan files
- Graceful handling of missing database (falls back to current behavior)
- Optional migration command to import historical scan data

### Testing Strategy

- Unit tests for all refactored components
- Integration tests for database operations
- Performance tests for large file sets
- Backward compatibility tests

## Risk Mitigation

### Technical Risks

- **Database Corruption**: Implement backup/restore functionality
- **Performance Regression**: Benchmark against current implementation
- **Cross-Platform Issues**: Test on Windows, macOS, Linux

### User Experience Risks

- **Breaking Changes**: Maintain CLI compatibility during transition
- **Data Loss**: Implement robust backup before migrations
- **Complexity Increase**: Keep simple use cases simple

## Success Criteria

### Performance Metrics

- 50%+ reduction in scan time for re-scanned directories
- Hash cache hit rate >80% for stable file sets
- Database query time <100ms for typical operations

### Functionality Metrics

- All existing video duplicate detection functionality preserved
- Cross-scan duplicate detection working correctly
- File type filtering working for at least 5 common types

### User Experience Metrics

- No breaking changes to existing CLI workflows
- New features accessible through intuitive CLI commands
- Clear migration path for existing users

## Dependencies

- **PR #4**: Configuration system must be merged first
- **Python 3.12+**: SQLite support and pathlib improvements
- **PyYAML**: For configuration and scan result files
- **Click**: Enhanced CLI argument handling

## Timeline Estimate

- **Phase 1**: 2-3 weeks (Foundation)
- **Phase 2**: 2-3 weeks (Enhanced Scanning)
- **Phase 3**: 1-2 weeks (Advanced Features)
- **Total**: 5-8 weeks for complete implementation

## Future Considerations

### Potential Extensions

- **Cloud Storage Integration**: OneDrive, Google Drive duplicate detection
- **GUI Application**: Desktop interface using the same core libraries
- **API Server**: REST API for programmatic access
- **Plugins**: Extensible architecture for custom file types

### Technology Evolution

- **Alternative Databases**: PostgreSQL support for enterprise use
- **Distributed Scanning**: Multi-machine scanning coordination
- **Machine Learning**: Content-based duplicate detection beyond hashing

## JSON Schema Definitions

### Configuration Schema

The configuration file format will be defined using JSON Schema to ensure consistency and enable validation:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Duplicate Scanner Configuration",
  "type": "object",
  "properties": {
    "fuzzy_threshold": {
      "type": "number",
      "minimum": 0.0,
      "maximum": 1.0,
      "default": 0.8,
      "description": "Fuzzy matching threshold for potential duplicates"
    },
    "recursive_scan": {
      "type": "boolean", 
      "default": true,
      "description": "Scan subdirectories recursively by default"
    },
    "default_file_patterns": {
      "type": "array",
      "items": {"type": "string"},
      "description": "Default file patterns to include in scans"
    },
    "exclude_patterns": {
      "type": "array", 
      "items": {"type": "string"},
      "description": "File patterns to exclude from scans"
    },
    "file_type_settings": {
      "type": "object",
      "patternProperties": {
        "^[a-z_]+$": {
          "type": "object",
          "properties": {
            "extensions": {
              "type": "array",
              "items": {"type": "string"}
            },
            "large_file_threshold": {
              "type": "integer",
              "minimum": 0
            }
          },
          "required": ["extensions"]
        }
      }
    },
    "database": {
      "type": "object",
      "properties": {
        "enabled": {"type": "boolean", "default": true},
        "cache_hashes": {"type": "boolean", "default": true},
        "max_cache_age_days": {"type": "integer", "minimum": 1, "default": 30}
      }
    }
  }
}
```

### Scan Results Schema

Individual scan result files will follow this schema:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Duplicate Scanner Results",
  "type": "object",
  "required": ["metadata", "confirmed_duplicates", "potential_matches", "statistics"],
  "properties": {
    "schema_version": {
      "type": "string",
      "pattern": "^\\d+\\.\\d+\\.\\d+$",
      "description": "Schema version for compatibility"
    },
    "metadata": {
      "type": "object",
      "required": ["scan_id", "timestamp", "directory"],
      "properties": {
        "scan_id": {"type": "string"},
        "timestamp": {"type": "string", "format": "date-time"},
        "directory": {"type": "string"},
        "recursive": {"type": "boolean"},
        "total_files_scanned": {"type": "integer", "minimum": 0},
        "total_size_bytes": {"type": "integer", "minimum": 0},
        "scan_duration_seconds": {"type": "number", "minimum": 0},
        "scanner_version": {"type": "string"}
      }
    },
    "confirmed_duplicates": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["group_id", "hash", "files"],
        "properties": {
          "group_id": {"type": "integer"},
          "hash": {"type": "string"},
          "total_size": {"type": "integer", "minimum": 0},
          "files": {
            "type": "array",
            "minItems": 2,
            "items": {
              "type": "object",
              "required": ["path", "size"],
              "properties": {
                "path": {"type": "string"},
                "size": {"type": "integer", "minimum": 0},
                "modified": {"type": "string", "format": "date-time"}
              }
            }
          }
        }
      }
    },
    "potential_matches": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["group_id", "similarity_score", "files"],
        "properties": {
          "group_id": {"type": "integer"},
          "similarity_score": {"type": "number", "minimum": 0, "maximum": 1},
          "files": {
            "type": "array",
            "minItems": 2,
            "items": {
              "type": "object",
              "required": ["path", "size"],
              "properties": {
                "path": {"type": "string"},
                "size": {"type": "integer", "minimum": 0}
              }
            }
          }
        }
      }
    },
    "statistics": {
      "type": "object",
      "required": ["duplicate_groups", "potential_match_groups"],
      "properties": {
        "duplicate_groups": {"type": "integer", "minimum": 0},
        "potential_match_groups": {"type": "integer", "minimum": 0},
        "total_duplicate_files": {"type": "integer", "minimum": 0},
        "total_wasted_space_bytes": {"type": "integer", "minimum": 0}
      }
    }
  }
}
```

### Schema Implementation

- **Validation**: Use `jsonschema` library for runtime validation
- **Documentation**: Generate markdown docs from schema
- **Testing**: Validate all YAML files against schema in tests
- **Migration**: Include schema version for future compatibility

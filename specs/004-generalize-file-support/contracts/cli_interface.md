# CLI Commands Contract

**Version**: 1.0.0  
**Purpose**: Extended command-line interface for generalized file duplicate detection

## Enhanced Scan Command

### Basic Usage

```bash
# Enhanced video scanning (backward compatible)
duplicate-scanner scan /path/to/videos

# Generalized file scanning
duplicate-scanner scan /path/to/files --include "*.pdf,*.doc,*.txt"

# Size-based filtering
duplicate-scanner scan /path --min-size 1MB --max-size 1GB

# File type filtering
duplicate-scanner scan /path --type video,document,image
```

### Advanced Options

```bash
# Database integration
duplicate-scanner scan /path --use-database --cache-hashes

# Pattern filtering
duplicate-scanner scan /path \
  --include "*.mp4,*.mkv" \
  --exclude "*.tmp,*.log,**/cache/**"

# Output format options
duplicate-scanner scan /path --output results.yaml --format yaml
duplicate-scanner scan /path --output results.json --format json
```

### Command Specification

```
duplicate-scanner scan DIRECTORY [OPTIONS]

Arguments:
  DIRECTORY    Directory to scan for duplicates

Options:
  --include PATTERNS      Comma-separated file patterns to include (glob syntax)
  --exclude PATTERNS      Comma-separated file patterns to exclude (glob syntax)
  --min-size SIZE         Minimum file size (e.g., 1KB, 10MB, 1GB)
  --max-size SIZE         Maximum file size (e.g., 1KB, 10MB, 1GB)
  --type CATEGORIES       File type categories: video,document,image,archive,text
  --recursive/--no-recursive    Scan subdirectories (default: recursive)
  --use-database/--no-database  Enable database integration (default: enabled)
  --cache-hashes/--no-cache     Cache computed hashes (default: enabled)
  --output FILE           Output file path (default: stdout)
  --format FORMAT         Output format: yaml,json,human (default: yaml)
  --scan-id ID           Custom scan identifier
  --progress/--no-progress      Show progress bar (default: enabled)
  --verbose, -v          Verbose output
  --quiet, -q            Suppress non-essential output
```

## Database Management Commands

### Database Status

```bash
# Database information
duplicate-scanner database status
duplicate-scanner database info

# Output example:
Database: /home/user/.local/share/duplicate-scanner/files.db
Size: 2.3 MB
Files tracked: 15,420
Scans recorded: 127
Cache hit rate: 87.3%
Last cleanup: 2025-09-15
```

### Database Maintenance

```bash
# Cleanup old records
duplicate-scanner database cleanup --older-than 30d
duplicate-scanner database cleanup --orphaned-files

# Database optimization
duplicate-scanner database vacuum
duplicate-scanner database reindex

# Backup and restore
duplicate-scanner database backup /path/to/backup.db
duplicate-scanner database restore /path/to/backup.db
```

### File History and Analysis

```bash
# File movement tracking
duplicate-scanner database history /path/to/file.mp4

# Global duplicate search
duplicate-scanner database find-duplicates --hash SHA256_HASH
duplicate-scanner database find-duplicates --path /path/to/file.mp4

# Storage statistics
duplicate-scanner database stats --directory /path
duplicate-scanner database stats --global
```

## Configuration Commands

### Configuration Management

```bash
# View current configuration
duplicate-scanner config show
duplicate-scanner config show --file-types

# Edit configuration
duplicate-scanner config edit
duplicate-scanner config set fuzzy_threshold 0.85
duplicate-scanner config set database.enabled true

# File type management
duplicate-scanner config add-type custom_type --extensions "*.cust,*.data"
duplicate-scanner config remove-type custom_type
duplicate-scanner config list-types
```

### Configuration Schema

```bash
# Validate configuration
duplicate-scanner config validate
duplicate-scanner config validate --file /path/to/config.yaml

# Generate default configuration
duplicate-scanner config init --overwrite
duplicate-scanner config export --format yaml > config.yaml
```

## Scan History Commands

### Viewing Results

```bash
# List recent scans
duplicate-scanner results list
duplicate-scanner results list --directory /path
duplicate-scanner results list --limit 20

# Show specific scan
duplicate-scanner results show SCAN_ID
duplicate-scanner results show latest
duplicate-scanner results show latest --directory /path

# Export scan results
duplicate-scanner results export SCAN_ID --format json
duplicate-scanner results export SCAN_ID --output results.yaml
```

### Scan Comparison

```bash
# Compare two scans
duplicate-scanner results diff SCAN_ID_1 SCAN_ID_2
duplicate-scanner results diff latest previous

# Track changes over time
duplicate-scanner results timeline /path/to/directory
duplicate-scanner results changes --since "2025-09-01"
```

## Advanced Analysis Commands

### Global Duplicate Detection

```bash
# Find duplicates across all scans
duplicate-scanner analyze global-duplicates
duplicate-scanner analyze global-duplicates --min-copies 3

# Storage optimization insights
duplicate-scanner analyze storage --recommend-deletions
duplicate-scanner analyze storage --by-directory
duplicate-scanner analyze storage --by-type
```

### Batch Operations

```bash
# Generate deletion scripts
duplicate-scanner generate delete-script SCAN_ID --keep newest
duplicate-scanner generate delete-script SCAN_ID --keep /priority/path/**

# Verify file integrity
duplicate-scanner verify SCAN_ID
duplicate-scanner verify --rehash-changed
```

## Output Formats

### YAML Format (Default)

```yaml
schema_version: "1.0.0"
metadata:
  scan_id: "scan_20250919_143022"
  timestamp: "2025-09-19T14:30:22Z"
  directory: "/path/to/scan"
  # ... metadata

confirmed_duplicates:
  - group_id: 1
    hash: "a1b2c3..."
    total_size: 1048576
    files:
      - path: "/path/file1.mp4"
        size: 1048576
        modified: "2025-09-15T10:30:00Z"
      # ... more files

potential_matches:
  - group_id: 1
    similarity_score: 0.85
    files:
      # ... similar files

statistics:
  duplicate_groups: 15
  total_duplicate_files: 42
  total_wasted_space_bytes: 1073741824
```

### JSON Format (Backward Compatibility)

```json
{
  "schema_version": "1.0.0",
  "metadata": {
    "scan_id": "scan_20250919_143022",
    "timestamp": "2025-09-19T14:30:22Z"
  },
  "confirmed_duplicates": [],
  "potential_matches": [],
  "statistics": {}
}
```

### Human-Readable Format

```
Duplicate Scan Results
======================
Scanned: /path/to/directory
Time: 2025-09-19 14:30:22
Files: 1,524 files scanned

Confirmed Duplicates: 15 groups, 42 files
Total wasted space: 1.0 GB

Group 1: video_sample.mp4 (100 MB, 3 copies)
  /movies/sample.mp4
  /backup/movies/sample.mp4
  /archive/old_movies/sample.mp4

Potential Matches: 8 groups, 18 files
...
```

## Error Handling and Exit Codes

### Exit Codes

- 0: Success
- 1: General error
- 2: Invalid arguments
- 3: File access error
- 4: Database error
- 5: Configuration error

### Error Messages

```bash
# Clear error reporting
Error: Cannot access directory '/invalid/path'
Suggestion: Check path exists and you have read permission

Error: Database corrupted at /path/to/files.db
Suggestion: Run 'duplicate-scanner database repair' or restore from backup

Error: Invalid configuration file
Suggestion: Run 'duplicate-scanner config validate' for details
```

## Backward Compatibility

### Preserved Commands

All existing commands continue to work unchanged:

```bash
# These work exactly as before
duplicate-scanner scan /videos
duplicate-scanner scan /videos --output results.json
duplicate-scanner config show
```

### Migration Path

```bash
# Automatic migration on first run
duplicate-scanner scan /path  # Creates database, imports old results

# Manual migration
duplicate-scanner database migrate --from-results /path/to/old/results.yaml
```
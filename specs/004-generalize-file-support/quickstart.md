# Quickstart Guide: Generalized File Duplicate Detection

**Purpose**: Get started with the enhanced universal file duplicate scanner  
**Audience**: Existing users migrating from video-only version and new users

## Installation and Setup

### Prerequisites

- Python 3.12 or higher
- 50MB disk space for application and database
- Read access to directories you want to scan

### First-Time Setup

```bash
# Install the enhanced version
pip install duplicate-scanner --upgrade

# Verify installation
duplicate-scanner --version

# Initialize configuration (optional)
duplicate-scanner config init
```

### Database Setup

The enhanced version automatically creates a SQLite database for improved performance:

```bash
# Check database status
duplicate-scanner database status

# Expected output:
# Database: ~/.local/share/duplicate-scanner/files.db
# Status: Ready (newly created)
# Files tracked: 0
```

## Migration from Video-Only Version

### Automatic Migration

Your first scan automatically migrates existing functionality:

```bash
# This works exactly as before, but now with database backing
duplicate-scanner scan /path/to/videos

# Your existing commands continue to work unchanged
duplicate-scanner scan /videos --output results.json
```

### Import Historical Data

If you have previous scan results, import them:

```bash
# Import old scan results into database
duplicate-scanner database import /path/to/old/results.yaml

# Verify import
duplicate-scanner database stats
```

## Basic Usage Examples

### Video Files (Existing Workflow)

```bash
# Exactly the same as before - backward compatible
duplicate-scanner scan /path/to/videos

# With database benefits (faster re-scans)
duplicate-scanner scan /path/to/videos  # First run: full scan
duplicate-scanner scan /path/to/videos  # Second run: much faster due to caching
```

### Document Files (New Capability)

```bash
# Scan for document duplicates
duplicate-scanner scan /path/to/documents --include "*.pdf,*.doc,*.txt"

# Large documents only
duplicate-scanner scan /documents --min-size 10MB --type document
```

### Mixed File Types

```bash
# Scan multiple file types
duplicate-scanner scan /path --type video,document,image

# Custom patterns
duplicate-scanner scan /path --include "*.mp4,*.pdf,*.jpg" --exclude "*.tmp"
```

## Advanced Features

### Cross-Scan Duplicate Detection

Find duplicates across different scans:

```bash
# Scan different directories
duplicate-scanner scan /movies
duplicate-scanner scan /backup/movies
duplicate-scanner scan /archive

# Find global duplicates
duplicate-scanner analyze global-duplicates
```

### File Movement Tracking

Track how files move between locations:

```bash
# Check file history
duplicate-scanner database history /path/to/file.mp4

# Expected output:
# File History: sample.mp4
# 2025-09-01: /movies/sample.mp4 (scan_001)
# 2025-09-10: /backup/movies/sample.mp4 (scan_015)
# 2025-09-19: /archive/movies/sample.mp4 (scan_023)
```

### Storage Optimization

Get insights on storage usage:

```bash
# Storage analysis
duplicate-scanner analyze storage

# Expected output:
# Storage Analysis Report
# ======================
# Total files tracked: 15,420
# Duplicate groups: 1,247
# Wasted space: 2.3 GB
# 
# Top directories by duplicates:
# 1. /downloads - 847 MB wasted
# 2. /backup - 523 MB wasted
# 3. /archive - 312 MB wasted
```

## Configuration Examples

### Basic Configuration

```bash
# View current settings
duplicate-scanner config show

# Edit configuration
duplicate-scanner config edit
```

### Custom File Types

```bash
# Add a new file type category
duplicate-scanner config add-type ebooks --extensions "*.epub,*.mobi,*.pdf"

# Scan using custom type
duplicate-scanner scan /library --type ebooks
```

### Performance Tuning

```yaml
# ~/.config/duplicate-scanner/config.yaml
database:
  enabled: true
  cache_hashes: true
  max_cache_age_days: 30

performance:
  large_file_threshold: 100000000  # 100MB
  chunk_size: 65536  # 64KB for hash computation
  max_concurrent_files: 4

file_type_settings:
  video:
    extensions: ["mp4", "mkv", "avi", "mov"]
    large_file_threshold: 500000000  # 500MB
  document:
    extensions: ["pdf", "doc", "docx", "txt"]
    large_file_threshold: 50000000   # 50MB
```

## Common Workflows

### Daily Backup Verification

```bash
#!/bin/bash
# Daily script to check for new duplicates

# Scan main directories
duplicate-scanner scan /home/user/Documents --scan-id daily_docs
duplicate-scanner scan /home/user/Downloads --scan-id daily_downloads

# Check for cross-directory duplicates
duplicate-scanner analyze global-duplicates --min-copies 2

# Cleanup old database records
duplicate-scanner database cleanup --older-than 30d
```

### Storage Cleanup

```bash
# Find all duplicates
duplicate-scanner scan /storage --type video,document,image

# Generate deletion script keeping newest files
duplicate-scanner generate delete-script latest --keep newest

# Review and execute (manually)
bash deletion_script.sh
```

### Archive Management

```bash
# Scan archive before and after
duplicate-scanner scan /archive --scan-id before_cleanup

# ... perform manual cleanup ...

duplicate-scanner scan /archive --scan-id after_cleanup

# Compare results
duplicate-scanner results diff before_cleanup after_cleanup
```

## Performance Expectations

### Scan Performance

| File Count | First Scan | Re-scan (cached) | Database Size |
|------------|------------|------------------|---------------|
| 1,000 files | 30 seconds | 5 seconds | 2 MB |
| 10,000 files | 5 minutes | 30 seconds | 15 MB |
| 100,000 files | 45 minutes | 5 minutes | 120 MB |

### Hash Cache Benefits

```bash
# Monitor cache effectiveness
duplicate-scanner database stats

# Expected output shows cache hit rate:
# Cache hit rate: 87.3% (13,456/15,420 files)
# Average scan speedup: 3.2x
```

## Troubleshooting

### Database Issues

```bash
# Check database integrity
duplicate-scanner database verify

# Repair corrupted database
duplicate-scanner database repair

# Backup and restore
duplicate-scanner database backup /path/to/backup.db
duplicate-scanner database restore /path/to/backup.db
```

### Performance Issues

```bash
# Enable verbose logging
duplicate-scanner scan /path --verbose

# Check system resources
duplicate-scanner database stats --performance

# Reduce memory usage for large scans
duplicate-scanner scan /path --no-cache --chunk-size 32768
```

### Configuration Problems

```bash
# Validate configuration
duplicate-scanner config validate

# Reset to defaults
duplicate-scanner config init --overwrite

# Show schema for reference
duplicate-scanner config schema
```

## Migration Checklist

### From Video-Only Version

- [x] Existing commands work unchanged
- [x] Scan results format remains compatible  
- [x] Configuration files are automatically upgraded
- [x] Performance improves on subsequent scans
- [x] New features are opt-in

### Verification Steps

1. **Run existing command**: `duplicate-scanner scan /videos`
2. **Check results match**: Compare with previous scan results
3. **Verify performance**: Second scan should be significantly faster
4. **Test new features**: Try file type filtering and database commands
5. **Confirm configuration**: `duplicate-scanner config show`

## Getting Help

### Documentation

```bash
# Command help
duplicate-scanner --help
duplicate-scanner scan --help
duplicate-scanner database --help

# Configuration reference
duplicate-scanner config help

# Version and build info
duplicate-scanner --version --verbose
```

### Common Issues

1. **Slow initial scan**: Normal - subsequent scans will be much faster
2. **Database locked**: Another scan may be running - wait or check processes
3. **Permission errors**: Ensure read access to scan directories
4. **Memory usage**: Use `--no-cache` for extremely large file sets

### Support Resources

- GitHub Issues: Report bugs and request features
- Documentation: Full API and configuration reference
- Examples: Additional workflow examples and scripts

---

**Ready to Use**: The enhanced duplicate scanner is backward compatible and immediately provides better performance for existing workflows while enabling new file type detection capabilities.
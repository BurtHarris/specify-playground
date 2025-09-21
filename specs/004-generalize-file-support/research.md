# Phase 0: Research - Generalize File Support and Add Central Database

**Generated**: September 19, 2025  
**Scope**: Research decisions for universal file duplicate detection with SQLite integration

## Research Areas

### Database Migration Strategy for Existing Users

**Decision**: Graceful migration with automatic backup and fallback

**Rationale**: 
- First-time users experience seamless transition from file-only to database-backed scanning
- Existing scan result files remain valid and readable
- Database corruption or issues don't break core functionality

**Alternatives Considered**:
- Forced migration: Rejected due to risk of data loss
- Database-only mode: Rejected due to complexity for simple use cases
- Manual migration only: Rejected due to poor user experience

**Implementation**:
- Auto-create database on first run with new version
- Import historical scan data from existing YAML files when found
- Maintain database-less fallback mode for emergency recovery
- Implement database backup/restore commands

### Performance Impact Assessment for Large File Sets

**Decision**: Streaming hash computation with intelligent caching

**Rationale**:
- Large files (>100MB) use streaming SHA-256 to avoid memory issues
- Hash caching in database provides 50%+ performance improvement on re-scans
- Database queries optimized with proper indexing for <100ms response times

**Alternatives Considered**:
- In-memory hash computation: Rejected due to memory constraints for large files
- Alternative hash algorithms (MD5, Blake2b): SHA-256 chosen for security and widespread support
- File modification time-based caching: Enhanced with size+mtime composite key for accuracy

**Implementation**:
- Use hashlib with 64KB chunks for streaming computation
- SQLite indexes on path, size, and hash columns
- Cache invalidation based on file size and modification time
- Background hash computation for non-blocking UI

### JSON Schema Design for Configuration Validation

**Decision**: JSON Schema v7 with comprehensive validation rules

**Rationale**:
- Provides clear documentation and validation for configuration files
- Enables better error messages for invalid configurations
- Supports future configuration evolution with version compatibility

**Alternatives Considered**:
- Pydantic models: Rejected to avoid adding heavy dependencies
- Manual validation: Rejected due to maintenance overhead and poor error messages
- Cerberus: JSON Schema chosen for standardization and tooling support

**Implementation**:
- Separate schemas for configuration and scan results
- Runtime validation with jsonschema library
- Schema version tracking for future compatibility
- Auto-generated documentation from schemas

### File Type Categorization Approach

**Decision**: Configurable extension-based categorization with overrides

**Rationale**:
- Simple extension-based approach covers 95% of use cases
- Configurable categories allow user customization
- Performance-optimized with no file content inspection required

**Alternatives Considered**:
- MIME type detection: Rejected due to performance overhead
- File content inspection: Rejected due to complexity and false positives
- Magic number detection: Extension-based chosen for speed and simplicity

**Implementation**:
- Default categories: video, document, image, archive, text
- User-configurable via YAML configuration
- Category-specific settings (size thresholds, special handling)
- Fallback to "other" category for unknown extensions

### Cross-Platform Database Location Strategy

**Decision**: Platform-specific user data directories with environment variable override

**Rationale**:
- Follows platform conventions for data storage
- Supports portable installations via environment variables
- Consistent with configuration file location strategy

**Alternatives Considered**:
- Current directory: Rejected due to permission and portability issues
- Home directory: Platform-specific locations preferred for better integration
- Temp directory: Rejected due to data persistence requirements

**Implementation**:
- Windows: `%APPDATA%/duplicate-scanner/`
- macOS: `~/Library/Application Support/duplicate-scanner/`
- Linux: `~/.local/share/duplicate-scanner/`
- Override via `DUPLICATE_SCANNER_DATA_DIR` environment variable
- Auto-create directory structure with proper permissions

### Backward Compatibility Testing Approach

**Decision**: Comprehensive regression test suite with version compatibility matrix

**Rationale**:
- Existing users must experience zero breaking changes
- CLI interface remains stable while adding new features
- Scan result format maintains compatibility with existing tooling

**Alternatives Considered**:
- Manual testing only: Rejected due to error-prone nature
- Limited compatibility: Full compatibility chosen to preserve user trust
- Version-specific modes: Unified interface chosen for simplicity

**Implementation**:
- Contract tests for all existing CLI commands
- Golden file testing for scan result format compatibility
- Performance regression tests with benchmarking
- Integration tests with real-world file structures
- Continuous testing against previous version outputs

## Technology Decisions

### SQLite Database Engine

**Decision**: SQLite with WAL mode and optimized pragmas

**Rationale**:
- Zero-configuration embedded database
- Excellent Python integration
- ACID transactions with good performance
- Cross-platform compatibility

**Configuration**:
```sql
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA cache_size = 10000;
PRAGMA foreign_keys = ON;
```

### JSON Schema Validation

**Decision**: `jsonschema` library with Draft 7 specification

**Rationale**:
- Mature library with excellent Python integration
- Comprehensive validation capabilities
- Good error reporting for user feedback

### Hash Algorithm Selection

**Decision**: SHA-256 for file content hashing

**Rationale**:
- Cryptographically secure (prevents accidental collisions)
- Widely supported and standardized
- Good balance of speed and security
- 256-bit output provides excellent collision resistance

### Configuration Management Integration

**Decision**: Extend existing PyYAML-based configuration system

**Rationale**:
- Consistent with current implementation
- Human-readable configuration files
- Good Python ecosystem support
- Easy migration from existing configuration

## Risk Mitigation

### Database Corruption Recovery

- Automatic database integrity checks on startup
- Backup before schema migrations
- Recovery from corruption by rebuilding from scan history
- Graceful degradation to file-only mode

### Performance Regression Prevention

- Benchmark suite with performance thresholds
- Memory usage monitoring for large file sets
- Database query performance monitoring
- Streaming algorithms to prevent memory spikes

### Cross-Platform Compatibility

- Path handling exclusively through pathlib
- Platform-specific testing in CI pipeline
- File system permission handling
- Character encoding standardization (UTF-8)

## Implementation Notes

### Database Schema Evolution

- Version tracking in database metadata
- Incremental migration scripts
- Backward compatibility for at least 2 major versions
- Migration testing with real-world data

### Testing Strategy

- Unit tests for all new components
- Integration tests for database operations
- Performance tests with large file sets
- Contract tests for CLI interface stability
- Cross-platform testing automation

### Error Handling

- Graceful degradation when database unavailable
- Clear error messages for configuration issues
- Recovery suggestions for common problems
- Logging for debugging complex scenarios

---

**Research Complete**: All technical unknowns resolved with concrete implementation decisions.
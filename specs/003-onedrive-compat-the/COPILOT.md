# OneDrive Integration Instructions for GitHub Copilot

**Feature**: OneDrive Integration and Compatibility  
**Branch**: 003-onedrive-compat-the  
**Phase**: Implementation Planning Complete  

## OneDrive Integration Context

This feature extends the existing Video Duplicate Scanner with **optional** OneDrive cloud storage integration. The system maintains full functionality without OneDrive API access, while providing enhanced features for users who complete the authentication setup. Microsoft Graph API integration is used only when available and configured.

**Design Philosophy:**
- **Core functionality remains unchanged** - scanner works perfectly without OneDrive API
- **Optional enhancement** - OneDrive integration provides additional capabilities for power users
- **Graceful degradation** - authentication/API failures never break basic scanning
- **Deferred complexity** - users can start immediately, add OneDrive features later

## Python Version Requirement

**Python 3.12+** is required for this feature. The CLI must validate the Python version at startup and exit with an error message if an older version is detected.

## Key OneDrive Integration Points

### MVP Scope (Local Detection Only)
- **Enhanced VideoFileScanner**: Detect OneDrive files using local file attributes
- **CloudFileStatus**: Simple enum with LOCAL and CLOUD_ONLY states
- **Platform Detection**: Windows file attribute checking only

### Future Enhancement Scope (API Integration)
- **OneDriveService**: Microsoft Graph API integration for file metadata and hash retrieval
- **OneDriveMetadata**: Container for Graph API response data including QuickXorHash
- **Advanced CloudFileStatus**: Extended enum with available, pinned states

### Authentication & API (Optional)
- **Microsoft Graph SDK**: Use `msgraph-sdk` and `azure-identity` for authentication (only when user opts in)
- **Delegated Permissions**: Files.Read scope for user OneDrive access (deferred setup)
- **Rate Limiting**: Respect 10,000 requests/hour limit with exponential backoff
- **Batch Operations**: Group up to 20 files per API request for efficiency
- **No Authentication Fallback**: Scanner works normally without any Graph API setup

### Hash Algorithm Support
- **BLAKE2b**: Default hash algorithm for all files (MVP and Future Enhancement)

### Platform Detection
OneDrive files are detected using file-level attributes only - no directory pattern matching required.

**MVP Scope:**
- **Windows**: Use `FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS` file attribute via Windows API

**Future Enhancement:**
- **macOS**: Check `com.microsoft.OneDrive.status` extended attribute  
- **Linux**: OneDrive Linux client metadata detection

Each file is checked individually during scanning; no special OneDrive directory detection needed.

## Implementation Guidelines

### OneDrive File Processing (MVP)
```python
# MVP: Simple local file attribute detection only
# Skip cloud-only files silently, use BLAKE2b for all locally available files

def process_onedrive_file(file_path: Path) -> Optional[VideoFile]:
    status = detect_cloud_status(file_path)  # LOCAL or CLOUD_ONLY
    
    if status == CloudFileStatus.CLOUD_ONLY:
        # Skip cloud-only files silently
        return None
    else:
        # Process as normal local file with BLAKE2b hash
        return VideoFile(path=file_path, cloud_status=status)
```

### Error Handling Patterns
- **API Unavailable**: Continue with local-only scanning, report status in final summary
- **Authentication Failed**: Report auth failure in summary, suggest re-authentication
- **Rate Limited**: Implement exponential backoff, continue with cached data
- **Partial Metadata**: Use available information, no user notification needed

### Testing Requirements
- **Mock Graph API**: Use `responses` library for HTTP mocking
- **Platform Detection**: Mock file attributes for cross-platform testing
- **Cloud Scenarios**: Test mixed local/cloud environments
- **Error Conditions**: Verify graceful degradation in all failure modes

## Code Quality Standards

### Performance Requirements
- **API Batch Size**: Maximum 20 files per Graph API request
- **Memory Efficiency**: Stream large directory scans, avoid loading all metadata at once
- **Network Efficiency**: Cache metadata for 30 minutes, avoid redundant API calls
- **Fallback Performance**: Local file performance unchanged when API unavailable

### Data Validation
- **Cloud Status Consistency**: All OneDrive files must have valid CloudFileStatus
- **Hash Algorithm Tracking**: Always record which algorithm produced each hash
- **Metadata Completeness**: Validate OneDrive metadata before using for comparison
- **Cross-Platform Paths**: Handle OneDrive path variations across operating systems

## Integration with Existing Code

### VideoFile Model Enhancement (MVP)
```python
@dataclass
class VideoFile:
    # Existing fields
    path: Path
    size: int
    _hash: Optional[str] = None
    
    # MVP OneDrive field
    cloud_status: CloudFileStatus = CloudFileStatus.LOCAL
    
    # Future Enhancement fields (unused in MVP)
    # cloud_hash: Optional[str] = None
    # cloud_hash_algorithm: Optional[str] = None
    # onedrive_item_id: Optional[str] = None
```

### CLI Output Enhancement
- **Cloud Indicators**: Mark OneDrive files in output with cloud status (local vs synced)
- **Mixed Groups**: Clearly show when duplicate groups contain both local and cloud files
- **Summary Statistics**: Report API authentication status and any degraded mode operation at scan completion
- **Silent Operation**: No mention of skipped cloud-only files during normal operation

## Development Workflow

### Implementation Order (MVP Focus)
1. **Core Models**: Extend VideoFile with cloud_status field, add CloudFileStatus enum (LOCAL, CLOUD_ONLY only)
2. **Platform Detection**: Implement Windows OneDrive file attribute detection using Windows API
3. **Basic OneDrive Support**: Scanner detects OneDrive files, skips cloud-only files silently
4. **CLI Integration**: Update output to show "OneDrive" indicator for detected files
5. **Testing Suite**: Comprehensive testing of local OneDrive detection and graceful degradation
6. **MVP Release**: Complete working solution without API dependencies

**Future Enhancements (Optional):**
7. **Graph API Integration**: OneDriveService with authentication and metadata retrieval
8. **Hash Compatibility**: Cross-algorithm comparison and API-based optimization
9. **Enhanced Testing**: API mocking and cloud scenario testing

### Testing Strategy
- **Unit Tests**: Mock all external dependencies (Graph API, file system attributes)
- **Integration Tests**: End-to-end scenarios with real OneDrive directories (optional)
- **Contract Tests**: Verify API integration contracts match Graph API specification
- **Performance Tests**: Benchmark OneDrive integration overhead

## Security Considerations

### Authentication
- **Minimize Scope**: Request only Files.Read permissions, avoid write access
- **Token Handling**: Use Azure Identity library for secure credential management
- **User Privacy**: Don't log or cache sensitive file metadata unnecessarily

### Data Protection
- **API Limits**: Respect Microsoft Graph throttling to avoid service disruption
- **Error Logging**: Avoid logging authentication tokens or sensitive file paths
- **Graceful Degradation**: Never fail entire scan due to OneDrive issues

## Completion Criteria

**MVP Release - Core OneDrive Support (Local Detection Only):**
- ✅ OneDrive files are detected using local file attributes
- ✅ Scanner works normally in OneDrive directories without API
- ✅ CLI output indicates OneDrive vs local files
- ✅ Windows platform supports OneDrive file detection
- ✅ Graceful handling when files are cloud-only (skip silently)
- ✅ Comprehensive testing of local OneDrive detection

**Future Enhancement - Advanced OneDrive Support (Optional API Integration):**
- ✅ Graph API metadata is retrieved and cached efficiently (when configured)
- ✅ QuickXorHash values are used for duplicate detection when available
- ✅ Cross-algorithm hash comparison works correctly
- ✅ Scanner gracefully handles authentication and API failures
- ✅ Performance overhead is acceptable (<50% for typical OneDrive directories)
- ✅ Comprehensive test coverage includes mocked scenarios

**Key Principle:** Core functionality never depends on Graph API - it's purely an enhancement.

When implementing, prioritize the graceful degradation aspects - the scanner should always work for local files even when OneDrive integration fails.

## Windows API Implementation Details

The MVP uses Windows file attributes to detect OneDrive cloud files:

- **Target Attribute**: `FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS` (0x00400000)
- **Detection Method**: Check if file has this attribute set
- **API Function**: Use `GetFileAttributes()` Windows API
- **Python Implementation**: Access via ctypes to windll.kernel32

### Complete Implementation Approach

```python
import ctypes
from pathlib import Path
from enum import Enum

class CloudFileStatus(Enum):
    """OneDrive cloud file status."""
    LOCAL = "local"
    CLOUD_ONLY = "cloud_only"

FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS = 0x00400000
INVALID_FILE_ATTRIBUTES = 0xFFFFFFFF

def get_onedrive_status(file_path: Path) -> CloudFileStatus:
    """
    Get OneDrive cloud status for a file using Windows API.
    
    Args:
        file_path: Path to the file to check
        
    Returns:
        CloudFileStatus indicating whether file is local or cloud-only
        
    Note:
        Returns LOCAL on non-Windows platforms or if API call fails
    """
    try:
        # Only works on Windows
        if not hasattr(ctypes, 'windll'):
            return CloudFileStatus.LOCAL
            
        # Get file attributes using Windows API
        # GetFileAttributesW for Unicode support
        attributes = ctypes.windll.kernel32.GetFileAttributesW(str(file_path))
        
        # Check for API call failure
        if attributes == INVALID_FILE_ATTRIBUTES:
            return CloudFileStatus.LOCAL
            
        # Check if file has recall-on-data-access attribute
        if attributes & FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS:
            return CloudFileStatus.CLOUD_ONLY
        else:
            return CloudFileStatus.LOCAL
            
    except (OSError, AttributeError):
        # Fallback to LOCAL on any error
        return CloudFileStatus.LOCAL
```

### Integration with VideoFile Model

The `VideoFile` class will be enhanced with:

```python
@property
def cloud_status(self) -> CloudFileStatus:
    """OneDrive cloud status (computed lazily)."""
    if self._cloud_status is None:
        self._cloud_status = get_onedrive_status(self.path)
    return self._cloud_status

def is_cloud_only(self) -> bool:
    """Check if file is OneDrive cloud-only."""
    return self.cloud_status == CloudFileStatus.CLOUD_ONLY
```

### Error Handling Strategy

- **API Failures**: Default to `LOCAL` status (assume file is accessible)
- **Non-Windows Platforms**: Return `LOCAL` (feature is Windows-specific)
- **Permission Errors**: Return `LOCAL` (conservative approach)
- **File Not Found**: Return `LOCAL` (let normal file processing handle)

The file attribute indicates that the file is stored in OneDrive cloud and is not fully present locally (only metadata/stub exists). When this attribute is present, the file should be skipped during hash computation to avoid triggering download.
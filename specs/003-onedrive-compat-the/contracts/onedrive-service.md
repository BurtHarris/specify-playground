# OneDrive Service Contract

**Created**: September 18, 2025  
**Phase**: 1 - Design & Contracts  
**Service**: OneDriveService  

## Interface Definition

### Core Service Interface
```python
from abc import ABC, abstractmethod
from typing import Optional, List, Dict
from pathlib import Path

class IOneDriveService(ABC):
    """Contract for OneDrive file detection and metadata services"""
    
    @abstractmethod
    async def detect_cloud_status(self, file_path: Path) -> CloudFileStatus:
        """
        Detect OneDrive sync status for a file.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            CloudFileStatus indicating sync state
            
        Raises:
            OneDriveServiceError: For service-level failures
            FileNotFoundError: If file doesn't exist
        """
        pass
    
    @abstractmethod
    async def get_file_metadata(self, file_path: Path) -> Optional[OneDriveMetadata]:
        """
        Retrieve OneDrive metadata via Graph API.
        
        Args:
            file_path: Path to OneDrive file
            
        Returns:
            OneDriveMetadata with hash information, or None if unavailable
            
        Raises:
            OneDriveAPIError: For Graph API failures
            OneDriveAuthError: For authentication issues
            OneDriveRateLimitError: For rate limiting
        """
        pass
    
    @abstractmethod
    def is_onedrive_directory(self, directory: Path) -> bool:
        """
        Check if directory is managed by OneDrive.
        
        Args:
            directory: Directory path to check
            
        Returns:
            True if directory is OneDrive-managed
            
        Note:
            Should work offline using local detection methods
        """
        pass
    
    @abstractmethod
    async def batch_get_metadata(self, file_paths: List[Path]) -> Dict[Path, OneDriveMetadata]:
        """
        Efficiently retrieve metadata for multiple files.
        
        Args:
            file_paths: List of OneDrive file paths
            
        Returns:
            Dictionary mapping paths to metadata (missing files omitted)
            
        Raises:
            OneDriveAPIError: For API failures affecting entire batch
            
        Note:
            Should handle partial failures gracefully
        """
        pass
```

## Method Contracts

### detect_cloud_status

**Input Contract:**
- `file_path`: Must be an existing file path
- File must be readable by current user
- Path can be absolute or relative

**Output Contract:**
- Returns `CloudFileStatus` enum value
- `LOCAL`: Regular local file (not OneDrive managed)
- `CLOUD_ONLY`: OneDrive placeholder file 
- `LOCALLY_AVAILABLE`: OneDrive file cached locally
- `ALWAYS_LOCAL`: OneDrive file pinned to device
- `UNKNOWN`: Status could not be determined

**Error Contract:**
- `FileNotFoundError`: File does not exist
- `OneDriveServiceError`: Platform detection failed
- `PermissionError`: Insufficient file access rights

**Performance Contract:**
- Should complete in <100ms for local detection
- Should not trigger network requests
- Should not cause file downloads

### get_file_metadata

**Input Contract:**
- `file_path`: Must be OneDrive-managed file
- User must have OneDrive access permissions
- Network connectivity required for Graph API

**Output Contract:**
- Returns `OneDriveMetadata` with available hash information
- Returns `None` if file not accessible via API
- Metadata includes at least `item_id` and `size`
- Hash fields populated based on OneDrive availability

**Error Contract:**
- `OneDriveAuthError`: Authentication failed or expired
- `OneDriveAPIError`: Graph API request failed
- `OneDriveRateLimitError`: API rate limit exceeded
- `FileNotFoundError`: File not found in OneDrive

**Performance Contract:**
- Single request should complete in <2 seconds
- Should respect Graph API rate limits (10k/hour)
- Should cache results for duplicate requests

### is_onedrive_directory

**Input Contract:**
- `directory`: Directory path (existing or non-existing)
- Should handle both absolute and relative paths
- Should work with empty or inaccessible directories

**Output Contract:**
- Returns `True` if directory is OneDrive-managed
- Returns `False` for regular directories
- Should be consistent across platform implementations

**Error Contract:**
- Should not raise exceptions for normal cases
- `PermissionError`: Only if directory access completely denied

**Performance Contract:**
- Should complete in <50ms using local detection
- Should not require network access
- Should cache results for repeated queries

### batch_get_metadata

**Input Contract:**
- `file_paths`: List of OneDrive file paths (max 20 for efficiency)
- All paths should be OneDrive-managed files
- Requires authenticated Graph API client

**Output Contract:**
- Returns dictionary mapping successful paths to metadata
- Omits paths that failed or are inaccessible
- Preserves order information via consistent iteration

**Error Contract:**
- `OneDriveAPIError`: For request-level failures affecting all files
- Individual file failures should not cause method failure
- Rate limiting should be handled with exponential backoff

**Performance Contract:**
- Batch of 20 files should complete in <5 seconds
- Should use Graph API batch endpoints when possible
- Should implement request coalescing for efficiency

## Implementation Requirements

### Authentication Handling
```python
# Required authentication support
class AuthenticationContract:
    def supports_delegated_auth(self) -> bool:
        """Must support user-delegated OneDrive access"""
        return True
    
    def handles_auth_refresh(self) -> bool:
        """Must handle token refresh automatically"""
        return True
    
    def graceful_auth_failure(self) -> bool:
        """Must degrade gracefully when auth fails"""
        return True
```

### Caching Requirements
```python
# Required caching behavior
class CachingContract:
    def caches_metadata(self) -> bool:
        """Should cache OneDrive metadata to reduce API calls"""
        return True
    
    def cache_ttl_minutes(self) -> int:
        """Metadata cache should expire after reasonable time"""
        return 30
    
    def respects_rate_limits(self) -> bool:
        """Must implement rate limiting awareness"""
        return True
```

### Platform Support
```python
# Required platform detection methods
class PlatformContract:
    def supports_windows(self) -> bool:
        """Must detect OneDrive on Windows using file attributes"""
        return True
    
    def supports_macos(self) -> bool:
        """Must detect OneDrive on macOS using extended attributes"""
        return True
    
    def supports_linux(self) -> bool:
        """Should support Linux OneDrive client detection"""
        return True  # Best effort
```

## Error Handling Contract

### Exception Hierarchy
```python
class OneDriveServiceError(Exception):
    """Base exception for all OneDrive service issues"""
    pass

class OneDriveAPIError(OneDriveServiceError):
    """Graph API request failures"""
    def __init__(self, message: str, status_code: int, request_id: str):
        super().__init__(message)
        self.status_code = status_code
        self.request_id = request_id

class OneDriveAuthError(OneDriveServiceError):
    """Authentication/authorization failures"""
    def __init__(self, message: str, requires_reauth: bool = False):
        super().__init__(message)
        self.requires_reauth = requires_reauth

class OneDriveRateLimitError(OneDriveServiceError):
    """API rate limiting encountered"""
    def __init__(self, message: str, retry_after_seconds: int):
        super().__init__(message)
        self.retry_after_seconds = retry_after_seconds
```

### Recovery Strategies
- **Authentication Failures**: Prompt for re-authentication or continue local-only
- **Rate Limiting**: Implement exponential backoff with jitter
- **API Unavailable**: Fall back to local-only processing
- **Partial Failures**: Process available files, report failed files separately

## Testing Contract

### Mock Requirements
```python
class MockOneDriveService(IOneDriveService):
    """Test mock must support all scenarios"""
    
    def setup_cloud_file(self, path: Path, status: CloudFileStatus):
        """Configure mock file status for testing"""
        pass
    
    def setup_api_failure(self, error_type: Type[Exception]):
        """Configure API failure scenarios"""
        pass
    
    def setup_rate_limiting(self, requests_before_limit: int):
        """Configure rate limiting simulation"""
        pass
```

### Required Test Scenarios
- Local file detection (should return LOCAL status)
- OneDrive placeholder detection (various sync states)
- Graph API metadata retrieval (with different hash types)
- Batch processing with partial failures
- Authentication failure recovery
- Rate limiting and retry behavior
- Offline operation (API unavailable)
- Cross-platform file detection
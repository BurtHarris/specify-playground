# VideoFileScanner Contract (Enhanced)

**Created**: September 18, 2025  
**Phase**: 1 - Design & Contracts  
**Service**: VideoFileScanner (OneDrive Integration)  

## Interface Enhancement

### Enhanced Scanner Interface
```python
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, AsyncIterator
from pathlib import Path

class IVideoFileScanner(ABC):
    """Enhanced video file scanner with OneDrive integration"""
    
    @abstractmethod
    async def scan_directory(self,
                           directory: Path,
                           recursive: bool = True,
                           include_cloud: bool = True,
                           cloud_only: bool = False) -> ScanResult:
        """
        Scan directory for video duplicates with cloud support.
        
        Args:
            directory: Root directory to scan
            recursive: Include subdirectories
            include_cloud: Process OneDrive files
            cloud_only: Only process cloud files (skip local)
            
        Returns:
            ScanResult with duplicates and cloud statistics
            
        Raises:
            DirectoryNotFoundError: Directory doesn't exist
            PermissionError: Insufficient directory access
        """
        pass
    
    @abstractmethod
    async def scan_files(self, 
                        file_paths: List[Path],
                        include_cloud: bool = True) -> ScanResult:
        """
        Scan specific files for duplicates with cloud support.
        
        Args:
            file_paths: Specific video files to scan
            include_cloud: Process OneDrive files in list
            
        Returns:
            ScanResult containing only the specified files
        """
        pass
    
    @abstractmethod
    async def stream_video_files(self,
                                directory: Path,
                                recursive: bool = True,
                                include_cloud: bool = True) -> AsyncIterator[VideoFile]:
        """
        Stream video files with cloud metadata as discovered.
        
        Args:
            directory: Root directory to scan
            recursive: Include subdirectories  
            include_cloud: Include OneDrive files
            
        Yields:
            VideoFile instances with cloud metadata populated
            
        Note:
            Memory-efficient for large directories
        """
        pass
```

## Method Contracts

### scan_directory (Enhanced)

**Input Contract:**
- `directory`: Must be existing readable directory
- `recursive`: Boolean flag for subdirectory traversal
- `include_cloud`: Whether to process OneDrive files
- `cloud_only`: If True, only process cloud files (exclude local)

**Output Contract:**
- Returns `ScanResult` with enhanced cloud statistics
- `duplicate_groups`: Contains both local and cloud duplicates
- `cloud_stats`: Populated with OneDrive-specific metrics
- Mixed groups clearly marked with cloud file indicators

**Enhanced Behavior:**
- Detects OneDrive directories using platform-specific methods
- Retrieves cloud metadata without triggering downloads
- Handles authentication failures gracefully (continues local-only)
- Respects API rate limits with automatic backoff

**Error Contract:**
- `DirectoryNotFoundError`: Directory does not exist
- `PermissionError`: Cannot access directory or files
- OneDrive-specific errors are handled internally (non-fatal)

**Performance Contract:**
- Local file performance unchanged from baseline
- Cloud metadata adds <100ms per file with good network
- Batch API requests minimize network round-trips
- Progress reporting includes cloud processing status

### scan_files (Enhanced)

**Input Contract:**
- `file_paths`: List of specific video file paths
- Paths can mix local and OneDrive files
- `include_cloud`: Controls processing of OneDrive files in list

**Output Contract:**
- Returns `ScanResult` limited to specified files
- Cloud files processed with metadata when available
- Statistics reflect only the scanned files

**Enhanced Behavior:**
- Automatically detects which files are OneDrive-managed
- Processes cloud files without downloads
- Handles mixed local/cloud file lists seamlessly

**Error Contract:**
- Individual file failures don't abort entire scan
- Missing files are excluded from results (not error)
- Cloud processing errors are logged but non-fatal

### stream_video_files (New)

**Input Contract:**
- `directory`: Root directory for streaming scan
- `recursive`: Include subdirectories in stream
- `include_cloud`: Whether to yield OneDrive files

**Output Contract:**
- Yields `VideoFile` instances as they are discovered
- Cloud metadata populated asynchronously
- Memory usage remains constant regardless of directory size

**Performance Contract:**
- Should yield first file within 1 second
- Memory usage <50MB regardless of directory size
- Cloud metadata retrieved in background batches

## Cloud Integration Contracts

### OneDrive Detection Contract
```python
async def _detect_onedrive_files(self, files: List[Path]) -> Dict[Path, CloudFileStatus]:
    """
    Detect OneDrive status for multiple files efficiently.
    
    Returns:
        Dictionary mapping file paths to their cloud status
        
    Performance:
        Should batch platform detection calls
        Should complete in <500ms for 100 files
    """
    pass
```

### Cloud Metadata Contract
```python
async def _enrich_with_cloud_metadata(self, files: List[VideoFile]) -> List[VideoFile]:
    """
    Enrich VideoFile instances with OneDrive metadata.
    
    Args:
        files: VideoFile instances needing cloud metadata
        
    Returns:
        Same instances with cloud_hash and metadata populated
        
    Behavior:
        Uses batch API requests for efficiency
        Handles authentication and rate limiting
        Gracefully handles metadata unavailability
    """
    pass
```

### Hash Compatibility Contract
```python
def _compare_cross_algorithm_hashes(self, file1: VideoFile, file2: VideoFile) -> bool:
    """
    Compare files with potentially different hash algorithms.
    
    Args:
        file1, file2: VideoFile instances to compare
        
    Returns:
        True if files are duplicates, False otherwise
        
    Behavior:
        Same algorithm: Direct comparison
        Different algorithms: Fallback to local computation
        QuickXorHash vs BLAKE2b: Compute missing hash
    """
    pass
```

## Cloud Statistics Contract

### Required Cloud Metrics
```python
@dataclass
class CloudScanStatistics:
    """Statistics that must be tracked during cloud scanning"""
    
    # File counts
    total_cloud_files: int = 0
    cloud_only_files: int = 0  
    locally_available_files: int = 0
    always_local_files: int = 0
    
    # API interaction
    api_requests_made: int = 0
    api_rate_limited: int = 0
    api_auth_failures: int = 0
    
    # Processing status
    cloud_files_processed: int = 0
    cloud_files_skipped: int = 0  # Due to errors
    offline_cloud_files: int = 0  # API unavailable
    
    # Hash information
    cloud_files_with_hashes: int = 0
    quick_xor_hashes: int = 0
    sha1_hashes: int = 0
    local_computed_hashes: int = 0  # For cloud files
    
    @property
    def cloud_processing_success_rate(self) -> float:
        """Percentage of cloud files successfully processed"""
        if self.total_cloud_files == 0:
            return 100.0
        return (self.cloud_files_processed / self.total_cloud_files) * 100
```

## Error Handling Contract

### Graceful Degradation Requirements
```python
class CloudScanErrorHandler:
    """Required error handling patterns for cloud scanning"""
    
    def handle_onedrive_unavailable(self) -> ScanBehavior:
        """
        When OneDrive API is completely unavailable:
        - Continue with local files only
        - Skip cloud-only files  
        - Report degraded mode in statistics
        """
        return ScanBehavior.LOCAL_ONLY
    
    def handle_authentication_failure(self) -> ScanBehavior:
        """
        When OneDrive authentication fails:
        - Prompt for re-authentication (optional)
        - Continue with local files
        - Include cloud files using local-only heuristics
        """
        return ScanBehavior.LOCAL_WITH_CLOUD_DETECTION
    
    def handle_rate_limiting(self, retry_after: int) -> ScanBehavior:
        """
        When API rate limits are hit:
        - Implement exponential backoff
        - Continue with cached metadata
        - Process remaining files with available data
        """
        return ScanBehavior.CACHED_WITH_BACKOFF
    
    def handle_partial_metadata(self, file: VideoFile) -> ProcessingDecision:
        """
        When cloud metadata is incomplete:
        - Use available hash information
        - Compute local hash if cloud unavailable
        - Mark metadata source in results
        """
        return ProcessingDecision.USE_AVAILABLE_DATA
```

## Progress Reporting Contract

### Enhanced Progress Events
```python
class CloudScanProgressEvent:
    """Progress events specific to cloud scanning"""
    
    class EventType(Enum):
        CLOUD_DETECTION_STARTED = "cloud_detection_started"
        CLOUD_METADATA_BATCH = "cloud_metadata_batch"
        CLOUD_HASH_RETRIEVED = "cloud_hash_retrieved"
        CLOUD_FALLBACK_HASH = "cloud_fallback_hash"  
        API_RATE_LIMITED = "api_rate_limited"
        AUTH_REFRESH_NEEDED = "auth_refresh_needed"
    
    event_type: EventType
    current_count: int
    total_count: int
    file_path: Optional[Path] = None
    additional_info: Dict[str, Any] = None
```

### Required Progress Callbacks
```python
class IProgressReporter(ABC):
    """Enhanced progress reporting for cloud operations"""
    
    @abstractmethod
    def report_cloud_detection(self, detected: int, total: int):
        """Report progress of OneDrive file detection"""
        pass
    
    @abstractmethod
    def report_cloud_metadata(self, retrieved: int, total_cloud_files: int):
        """Report progress of metadata retrieval"""
        pass
    
    @abstractmethod
    def report_api_limitation(self, limitation_type: str, retry_after: Optional[int]):
        """Report API rate limiting or authentication issues"""
        pass
```

## Testing Contract

### Mock Integration Requirements
```python
class MockVideoFileScanner(IVideoFileScanner):
    """Test mock supporting cloud scenarios"""
    
    def setup_onedrive_directory(self, path: Path, file_count: int):
        """Configure mock OneDrive directory structure"""
        pass
    
    def setup_mixed_environment(self, local_files: List[Path], cloud_files: List[Path]):
        """Configure mixed local/cloud test environment"""
        pass
    
    def setup_api_scenario(self, scenario: str):
        """Configure API behavior (success, failure, rate_limit, etc.)"""
        pass
    
    def setup_hash_scenarios(self, file_hash_map: Dict[Path, Tuple[str, str]]):
        """Configure file hash information (value, algorithm)"""
        pass
```

### Required Test Scenarios
- Mixed local/cloud directory scanning
- Cloud-only file processing
- API authentication failure recovery
- Rate limiting and retry behavior
- Cross-algorithm hash comparison
- Large directory streaming performance
- Offline mode operation
- Partial metadata handling

## Integration Requirements

### Dependency Injection
```python
class VideoFileScanner:
    def __init__(self, 
                 onedrive_service: Optional[IOneDriveService] = None,
                 progress_reporter: Optional[IProgressReporter] = None,
                 hash_service: Optional[IHashService] = None):
        """
        Scanner must accept injected dependencies for testability
        
        Args:
            onedrive_service: OneDrive integration service
            progress_reporter: Progress reporting callback interface  
            hash_service: Hash computation and comparison service
        """
        pass
```

### Configuration Contract
```python
@dataclass
class CloudScanConfig:
    """Configuration for cloud scanning behavior"""
    
    # OneDrive behavior
    enable_onedrive: bool = True
    api_timeout_seconds: int = 30
    max_api_retries: int = 3
    batch_size: int = 20
    
    # Fallback behavior
    compute_local_hash_for_cloud: bool = True
    skip_cloud_on_auth_failure: bool = False
    
    # Performance tuning
    metadata_cache_ttl_minutes: int = 30
    concurrent_api_requests: int = 5
```
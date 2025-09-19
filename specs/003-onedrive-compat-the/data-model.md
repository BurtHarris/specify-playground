# Data Model: OneDrive Integration and Compatibility

**Created**: September 18, 2025  
**Phase**: 1 - Design & Contracts  
**Dependencies**: research.md  

## Core Entity Extensions

### VideoFile (Enhanced)
```python
@dataclass
class VideoFile:
    """Enhanced video file representation with cloud storage support"""
    path: Path
    size: int
    _hash: Optional[str] = None
    
    # New cloud-specific properties
    cloud_status: CloudFileStatus = CloudFileStatus.LOCAL
    cloud_hash: Optional[str] = None
    cloud_hash_algorithm: Optional[str] = None
    onedrive_item_id: Optional[str] = None
    
    @property
    def hash(self) -> str:
        """Priority: cloud_hash if available, otherwise compute local hash"""
        if self.cloud_hash and self.cloud_status != CloudFileStatus.LOCAL:
            return self.cloud_hash
        if self._hash is None:
            self._hash = self._compute_hash()
        return self._hash
    
    @property
    def effective_hash_algorithm(self) -> str:
        """Returns the algorithm used for the current hash value"""
        return self.cloud_hash_algorithm or "BLAKE2b"
    
    def is_cloud_file(self) -> bool:
        """Check if file is stored in cloud (OneDrive)"""
        return self.cloud_status != CloudFileStatus.LOCAL
```

### CloudFileStatus (New Enum)
```python
from enum import Enum

class CloudFileStatus(Enum):
    """OneDrive file synchronization status"""
    LOCAL = "local"                    # Regular local file
    CLOUD_ONLY = "cloud_only"         # OneDrive placeholder, no local content
    LOCALLY_AVAILABLE = "available"   # Cached locally, can go cloud-only
    ALWAYS_LOCAL = "pinned"           # User-pinned to stay local
    UNKNOWN = "unknown"               # Status could not be determined
```

### OneDriveMetadata (New)
```python
@dataclass
class OneDriveMetadata:
    """OneDrive-specific file metadata from Graph API"""
    item_id: str
    quick_xor_hash: Optional[str] = None
    sha1_hash: Optional[str] = None
    crc32_hash: Optional[str] = None
    size: int = 0
    mime_type: Optional[str] = None
    last_modified: Optional[datetime] = None
    
    @property
    def best_hash(self) -> Tuple[Optional[str], Optional[str]]:
        """Returns (hash_value, algorithm_name) for best available hash"""
        if self.sha1_hash:
            return (self.sha1_hash, "SHA1")
        if self.quick_xor_hash:
            return (self.quick_xor_hash, "QuickXorHash")
        if self.crc32_hash:
            return (self.crc32_hash, "CRC32")
        return (None, None)
```

### ScanResult (Enhanced)
```python
@dataclass 
class ScanResult:
    """Enhanced scan results with cloud file support"""
    duplicate_groups: List[DuplicateGroup]
    potential_matches: List[PotentialMatchGroup]
    metadata: ScanMetadata
    
    # New cloud-specific statistics
    cloud_stats: CloudScanStatistics
    
    def get_cloud_duplicates(self) -> List[DuplicateGroup]:
        """Get duplicate groups containing OneDrive files"""
        return [group for group in self.duplicate_groups 
                if any(file.is_cloud_file() for file in group.files)]
    
    def get_mixed_duplicates(self) -> List[DuplicateGroup]:
        """Get duplicate groups with both local and cloud files"""
        return [group for group in self.duplicate_groups
                if (any(file.is_cloud_file() for file in group.files) and
                    any(not file.is_cloud_file() for file in group.files))]
```

### CloudScanStatistics (New)
```python
@dataclass
class CloudScanStatistics:
    """Statistics specific to cloud file scanning"""
    total_cloud_files: int = 0
    cloud_only_files: int = 0
    locally_available_files: int = 0
    cloud_files_with_hashes: int = 0
    api_requests_made: int = 0
    api_rate_limited: int = 0
    offline_cloud_files: int = 0  # Files skipped due to API unavailability
    
    @property
    def cloud_hash_coverage(self) -> float:
        """Percentage of cloud files with available hash information"""
        if self.total_cloud_files == 0:
            return 0.0
        return (self.cloud_files_with_hashes / self.total_cloud_files) * 100
```

## Service Layer Entities

### OneDriveService (New)
```python
class OneDriveService:
    """Service for OneDrive file detection and metadata retrieval"""
    
    def __init__(self, graph_client: Optional[GraphServiceClient] = None):
        self.graph_client = graph_client
        self.metadata_cache: Dict[str, OneDriveMetadata] = {}
    
    async def detect_cloud_status(self, file_path: Path) -> CloudFileStatus:
        """Detect if file is OneDrive-managed and its sync status"""
        pass
    
    async def get_file_metadata(self, file_path: Path) -> Optional[OneDriveMetadata]:
        """Retrieve OneDrive metadata for file via Graph API"""
        pass
    
    def is_onedrive_directory(self, directory: Path) -> bool:
        """Check if directory is managed by OneDrive"""
        pass
    
    async def batch_get_metadata(self, file_paths: List[Path]) -> Dict[Path, OneDriveMetadata]:
        """Efficiently retrieve metadata for multiple files"""
        pass
```

### VideoFileScanner (Enhanced)
```python
class VideoFileScanner:
    """Enhanced scanner with OneDrive integration"""
    
    def __init__(self, onedrive_service: Optional[OneDriveService] = None):
        self.onedrive_service = onedrive_service
    
    async def scan_directory(self, 
                           directory: Path, 
                           recursive: bool = True,
                           include_cloud: bool = True) -> ScanResult:
        """Enhanced scan with cloud file support"""
        pass
    
    async def _process_cloud_file(self, file_path: Path) -> VideoFile:
        """Process OneDrive file without triggering download"""
        pass
    
    def _should_include_cloud_file(self, status: CloudFileStatus) -> bool:
        """Determine if cloud file should be included in scan"""
        pass
```

## Hash Compatibility Matrix

### Supported Hash Algorithms
```python
class HashAlgorithm(Enum):
    BLAKE2B = "BLAKE2b"           # Current default, local computation
    QUICK_XOR = "QuickXorHash"    # OneDrive native, from Graph API
    SHA1 = "SHA1"                 # OneDrive secondary, widely compatible
    CRC32 = "CRC32"               # OneDrive backup, fast but collision-prone

class HashComparator:
    """Handles cross-algorithm hash comparison for duplicate detection"""
    
    @staticmethod
    def can_compare(hash1_algo: str, hash2_algo: str) -> bool:
        """Check if two hash algorithms are compatible for comparison"""
        # Same algorithm always comparable
        if hash1_algo == hash2_algo:
            return True
        
        # Cross-algorithm comparison not supported
        return False
    
    @staticmethod
    def normalize_hash(hash_value: str, algorithm: str) -> str:
        """Normalize hash value for comparison"""
        if algorithm == "QuickXorHash":
            # QuickXorHash is base64-encoded, convert to hex for consistency
            return base64.b64decode(hash_value).hex()
        return hash_value.lower()
```

## Data Flow Patterns

### Cloud File Discovery Flow
```
1. Directory Scan → Check if OneDrive directory
2. File Discovery → Detect cloud status for each video file
3. Metadata Retrieval → Batch request OneDrive metadata
4. Hash Processing → Use cloud hash or compute locally
5. Duplicate Detection → Cross-compare with hash compatibility
```

### Mixed Environment Scenarios
```
Scenario A: Local + Cloud duplicates
├── local_video.mp4 (BLAKE2b hash)
└── cloud_video.mp4 (QuickXorHash) 
    → Requires local computation for comparison

Scenario B: Cloud-only duplicates  
├── cloud_video1.mp4 (QuickXorHash)
└── cloud_video2.mp4 (QuickXorHash)
    → Direct QuickXorHash comparison

Scenario C: Offline cloud files
├── cloud_video.mp4 (no API access)
└── local_video.mp4 (BLAKE2b hash)
    → Skip cloud file or use local heuristics
```

## Error Handling Patterns

### Cloud Service Failures
```python
class CloudServiceError(Exception):
    """Base exception for cloud service issues"""
    pass

class OneDriveAPIError(CloudServiceError):
    """Graph API specific errors"""
    pass

class OneDriveAuthError(CloudServiceError): 
    """Authentication/authorization failures"""
    pass

class OneDriveRateLimitError(CloudServiceError):
    """API rate limiting encountered"""
    pass
```

### Graceful Degradation Strategy
```
1. API Unavailable → Skip cloud-only files, process local files normally
2. Authentication Failed → Prompt for re-auth or continue local-only
3. Rate Limited → Implement exponential backoff, cache aggressively
4. Partial Metadata → Use available information, mark incomplete
```

## CLI Output Extensions

### Enhanced Output Format
```yaml
# Example YAML output with cloud information
scan_metadata:
  cloud_stats:
    total_cloud_files: 15
    cloud_only_files: 8
    locally_available_files: 7
    cloud_hash_coverage: 87.5

duplicate_groups:
  - group_id: 1
    files:
      - path: "/local/video.mp4"
        size: 1024000
        hash: "blake2b_hash_value"
        cloud_status: "local"
      - path: "/OneDrive/video.mp4" 
        size: 1024000
        hash: "quick_xor_hash_value"
        hash_algorithm: "QuickXorHash"
        cloud_status: "cloud_only"
        onedrive_item_id: "item_123"
    total_size: 2048000
    file_size: 1024000
    cloud_mixed: true
```

## Validation Rules

### Data Integrity Constraints
- CloudFileStatus must be set for all files in OneDrive directories
- OneDrive metadata must include item_id when cloud_status != LOCAL
- Hash values must be valid for their declared algorithm
- Cloud statistics must sum correctly across categories

### Business Logic Constraints  
- Cloud-only files cannot have locally computed hashes
- API rate limiting must be respected (max 10,000 requests/hour)
- Authentication errors must not fail entire scan
- Mixed duplicate groups must clearly indicate file locations
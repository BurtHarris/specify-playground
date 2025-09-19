# Research: OneDrive Integration and Compatibility

**Created**: September 18, 2025  
**Phase**: 0 - Research & Technical Investigation  
**Status**: Complete

## OneDrive Hash Access Research

### OneDrive File Hashing Mechanisms

**Primary Hash Types Available:**
- **QuickXorHash**: OneDrive's proprietary hash algorithm for file integrity
  - Available via Microsoft Graph API `/me/drive/items/{item-id}` endpoint
  - Exposed in `file.hashes.quickXorHash` property
  - Base64-encoded, efficient for duplicate detection
  - Consistent across OneDrive clients and platforms

- **SHA1Hash**: Standard SHA-1 hashes when available
  - Available via `file.hashes.sha1Hash` property
  - Not guaranteed for all files (computed on-demand)
  - More CPU-intensive but widely compatible

- **CRC32Hash**: Cyclic redundancy check for basic integrity
  - Available via `file.hashes.crc32Hash` property
  - Fast but less suitable for duplicate detection

### Microsoft Graph API Access Methods

**Authentication Options:**
1. **Delegated Permissions** (User Context)
   - Uses existing user's OneDrive credentials
   - Requires `Files.Read` or `Files.ReadWrite` scope
   - Best for personal OneDrive scanning

2. **Application Permissions** (Service Context)
   - Requires `Files.Read.All` or `Files.ReadWrite.All`
   - Needs admin consent for organizational access
   - Not suitable for personal file scanning

**API Endpoints for File Metadata:**
```
GET /me/drive/items/{item-id}
GET /me/drive/root:/{path}
GET /me/drive/items/{item-id}/children
```

**Response Structure:**
```json
{
  "id": "file-id",
  "name": "video.mp4",
  "size": 1024000,
  "file": {
    "mimeType": "video/mp4",
    "hashes": {
      "quickXorHash": "base64-encoded-hash",
      "sha1Hash": "hex-encoded-sha1",
      "crc32Hash": "hex-encoded-crc32"
    }
  },
  "@microsoft.graph.downloadUrl": "temporary-download-url"
}
```

## OneDrive File Detection Research

### Local OneDrive Integration Detection

**Windows Detection:**
- OneDrive folders marked with `FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS` attribute
- Registry keys: `HKCU\Software\Microsoft\OneDrive\Accounts`
- OneDrive status via `attrib` command shows `O` attribute for cloud files

**macOS Detection:**
- OneDrive files have extended attributes: `com.microsoft.OneDrive.status`
- Cloud-only files show as aliases with special metadata
- Finder integration provides sync status information

**Linux Detection:**
- OneDrive for Linux stores metadata in `~/.config/onedrive/`
- File status can be queried via OneDrive Linux client APIs
- Limited native integration compared to Windows/macOS

### File Sync Status Categories

1. **Available locally** - Full file content on disk
2. **Available online-only** - Placeholder/stub file, content in cloud
3. **Locally available** - Recently accessed, temporarily cached
4. **Always keep on this device** - User-pinned files

## Python Integration Libraries

### Microsoft Graph SDK for Python
```python
# Installation: pip install msgraph-sdk
from msgraph import GraphServiceClient
from azure.identity import DefaultAzureCredential

# Authentication
credential = DefaultAzureCredential()
client = GraphServiceClient(credentials=credential)

# Get file metadata with hashes
file_info = await client.me.drive.items.by_drive_item_id(item_id).get()
quick_xor_hash = file_info.file.hashes.quick_xor_hash
```

### OneDrive SDK (Legacy)
```python
# Installation: pip install onedrivesdk
# Note: Deprecated, prefer Graph SDK
```

### Platform-Specific File Status Detection

**Windows - Win32 API:**
```python
import ctypes
from ctypes import wintypes

def is_onedrive_placeholder(file_path):
    attrs = ctypes.windll.kernel32.GetFileAttributesW(file_path)
    return bool(attrs & 0x00400000)  # FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS
```

**Cross-Platform - File Size Heuristics:**
```python
import os
from pathlib import Path

def detect_cloud_placeholder(file_path):
    # Cloud placeholders often have 0 or minimal size
    # but show larger size in metadata
    stat = os.stat(file_path)
    return stat.st_size == 0 and file_path.suffix in VIDEO_EXTENSIONS
```

## Technical Challenges & Solutions

### Challenge 1: Authentication Management
**Problem**: Graph API requires OAuth2 flow
**Solution**: Leverage existing user authentication via default credentials or cached tokens

### Challenge 2: Rate Limiting
**Problem**: Graph API has throttling limits (approximately 10,000 requests/hour)
**Solution**: Batch requests, implement exponential backoff, cache metadata locally

### Challenge 3: Hash Algorithm Compatibility
**Problem**: QuickXorHash is OneDrive-specific, not compatible with existing BLAKE2b
**Solution**: Support multiple hash algorithms, normalize for comparison, maintain compatibility matrix

### Challenge 4: Offline Scenarios
**Problem**: API access requires internet connectivity
**Solution**: Graceful degradation to local file analysis when API unavailable

## Performance Considerations

### API Request Optimization
- Batch file metadata requests (up to 20 items per batch)
- Use `$select` query parameter to request only needed fields
- Implement request caching with appropriate TTL

### Memory Efficiency
- Stream large directory traversals
- Avoid downloading file content unnecessarily
- Use pagination for large folder structures

### Network Efficiency
- Prefer metadata-only operations
- Implement request coalescing for similar operations
- Use conditional requests with ETags when possible

## Security & Privacy Implications

### Data Access Scope
- Minimize requested permissions to `Files.Read`
- Respect user's OneDrive sharing and privacy settings
- No persistent storage of authentication tokens

### Audit Trail
- Log API access patterns for debugging
- Avoid logging sensitive file metadata
- Respect organizational data governance policies

## Implementation Recommendations

### Primary Approach
1. **Hybrid Detection**: Combine local file attribute detection with Graph API metadata
2. **Hash Preference**: Use QuickXorHash when available, fallback to local computation
3. **Graceful Degradation**: Function without API access for local files

### Fallback Strategy
1. Detect OneDrive folders using platform-specific methods
2. Attempt Graph API authentication
3. If API available: Use cloud metadata for enhanced duplicate detection
4. If API unavailable: Skip cloud-only files or use local heuristics

### Integration Points
- Extend existing `VideoFile` model with cloud status and hash source
- Add `OneDriveService` alongside existing `VideoFileScanner`
- Modify CLI output to indicate cloud vs local file status

## Research Conclusions

**Key Findings:**
- OneDrive provides robust hash information via QuickXorHash algorithm
- Microsoft Graph API offers comprehensive metadata access without forcing downloads
- Platform-specific detection mechanisms can identify OneDrive files reliably
- Authentication complexity manageable through existing credential providers

**Technical Feasibility**: ✅ **HIGH** - Well-documented APIs and SDK support  
**Implementation Complexity**: 🟡 **MEDIUM** - Requires OAuth integration and multi-platform testing  
**Performance Impact**: 🟢 **LOW** - Metadata-only operations are efficient  

**Next Steps**: Proceed to Phase 1 design with focus on Graph SDK integration and hybrid file detection approach.
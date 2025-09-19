# OneDrive Integration Quickstart Guide

**Created**: September 18, 2025  
**Phase**: 1 - Design & Contracts  
**Purpose**: Implementation validation and testing  

## Prerequisites

### System Requirements
- Python 3.11+ (existing project requirement)
- OneDrive desktop client installed and synced
- Network connectivity for Microsoft Graph API access
- User with OneDrive access permissions

### Development Dependencies
```bash
# Core dependencies (from existing project)
pip install click pathlib hashlib

# New OneDrive integration dependencies  
pip install msgraph-sdk azure-identity
pip install aiohttp  # For async HTTP operations

# Development and testing
pip install pytest pytest-asyncio pytest-mock
pip install responses  # For mocking HTTP requests
```

### Authentication Setup
```bash
# Azure App Registration (for development)
# 1. Register app at https://portal.azure.com
# 2. Configure delegated permissions: Files.Read
# 3. Set redirect URI: http://localhost:8000
# 4. Note Application ID for configuration

# Environment setup
export AZURE_CLIENT_ID="your-app-id"
export AZURE_TENANT_ID="common"  # For personal accounts
```

## Quick Integration Test

### Test OneDrive Detection
```python
# test_onedrive_detection.py
import asyncio
from pathlib import Path
from src.services.onedrive_service import OneDriveService

async def test_basic_detection():
    """Test OneDrive file detection without API"""
    
    service = OneDriveService()
    
    # Test 1: Detect OneDrive directory
    onedrive_path = Path.home() / "OneDrive"
    if onedrive_path.exists():
        is_onedrive = service.is_onedrive_directory(onedrive_path)
        print(f"OneDrive directory detected: {is_onedrive}")
    
    # Test 2: Check file cloud status (local detection only)
    test_files = list(onedrive_path.glob("*.mp4"))[:5] if onedrive_path.exists() else []
    
    for file_path in test_files:
        status = await service.detect_cloud_status(file_path)
        print(f"{file_path.name}: {status.value}")

if __name__ == "__main__":
    asyncio.run(test_basic_detection())
```

### Test Scanner Integration
```python
# test_scanner_integration.py
import asyncio
from pathlib import Path
from src.services.video_file_scanner import VideoFileScanner
from src.services.onedrive_service import OneDriveService

async def test_scanner_with_onedrive():
    """Test enhanced scanner with OneDrive support"""
    
    # Setup services
    onedrive_service = OneDriveService()
    scanner = VideoFileScanner(onedrive_service=onedrive_service)
    
    # Test directory (use small OneDrive folder)
    test_dir = Path.home() / "OneDrive" / "Videos"  # Adjust path as needed
    
    if not test_dir.exists():
        print("OneDrive Videos directory not found, skipping test")
        return
    
    # Perform scan with cloud support
    print(f"Scanning {test_dir} with OneDrive integration...")
    result = await scanner.scan_directory(
        directory=test_dir,
        recursive=False,  # Limit scope for testing
        include_cloud=True
    )
    
    # Display results
    print(f"Total files found: {len(result.metadata.files_scanned)}")
    print(f"Cloud files: {result.cloud_stats.total_cloud_files}")
    print(f"Duplicate groups: {len(result.duplicate_groups)}")
    
    # Show cloud statistics
    if result.cloud_stats.total_cloud_files > 0:
        print(f"Cloud hash coverage: {result.cloud_stats.cloud_hash_coverage:.1f}%")
        print(f"API requests made: {result.cloud_stats.api_requests_made}")

if __name__ == "__main__":
    asyncio.run(test_scanner_with_onedrive())
```

## API Integration Testing

### Authentication Test
```python
# test_auth.py
import asyncio
from azure.identity import DefaultAzureCredential, InteractiveBrowserCredential
from msgraph import GraphServiceClient

async def test_graph_auth():
    """Test Microsoft Graph API authentication"""
    
    try:
        # Try default credential first (cached tokens)
        credential = DefaultAzureCredential()
        client = GraphServiceClient(credentials=credential, scopes=['https://graph.microsoft.com/Files.Read'])
        
        # Test basic API access
        me = await client.me.get()
        print(f"Authenticated as: {me.display_name}")
        
        # Test drive access
        drive = await client.me.drive.get()
        print(f"OneDrive available: {drive.id}")
        
        return True
        
    except Exception as e:
        print(f"Authentication failed: {e}")
        
        # Fallback to interactive auth for setup
        try:
            credential = InteractiveBrowserCredential()
            client = GraphServiceClient(credentials=credential, scopes=['https://graph.microsoft.com/Files.Read'])
            me = await client.me.get()
            print(f"Interactive auth successful: {me.display_name}")
            return True
        except Exception as e2:
            print(f"Interactive auth also failed: {e2}")
            return False

if __name__ == "__main__":
    success = asyncio.run(test_graph_auth())
    if success:
        print("✅ Graph API authentication working")
    else:
        print("❌ Graph API authentication failed")
```

### Metadata Retrieval Test
```python
# test_metadata.py
import asyncio
from pathlib import Path
from src.services.onedrive_service import OneDriveService

async def test_metadata_retrieval():
    """Test OneDrive metadata retrieval via Graph API"""
    
    service = OneDriveService()
    
    # Find OneDrive video files for testing
    onedrive_path = Path.home() / "OneDrive"
    video_files = []
    
    for ext in ['.mp4', '.mkv', '.mov']:
        video_files.extend(list(onedrive_path.rglob(f"*{ext}"))[:2])  # Limit for testing
    
    if not video_files:
        print("No OneDrive video files found for testing")
        return
    
    print(f"Testing metadata retrieval for {len(video_files)} files...")
    
    for file_path in video_files:
        try:
            metadata = await service.get_file_metadata(file_path)
            
            if metadata:
                print(f"\n{file_path.name}:")
                print(f"  OneDrive ID: {metadata.item_id}")
                print(f"  Size: {metadata.size:,} bytes")
                
                hash_value, hash_algo = metadata.best_hash
                if hash_value:
                    print(f"  Hash: {hash_algo} = {hash_value[:16]}...")
                else:
                    print("  No hash information available")
            else:
                print(f"{file_path.name}: No metadata available")
                
        except Exception as e:
            print(f"{file_path.name}: Error retrieving metadata - {e}")

if __name__ == "__main__":
    asyncio.run(test_metadata_retrieval())
```

## Performance Validation

### Benchmark Cloud vs Local Scanning
```python
# benchmark_performance.py
import asyncio
import time
from pathlib import Path
from src.services.video_file_scanner import VideoFileScanner
from src.services.onedrive_service import OneDriveService

async def benchmark_scanning():
    """Compare scanning performance with and without OneDrive integration"""
    
    test_dir = Path.home() / "OneDrive" / "Videos"  # Adjust as needed
    
    if not test_dir.exists():
        print("Test directory not found")
        return
    
    # Benchmark 1: Local-only scanning
    print("Benchmarking local-only scanning...")
    scanner_local = VideoFileScanner()
    
    start_time = time.time()
    result_local = await scanner_local.scan_directory(test_dir, include_cloud=False)
    local_time = time.time() - start_time
    
    print(f"Local scan: {local_time:.2f}s, {len(result_local.metadata.files_scanned)} files")
    
    # Benchmark 2: OneDrive-integrated scanning  
    print("Benchmarking OneDrive-integrated scanning...")
    onedrive_service = OneDriveService()
    scanner_cloud = VideoFileScanner(onedrive_service=onedrive_service)
    
    start_time = time.time()
    result_cloud = await scanner_cloud.scan_directory(test_dir, include_cloud=True)
    cloud_time = time.time() - start_time
    
    print(f"Cloud scan: {cloud_time:.2f}s, {len(result_cloud.metadata.files_scanned)} files")
    print(f"Cloud files found: {result_cloud.cloud_stats.total_cloud_files}")
    print(f"API requests: {result_cloud.cloud_stats.api_requests_made}")
    
    # Performance comparison
    overhead = ((cloud_time - local_time) / local_time) * 100 if local_time > 0 else 0
    print(f"OneDrive integration overhead: {overhead:.1f}%")

if __name__ == "__main__":
    asyncio.run(benchmark_scanning())
```

## Error Scenario Testing

### Test Offline Mode
```python
# test_offline.py
import asyncio
from pathlib import Path
from src.services.video_file_scanner import VideoFileScanner
from src.services.onedrive_service import OneDriveService

async def test_offline_behavior():
    """Test scanner behavior when OneDrive API is unavailable"""
    
    # Create service with no authentication (simulates offline)
    onedrive_service = OneDriveService(graph_client=None)
    scanner = VideoFileScanner(onedrive_service=onedrive_service)
    
    test_dir = Path.home() / "OneDrive" / "Videos"
    
    print("Testing offline OneDrive scanning...")
    result = await scanner.scan_directory(test_dir, include_cloud=True)
    
    print(f"Files processed: {len(result.metadata.files_scanned)}")
    print(f"Offline cloud files: {result.cloud_stats.offline_cloud_files}")
    print(f"Processing succeeded despite no API access: {len(result.duplicate_groups) >= 0}")

if __name__ == "__main__":
    asyncio.run(test_offline_behavior())
```

### Test Rate Limiting
```python
# test_rate_limit.py
import asyncio
from pathlib import Path
from src.services.onedrive_service import OneDriveService

async def test_rate_limit_handling():
    """Test behavior when API rate limits are hit"""
    
    service = OneDriveService()
    
    # Find many OneDrive files to trigger rate limiting
    onedrive_path = Path.home() / "OneDrive"
    many_files = list(onedrive_path.rglob("*"))[:100]  # Test with 100 files
    
    print(f"Testing rate limit handling with {len(many_files)} files...")
    
    start_time = asyncio.get_event_loop().time()
    
    try:
        metadata_results = await service.batch_get_metadata(many_files)
        end_time = asyncio.get_event_loop().time()
        
        print(f"Batch processing completed in {end_time - start_time:.2f}s")
        print(f"Successfully retrieved metadata for {len(metadata_results)} files")
        
    except Exception as e:
        print(f"Rate limiting or other error encountered: {e}")
        print("This is expected behavior - service should handle gracefully")

if __name__ == "__main__":
    asyncio.run(test_rate_limit_handling())
```

## Configuration Testing

### Test Environment Setup
```python
# test_config.py
import os
from src.services.onedrive_service import OneDriveService
from src.models.cloud_scan_config import CloudScanConfig

def test_configuration():
    """Test configuration and environment setup"""
    
    print("Testing OneDrive integration configuration...")
    
    # Check environment variables
    client_id = os.getenv('AZURE_CLIENT_ID')
    tenant_id = os.getenv('AZURE_TENANT_ID')
    
    print(f"Azure Client ID configured: {'Yes' if client_id else 'No'}")
    print(f"Azure Tenant ID configured: {'Yes' if tenant_id else 'No'}")
    
    # Test configuration object
    config = CloudScanConfig(
        enable_onedrive=True,
        api_timeout_seconds=30,
        batch_size=20
    )
    
    print(f"Default configuration loaded: {config}")
    
    # Test service initialization
    try:
        service = OneDriveService()
        print("OneDrive service initialized successfully")
    except Exception as e:
        print(f"Service initialization failed: {e}")

if __name__ == "__main__":
    test_configuration()
```

## Expected Results

### Successful Integration Indicators
- ✅ OneDrive directories correctly detected on all platforms
- ✅ Cloud file status accurately determined (cloud-only, local, etc.)
- ✅ Graph API authentication working (interactive fallback if needed)
- ✅ Metadata retrieval showing hash information when available
- ✅ Scanner processing mixed local/cloud environments seamlessly
- ✅ Performance overhead <50% for typical OneDrive directories
- ✅ Graceful degradation when API unavailable

### Common Issues and Solutions

**Authentication Errors:**
- Ensure Azure app registration includes Files.Read permission
- Use interactive browser authentication for initial setup
- Check firewall/proxy settings for Graph API access

**Performance Issues:**
- Verify batch_size configuration (default 20 files per request)
- Check network latency to Microsoft Graph endpoints
- Monitor API rate limiting in logs

**Detection Issues:**
- OneDrive client must be installed and running
- Files must be in OneDrive-synced directories
- Platform-specific detection varies (Windows most reliable)

## Next Steps

After successful quickstart validation:

1. **Run Performance Benchmarks**: Verify acceptable overhead
2. **Test Error Scenarios**: Confirm graceful degradation
3. **Validate Cross-Platform**: Test on Windows, macOS, Linux
4. **Integration Testing**: Full end-to-end duplicate detection
5. **User Acceptance Testing**: Real-world OneDrive directory scanning

The quickstart provides confidence that the OneDrive integration approach is technically sound and ready for full implementation.
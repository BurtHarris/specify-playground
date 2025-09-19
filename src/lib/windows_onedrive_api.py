"""
Windows OneDrive API detection utility for OneDrive Integration MVP.

This module provides Windows-specific functionality to detect OneDrive cloud file status
using Windows API file attributes. Uses ctypes to access FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS
for detecting cloud-only files.

MVP Scope:
- Local detection only (no Graph API)
- Windows platform only
- ctypes.windll.kernel32 for file attribute access
- Simple LOCAL/CLOUD_ONLY status detection
"""

import ctypes
import platform
from pathlib import Path
from typing import Optional

from ..models.cloud_file_status import CloudFileStatus


# Windows API constants
FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS = 0x00400000
INVALID_FILE_ATTRIBUTES = 0xFFFFFFFF


class WindowsOneDriveAPIError(Exception):
    """Raised when Windows OneDrive API operations fail."""
    pass


def is_windows_platform() -> bool:
    """
    Check if running on Windows platform.
    
    Returns:
        bool: True if Windows, False otherwise
    """
    return platform.system().lower() == "windows"


def detect_cloud_status(file_path: Path) -> CloudFileStatus:
    """
    Detect OneDrive cloud status for a file using Windows API.
    
    Args:
        file_path: Path to the file to check
        
    Returns:
        CloudFileStatus: LOCAL if file is local, CLOUD_ONLY if cloud-only
        
    Raises:
        WindowsOneDriveAPIError: If Windows API call fails
        OSError: If file does not exist or is inaccessible
        RuntimeError: If called on non-Windows platform
    """
    if not is_windows_platform():
        raise RuntimeError("OneDrive detection only supported on Windows platform")
    
    if not file_path.exists():
        raise OSError(f"File not found: {file_path}")
    
    try:
        # Get file attributes using Windows API
        attributes = ctypes.windll.kernel32.GetFileAttributesW(str(file_path))
        
        if attributes == INVALID_FILE_ATTRIBUTES:
            # Get last error for better diagnostics
            error_code = ctypes.windll.kernel32.GetLastError()
            raise WindowsOneDriveAPIError(
                f"Failed to get file attributes for {file_path}, error code: {error_code}"
            )
        
        # Check if file has recall-on-data-access attribute (cloud-only)
        if attributes & FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS:
            return CloudFileStatus.CLOUD_ONLY
        else:
            return CloudFileStatus.LOCAL
            
    except OSError:
        # Re-raise file system errors
        raise
    except Exception as e:
        # Wrap other exceptions in our custom error
        raise WindowsOneDriveAPIError(f"Windows API error detecting cloud status: {e}") from e


def detect_cloud_status_safe(file_path: Path) -> Optional[CloudFileStatus]:
    """
    Safely detect OneDrive cloud status, returning None on any error.
    
    This is the recommended function for production use where you want
    graceful degradation when detection fails.
    
    Args:
        file_path: Path to the file to check
        
    Returns:
        CloudFileStatus or None: Status if detected successfully, None on any error
    """
    try:
        return detect_cloud_status(file_path)
    except Exception:
        # Graceful degradation - return None for any error
        return None


def is_onedrive_supported() -> bool:
    """
    Check if OneDrive detection is supported on current platform.
    
    Returns:
        bool: True if Windows platform (OneDrive detection supported)
    """
    return is_windows_platform()


def get_platform_info() -> dict:
    """
    Get platform information for diagnostics.
    
    Returns:
        dict: Platform information including OS, version, and OneDrive support
    """
    return {
        "platform": platform.system(),
        "version": platform.version(),
        "onedrive_supported": is_onedrive_supported(),
        "api_available": is_windows_platform()
    }
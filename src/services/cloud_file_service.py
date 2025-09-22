"""
OneDrive cloud file service for Windows API integration.

This module provides CloudFileService for detecting OneDrive cloud file status
using Windows file attributes. MVP scope focuses on local detection only.
"""

import ctypes
import platform
from pathlib import Path
from typing import Union

from src.models.cloud_file_status import CloudFileStatus


class CloudFileService:
    """
    Service for detecting OneDrive cloud file status using Windows API.

    This service uses Windows file attributes to determine if a file is:
    - LOCAL: Fully available locally (can be processed normally)
    - CLOUD_ONLY: Cloud-only stub (should be skipped during processing)

    MVP scope: Windows-only detection using FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS
    """

    # Windows API constants
    FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS = 0x00400000
    INVALID_FILE_ATTRIBUTES = 0xFFFFFFFF

    def __init__(self):
        """Initialize CloudFileService."""
        self._is_windows = platform.system() == "Windows"
        self._has_windll = hasattr(ctypes, "windll")

    def get_file_status(self, file_path: Union[str, Path]) -> CloudFileStatus:
        """
        Get OneDrive cloud status for a file using Windows API.

        Args:
            file_path: Path to the file to check (string or Path object)

        Returns:
            CloudFileStatus indicating whether file is local or cloud-only

        Note:
            Returns LOCAL on non-Windows platforms or if API call fails.
            This provides graceful fallback behavior.
        """
        try:
            # Convert to Path object for consistent handling
            path = Path(file_path) if isinstance(file_path, str) else file_path

            # Only works on Windows with windll available
            if not self._is_windows or not self._has_windll:
                return CloudFileStatus.LOCAL

            # Get file attributes using Windows API
            # GetFileAttributesW for Unicode support
            attributes = ctypes.windll.kernel32.GetFileAttributesW(str(path))

            # Check for API call failure
            if attributes == self.INVALID_FILE_ATTRIBUTES:
                # Failed to get attributes - assume local (conservative approach)
                return CloudFileStatus.LOCAL

            # Check if file has recall-on-data-access attribute
            if attributes & self.FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS:
                return CloudFileStatus.CLOUD_ONLY
            else:
                return CloudFileStatus.LOCAL

        except (OSError, AttributeError, TypeError):
            # Fallback to LOCAL on any error (conservative approach)
            return CloudFileStatus.LOCAL

    def is_windows_only(self) -> bool:
        """
        Check if this service is Windows-only.

        Returns:
            True if service only works on Windows platforms
        """
        return True

    def is_supported(self) -> bool:
        """
        Check if OneDrive detection is supported on current platform.

        Returns:
            True if OneDrive detection is supported, False otherwise
        """
        return self._is_windows and self._has_windll

    def get_platform_info(self) -> dict:
        """
        Get platform information for diagnostics.

        Returns:
            Dictionary with platform detection details
        """
        return {
            "platform": platform.system(),
            "is_windows": self._is_windows,
            "has_windll": self._has_windll,
            "supported": self.is_supported(),
        }

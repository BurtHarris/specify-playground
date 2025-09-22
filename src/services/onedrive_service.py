"""
OneDrive Service MVP Implementation for cloud file detection.

This service provides OneDrive integration functionality for the universal file duplicate scanner.
MVP scope focuses on local Windows API detection without Graph API integration.

Key Features:
- Windows file attribute detection via Windows API
- Graceful degradation on non-Windows platforms
- CloudFileStatus detection for user files
- Integration with UserFileScanner pipeline
"""

from pathlib import Path
from typing import Optional

from ..models.cloud_file_status import CloudFileStatus
from ..lib.windows_onedrive_api import (
    detect_cloud_status_safe,
    is_onedrive_supported,
)


class OneDriveService:
    """
    OneDrive integration service for MVP implementation.

    Provides cloud file status detection using Windows API for local detection.
    Handles graceful degradation on non-Windows platforms.
    """

    def __init__(self):
        """Initialize OneDrive service with platform detection."""
        self._supported = is_onedrive_supported()

    def is_supported(self) -> bool:
        """
        Check if OneDrive detection is supported on current platform.

        Returns:
            bool: True if Windows platform (detection supported)
        """
        return self._supported

    def detect_cloud_status(self, file_path: Path) -> CloudFileStatus:
        """
        Detect cloud status for a video file.

        Args:
            file_path: Path to the video file

        Returns:
            CloudFileStatus: LOCAL if file is local, CLOUD_ONLY if cloud-only

        Raises:
            RuntimeError: If OneDrive detection not supported on platform
            OSError: If file doesn't exist or is inaccessible
            WindowsOneDriveAPIError: If Windows API call fails
        """
        if not self._supported:
            raise RuntimeError("OneDrive detection not supported on this platform")

        # Use the Windows API utility for detection
        from ..lib.windows_onedrive_api import detect_cloud_status

        return detect_cloud_status(file_path)

    def detect_cloud_status_safe(self, file_path: Path) -> Optional[CloudFileStatus]:
        """
        Safely detect cloud status with graceful error handling.

        This method never raises exceptions and returns None for any error.
        Recommended for production use in the scanning pipeline.

        Args:
            file_path: Path to the video file

        Returns:
            CloudFileStatus or None: Status if detected, None on error or unsupported platform
        """
        if not self._supported:
            # Graceful degradation - assume local on unsupported platforms
            return CloudFileStatus.LOCAL

        return detect_cloud_status_safe(file_path)

    def should_skip_file(self, file_path: Path) -> bool:
        """
        Determine if a file should be skipped during scanning due to cloud status.

        Args:
            file_path: Path to the video file

        Returns:
            bool: True if file should be skipped (cloud-only), False otherwise
        """
        status = self.detect_cloud_status_safe(file_path)

        # Skip only if we can confirm it's cloud-only
        # If detection fails, assume local and don't skip
        return status == CloudFileStatus.CLOUD_ONLY

    def is_cloud_only(self, file_path: Path) -> bool:
        """
        Check if a file is cloud-only (OneDrive stub).

        Args:
            file_path: Path to the video file

        Returns:
            bool: True if file is cloud-only, False otherwise (including errors)
        """
        return self.should_skip_file(file_path)

    def is_local(self, file_path: Path) -> bool:
        """
        Check if a file is locally available.

        Args:
            file_path: Path to the video file

        Returns:
            bool: True if file is local, False if cloud-only (assumes local on errors)
        """
        status = self.detect_cloud_status_safe(file_path)

        # Assume local if detection fails (graceful degradation)
        return status != CloudFileStatus.CLOUD_ONLY

    def get_service_info(self) -> dict:
        """
        Get service information for diagnostics and debugging.

        Returns:
            dict: Service status, platform support, and configuration
        """
        info = {
            "service": "OneDriveService",
            "version": "MVP-1.0",
            "supported": self._supported,
            "scope": "local_detection_only",
        }

        if self._supported:
            from ..lib.windows_onedrive_api import get_platform_info

            info["platform"] = get_platform_info()

        return info

#!/usr/bin/env python3
"""
Integration tests for Windows API OneDrive detection functionality.

Tests the Windows API detection components in a real environment,
validating that OneDrive cloud status detection works correctly
on Windows platforms.
"""

import pytest
import platform
from pathlib import Path
from unittest.mock import patch

from src.lib.windows_onedrive_api import (
    detect_cloud_status,
    detect_cloud_status_safe,
    is_windows_platform,
    is_onedrive_supported,
    get_platform_info,
    WindowsOneDriveAPIError,
)
from src.models.cloud_file_status import CloudFileStatus


class TestWindowsAPIDetectionIntegration:
    """Integration tests for Windows API OneDrive detection."""

    def test_platform_detection(self):
        """Test that platform detection works correctly."""
        # Should detect Windows correctly
        assert is_windows_platform() == (platform.system().lower() == "windows")
        assert is_onedrive_supported() == is_windows_platform()

    def test_platform_info_structure(self):
        """Test that platform info returns expected structure."""
        info = get_platform_info()

        assert isinstance(info, dict)
        assert "platform" in info
        assert "version" in info
        assert "onedrive_supported" in info
        assert "api_available" in info

        # Values should be consistent
        assert info["onedrive_supported"] == is_onedrive_supported()
        assert info["api_available"] == is_windows_platform()

    @pytest.mark.skipif(
        not is_windows_platform(), reason="Windows API tests require Windows"
    )
    def test_windows_api_with_real_file(self, tmp_path):
        """Test Windows API detection with a real file."""
        # Create a temporary test file
        test_file = tmp_path / "test_video.mp4"
        test_file.write_bytes(b"fake video content")

        # Should be able to detect status (likely LOCAL for temp files)
        status = detect_cloud_status(test_file)
        assert isinstance(status, CloudFileStatus)
        assert status in [CloudFileStatus.LOCAL, CloudFileStatus.CLOUD_ONLY]

    @pytest.mark.skipif(
        not is_windows_platform(), reason="Windows API tests require Windows"
    )
    def test_windows_api_safe_detection(self, tmp_path):
        """Test safe detection doesn't raise exceptions."""
        # Create a temporary test file
        test_file = tmp_path / "test_video.mp4"
        test_file.write_bytes(b"fake video content")

        # Safe detection should never raise
        status = detect_cloud_status_safe(test_file)
        assert status is None or isinstance(status, CloudFileStatus)

    @pytest.mark.skipif(
        not is_windows_platform(), reason="Windows API tests require Windows"
    )
    def test_windows_api_nonexistent_file_error(self):
        """Test that nonexistent files raise appropriate errors."""
        nonexistent = Path("nonexistent_file_12345.mp4")

        with pytest.raises(OSError):
            detect_cloud_status(nonexistent)

        # Safe version should return None
        status = detect_cloud_status_safe(nonexistent)
        assert status is None

    @pytest.mark.skipif(
        is_windows_platform(),
        reason="Non-Windows API tests require non-Windows",
    )
    def test_non_windows_platform_raises_error(self, tmp_path):
        """Test that non-Windows platforms raise appropriate errors."""
        test_file = tmp_path / "test_video.mp4"
        test_file.write_bytes(b"fake video content")

        with pytest.raises(
            RuntimeError, match="OneDrive detection only supported on Windows"
        ):
            detect_cloud_status(test_file)

        # Safe version should return None on non-Windows
        status = detect_cloud_status_safe(test_file)
        assert status is None

    @pytest.mark.skipif(
        not is_windows_platform(), reason="Windows API tests require Windows"
    )
    def test_windows_api_error_handling(self, tmp_path):
        """Test Windows API error handling with mocked failures."""
        # Create a real test file for proper mocking
        test_file = tmp_path / "test_file.mp4"
        test_file.write_bytes(b"test content")

        # Mock the Windows API to return failure
        with patch("ctypes.windll.kernel32.GetFileAttributesW") as mock_get_attrs:
            mock_get_attrs.return_value = 0xFFFFFFFF  # INVALID_FILE_ATTRIBUTES

            with patch("ctypes.windll.kernel32.GetLastError") as mock_get_error:
                mock_get_error.return_value = 2  # ERROR_FILE_NOT_FOUND

                with pytest.raises(WindowsOneDriveAPIError):
                    detect_cloud_status(test_file)

                # Safe version should handle the error
                status = detect_cloud_status_safe(test_file)
                assert status is None

    @pytest.mark.skipif(
        not is_windows_platform(), reason="Windows API tests require Windows"
    )
    def test_cloud_only_file_detection(self):
        """Test detection of cloud-only files (if available)."""
        # This test would need actual OneDrive cloud-only files
        # For now, we'll mock the API response
        test_file = Path("cloud_only_test.mp4")

        with patch("ctypes.windll.kernel32.GetFileAttributesW") as mock_get_attrs:
            with patch.object(Path, "exists", return_value=True):
                # Mock cloud-only file attributes
                mock_get_attrs.return_value = (
                    0x00400000  # FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS
                )

                status = detect_cloud_status(test_file)
                assert status == CloudFileStatus.CLOUD_ONLY

    @pytest.mark.skipif(
        not is_windows_platform(), reason="Windows API tests require Windows"
    )
    def test_local_file_detection(self):
        """Test detection of local files."""
        test_file = Path("local_test.mp4")

        with patch("ctypes.windll.kernel32.GetFileAttributesW") as mock_get_attrs:
            with patch.object(Path, "exists", return_value=True):
                # Mock local file attributes (no recall-on-data-access)
                mock_get_attrs.return_value = 0x00000020  # FILE_ATTRIBUTE_ARCHIVE

                status = detect_cloud_status(test_file)
                assert status == CloudFileStatus.LOCAL

    def test_integration_with_onedrive_service(self):
        """Test integration between Windows API and OneDriveService."""
        from src.services.onedrive_service import OneDriveService

        service = OneDriveService()

        # Service should initialize correctly
        assert service.is_supported() == is_onedrive_supported()

        # Service info should be consistent
        info = service.get_service_info()
        assert info["supported"] == is_onedrive_supported()

        if is_windows_platform():
            assert "platform" in info
            assert info["platform"]["onedrive_supported"] == True

    def test_error_propagation_through_service(self):
        """Test that errors propagate correctly through the service layer."""
        from src.services.onedrive_service import OneDriveService

        service = OneDriveService()
        nonexistent = Path("nonexistent_integration_test.mp4")

        if is_windows_platform():
            # Should raise error for nonexistent files
            with pytest.raises((OSError, RuntimeError)):
                service.detect_cloud_status(nonexistent)

            # Safe version should return None or LOCAL
            status = service.detect_cloud_status_safe(nonexistent)
            assert status in [None, CloudFileStatus.LOCAL]
        else:
            # Non-Windows should raise RuntimeError
            with pytest.raises(RuntimeError):
                service.detect_cloud_status(nonexistent)

            # Safe version should return LOCAL on non-Windows
            status = service.detect_cloud_status_safe(nonexistent)
            assert status == CloudFileStatus.LOCAL

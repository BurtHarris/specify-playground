#!/usr/bin/env python3
"""
Unit tests for Windows OneDrive API detection logic using mocks so tests
can run on non-Windows platforms.

These tests exercise the public functions in
`src.lib.windows_onedrive_api` by patching `platform.system`, `pathlib.Path.exists`,
and `ctypes.windll.kernel32` to produce deterministic code paths.
"""

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from src.lib import windows_onedrive_api as wapi
from src.models.cloud_file_status import CloudFileStatus


def test_non_windows_runtime_error_and_safe():
    # Simulate a non-Windows platform
    with patch("src.lib.windows_onedrive_api.platform.system", return_value="Linux"):
        assert wapi.is_windows_platform() is False

        with pytest.raises(RuntimeError):
            wapi.detect_cloud_status(Path("/non/windows/file.mp4"))

        assert wapi.detect_cloud_status_safe(Path("/non/windows/file.mp4")) is None


def test_file_not_exists_raises_and_safe_returns_none():
    # Simulate Windows platform but missing file
    with patch("src.lib.windows_onedrive_api.platform.system", return_value="Windows"):
        with patch.object(Path, "exists", return_value=False):
            with pytest.raises(OSError):
                wapi.detect_cloud_status(Path("C:/missing.mp4"))

            assert wapi.detect_cloud_status_safe(Path("C:/missing.mp4")) is None


def test_invalid_attributes_raises_windows_api_error():
    # Simulate Windows platform and API returning INVALID_FILE_ATTRIBUTES
    with patch("src.lib.windows_onedrive_api.platform.system", return_value="Windows"):
        with patch.object(Path, "exists", return_value=True):
            mock_get_attrs = MagicMock(return_value=wapi.INVALID_FILE_ATTRIBUTES)
            mock_get_last_error = MagicMock(return_value=1234)

            with patch("src.lib.windows_onedrive_api.ctypes.windll") as mock_windll:
                # Ensure kernel32 members exist and return our values
                mock_windll.kernel32.GetFileAttributesW = mock_get_attrs
                mock_windll.kernel32.GetLastError = mock_get_last_error

                with pytest.raises(wapi.WindowsOneDriveAPIError) as exc:
                    wapi.detect_cloud_status(Path("C:/somefile.mp4"))

                assert "error code" in str(exc.value) or "Failed to get file attributes" in str(exc.value)


def test_cloud_only_and_local_detection():
    # Simulate Windows platform and attribute flags for CLOUD_ONLY and LOCAL
    with patch("src.lib.windows_onedrive_api.platform.system", return_value="Windows"):
        with patch.object(Path, "exists", return_value=True):
            # Cloud-only
            with patch("src.lib.windows_onedrive_api.ctypes.windll") as mock_windll:
                mock_windll.kernel32.GetFileAttributesW = MagicMock(return_value=wapi.FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS)
                status = wapi.detect_cloud_status(Path("C:/cloud_only.mp4"))
                assert status == CloudFileStatus.CLOUD_ONLY

            # Local (no recall flag)
            with patch("src.lib.windows_onedrive_api.ctypes.windll") as mock_windll2:
                mock_windll2.kernel32.GetFileAttributesW = MagicMock(return_value=0x00000020)
                status = wapi.detect_cloud_status(Path("C:/local.mp4"))
                assert status == CloudFileStatus.LOCAL

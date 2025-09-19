#!/usr/bin/env python3
"""
Integration tests for mixed OneDrive/local directory scanning functionality.

Tests the complete scanning pipeline with mixed local and cloud files,
validating that the scanner correctly handles OneDrive cloud status
detection and filtering during directory traversal.
"""

import pytest
import platform
from pathlib import Path
from unittest.mock import patch, MagicMock
from tempfile import TemporaryDirectory

from src.services.file_scanner import FileScanner
from src.services.onedrive_service import OneDriveService
from src.models.cloud_file_status import CloudFileStatus
from src.models.user_file import UserFile


class TestMixedDirectoryScanIntegration:
    """Integration tests for mixed OneDrive/local directory scanning."""
    
    def setup_method(self):
        """Set up test environment for each test."""
        self.scanner = FileScanner()
        self.onedrive_service = OneDriveService()
    
    def test_scanner_initialization_with_onedrive(self):
        """Test that scanner initializes correctly with OneDrive support."""
        assert self.scanner is not None
        assert self.onedrive_service is not None
        assert self.onedrive_service.is_supported() == (platform.system().lower() == "windows")
    
    def test_mixed_directory_structure_creation(self):
        """Test creation of mixed directory structure for testing."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test video files
            local_file = temp_path / "local_video.mp4"
            cloud_file = temp_path / "cloud_video.mkv"
            nested_local = temp_path / "subfolder" / "nested_video.mov"
            
            # Create directories and files
            (temp_path / "subfolder").mkdir()
            local_file.write_bytes(b"local video content")
            cloud_file.write_bytes(b"cloud video content")
            nested_local.write_bytes(b"nested video content")
            
            # Verify structure
            assert local_file.exists()
            assert cloud_file.exists()
            assert nested_local.exists()
            assert len(list(temp_path.rglob("*.mp4"))) >= 1
            assert len(list(temp_path.rglob("*.mkv"))) >= 1
            assert len(list(temp_path.rglob("*.mov"))) >= 1
    
    @pytest.mark.skipif(platform.system().lower() != "windows", reason="OneDrive detection requires Windows")
    def test_real_directory_scan_with_onedrive_detection(self):
        """Test scanning a real directory with OneDrive detection."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test files
            test_files = []
            for i, ext in enumerate(['.mp4', '.mkv', '.mov']):
                file_path = temp_path / f"test_video_{i}{ext}"
                file_path.write_bytes(b"test video content")
                test_files.append(file_path)
            
            # Scan directory
            video_files = list(self.scanner.scan_directory(temp_path))
            
            # Should find all test files
            assert len(video_files) == len(test_files)
            
            # Each file should have cloud status detected
            for video_file in video_files:
                assert isinstance(video_file, UserFile)
                assert hasattr(video_file, 'cloud_status')
                
                # Cloud status should be detected (likely LOCAL for temp files)
                status = video_file.cloud_status
                assert isinstance(status, CloudFileStatus)
                assert status in [CloudFileStatus.LOCAL, CloudFileStatus.CLOUD_ONLY]
    
    def test_simulated_mixed_cloud_local_scan(self):
        """Test scanning with simulated mixed cloud/local files."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test files
            local_file = temp_path / "local_video.mp4"
            cloud_file = temp_path / "cloud_video.mkv"
            local_file.write_bytes(b"local content")
            cloud_file.write_bytes(b"cloud content")
            
            # Mock cloud status detection for specific files
            def mock_detect_status(file_path):
                if file_path.name == "cloud_video.mkv":
                    return CloudFileStatus.CLOUD_ONLY
                else:
                    return CloudFileStatus.LOCAL
            
            with patch('src.services.onedrive_service.OneDriveService.detect_cloud_status_safe', side_effect=mock_detect_status):
                # Scan directory
                video_files = list(self.scanner.scan_directory(temp_path))
                
                # Should find both files
                assert len(video_files) == 2
                
                # Check cloud status for each file
                for video_file in video_files:
                    if video_file.path.name == "cloud_video.mkv":
                        assert video_file.cloud_status == CloudFileStatus.CLOUD_ONLY
                        assert video_file.is_cloud_only == True
                        assert video_file.is_local == False
                    else:
                        assert video_file.cloud_status == CloudFileStatus.LOCAL
                        assert video_file.is_cloud_only == False
                        assert video_file.is_local == True
    
    def test_cloud_only_file_filtering(self):
        """Test that cloud-only files can be identified for filtering."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test files
            files = []
            for i in range(3):
                file_path = temp_path / f"video_{i}.mp4"
                file_path.write_bytes(b"content")
                files.append(file_path)
            
            # Mock some files as cloud-only
            def mock_detect_status(file_path):
                if "video_1" in file_path.name:
                    return CloudFileStatus.CLOUD_ONLY
                return CloudFileStatus.LOCAL
            
            with patch('src.services.onedrive_service.OneDriveService.detect_cloud_status_safe', side_effect=mock_detect_status):
                video_files = list(self.scanner.scan_directory(temp_path))
                
                # Separate local and cloud-only files
                local_files = [vf for vf in video_files if vf.is_local]
                cloud_only_files = [vf for vf in video_files if vf.is_cloud_only]
                
                assert len(local_files) == 2  # video_0 and video_2
                assert len(cloud_only_files) == 1  # video_1
                assert cloud_only_files[0].path.name == "video_1.mp4"
    
    def test_recursive_scan_with_mixed_cloud_status(self):
        """Test recursive scanning with mixed cloud status in subdirectories."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create nested directory structure
            (temp_path / "subdir1").mkdir()
            (temp_path / "subdir2").mkdir()
            
            files = [
                temp_path / "root_local.mp4",
                temp_path / "root_cloud.mkv",
                temp_path / "subdir1" / "sub1_local.mov",
                temp_path / "subdir1" / "sub1_cloud.mp4",
                temp_path / "subdir2" / "sub2_local.mkv"
            ]
            
            for file_path in files:
                file_path.write_bytes(b"content")
            
            # Mock cloud status based on filename
            def mock_detect_status(file_path):
                if "cloud" in file_path.name:
                    return CloudFileStatus.CLOUD_ONLY
                return CloudFileStatus.LOCAL
            
            with patch('src.services.onedrive_service.OneDriveService.detect_cloud_status_safe', side_effect=mock_detect_status):
                # Test recursive scan
                video_files = list(self.scanner.scan_directory(temp_path, recursive=True))
                
                assert len(video_files) == 5
                
                # Check cloud status distribution
                local_count = sum(1 for vf in video_files if vf.is_local)
                cloud_count = sum(1 for vf in video_files if vf.is_cloud_only)
                
                assert local_count == 3  # Files without "cloud" in name
                assert cloud_count == 2  # Files with "cloud" in name
    
    def test_error_handling_during_mixed_scan(self):
        """Test error handling when cloud detection fails for some files."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test files
            good_file = temp_path / "good_video.mp4"
            error_file = temp_path / "error_video.mkv"
            good_file.write_bytes(b"good content")
            error_file.write_bytes(b"error content")
            
            # Mock cloud detection with errors for specific files
            def mock_detect_status(file_path):
                if "error" in file_path.name:
                    return None  # Simulate detection failure
                return CloudFileStatus.LOCAL
            
            with patch('src.services.onedrive_service.OneDriveService.detect_cloud_status_safe', side_effect=mock_detect_status):
                video_files = list(self.scanner.scan_directory(temp_path))
                
                # Should still find both files
                assert len(video_files) == 2
                
                # Files with detection errors should default to LOCAL
                for video_file in video_files:
                    # The UserFile should handle detection failures gracefully
                    status = video_file.cloud_status
                    assert status == CloudFileStatus.LOCAL  # Fallback behavior
    
    def test_non_windows_platform_graceful_degradation(self):
        """Test that scanning works gracefully on non-Windows platforms."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test files
            file_path = temp_path / "test_video.mp4"
            file_path.write_bytes(b"content")
            
            # Force non-Windows behavior
            with patch('src.lib.windows_onedrive_api.is_windows_platform', return_value=False):
                video_files = list(self.scanner.scan_directory(temp_path))
                
                assert len(video_files) == 1
                
                # Should default to LOCAL on non-Windows
                video_file = video_files[0]
                assert video_file.cloud_status == CloudFileStatus.LOCAL
                assert video_file.is_local == True
                assert video_file.is_cloud_only == False
    
    def test_performance_impact_of_cloud_detection(self):
        """Test that cloud detection doesn't significantly impact scan performance."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create multiple test files
            num_files = 10
            for i in range(num_files):
                file_path = temp_path / f"video_{i}.mp4"
                file_path.write_bytes(b"content")
            
            import time
            
            # Measure scan time with cloud detection
            start_time = time.time()
            video_files = list(self.scanner.scan_directory(temp_path))
            scan_time = time.time() - start_time
            
            assert len(video_files) == num_files
            # Performance assertion - scan should complete quickly
            # This is a basic check, actual thresholds may need adjustment
            assert scan_time < 5.0  # Should complete within 5 seconds
    
    def test_cloud_status_persistence_across_operations(self):
        """Test that cloud status is cached and persists across operations."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            file_path = temp_path / "test_video.mp4"
            file_path.write_bytes(b"content")
            
            call_count = 0
            def counting_detect_status(file_path):
                nonlocal call_count
                call_count += 1
                return CloudFileStatus.LOCAL
            
            with patch('src.services.onedrive_service.OneDriveService.detect_cloud_status_safe', side_effect=counting_detect_status):
                video_files = list(self.scanner.scan_directory(temp_path))
                video_file = video_files[0]
                
                # Access cloud status multiple times
                status1 = video_file.cloud_status
                status2 = video_file.cloud_status
                status3 = video_file.cloud_status
                
                assert status1 == status2 == status3
                # Should only call detection once due to caching
                assert call_count == 1

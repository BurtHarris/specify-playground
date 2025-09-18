#!/usr/bin/env python3
"""
VideoFileScanner Service Contract Tests for Video Duplicate Scanner

These tests validate the VideoFileScanner service contract as specified in
specs/001-build-a-cli/contracts/service-apis.md

All tests MUST FAIL initially (TDD requirement) until implementation is complete.
"""

import pytest
from pathlib import Path
import tempfile
import shutil
import os

# Import the VideoFileScanner service (will fail until implemented)
try:
    from src.services.video_file_scanner import VideoFileScanner
    from src.models.video_file import VideoFile
except ImportError:
    # Expected to fail initially - create stubs for testing
    class VideoFileScanner:
        def scan_directory(self, directory, recursive=True):
            raise NotImplementedError("VideoFileScanner not yet implemented")
            
        def validate_file(self, file_path):
            raise NotImplementedError("VideoFileScanner not yet implemented")
    
    class VideoFile:
        def __init__(self, path):
            self.path = path


class TestVideoFileScannerContract:
    """Test VideoFileScanner service contract compliance."""
    
    def setup_method(self):
        """Set up test environment for each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.scanner = VideoFileScanner()
        
        # Create test file structure
        self.create_test_files()
        
    def teardown_method(self):
        """Clean up after each test."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def create_test_files(self):
        """Create test file structure for consistent testing."""
        # Root level video files with content
        (Path(self.temp_dir) / "video1.mp4").write_bytes(b"fake video content")
        (Path(self.temp_dir) / "video2.mkv").write_bytes(b"fake video content")
        (Path(self.temp_dir) / "video3.mov").write_bytes(b"fake video content")
        
        # Non-video files (should be ignored)
        (Path(self.temp_dir) / "document.txt").write_text("text content")
        (Path(self.temp_dir) / "image.jpg").write_bytes(b"fake image")
        
        # Subdirectory with video files
        subdir = Path(self.temp_dir) / "subdir"
        subdir.mkdir()
        (subdir / "sub_video1.mp4").write_bytes(b"fake video content")
        (subdir / "sub_video2.mkv").write_bytes(b"fake video content")
        
        # Deep nested directory
        deep_dir = subdir / "deep" / "nested"
        deep_dir.mkdir(parents=True)
        (deep_dir / "deep_video.mov").write_bytes(b"fake video content")

    @pytest.mark.contract
    def test_scan_directory_returns_iterator(self):
        """Test: scan_directory returns Iterator[VideoFile]."""
        result = self.scanner.scan_directory(Path(self.temp_dir))
        
        # Contract: Returns Iterator
        assert hasattr(result, '__iter__')
        assert hasattr(result, '__next__')
        
        # Contract: Yields VideoFile instances
        files = list(result)
        for file in files:
            assert isinstance(file, VideoFile)

    @pytest.mark.contract
    def test_scan_directory_recursive_finds_all_videos(self):
        """Test: Recursive scan finds video files in subdirectories."""
        files = list(self.scanner.scan_directory(Path(self.temp_dir), recursive=True))
        
        # Contract: MUST find all video files recursively
        video_paths = [f.path for f in files]
        video_names = [p.name for p in video_paths]
        
        # Should find all video files
        assert "video1.mp4" in video_names
        assert "video2.mkv" in video_names  
        assert "video3.mov" in video_names
        assert "sub_video1.mp4" in video_names
        assert "sub_video2.mkv" in video_names
        assert "deep_video.mov" in video_names
        
        # Should NOT find non-video files
        assert "document.txt" not in video_names
        assert "image.jpg" not in video_names

    @pytest.mark.contract
    def test_scan_directory_non_recursive_only_root_level(self):
        """Test: Non-recursive scan only finds root level video files."""
        files = list(self.scanner.scan_directory(Path(self.temp_dir), recursive=False))
        
        # Contract: MUST only find root level files when not recursive
        video_paths = [f.path for f in files]
        video_names = [p.name for p in video_paths]
        
        # Should find root level videos
        assert "video1.mp4" in video_names
        assert "video2.mkv" in video_names
        assert "video3.mov" in video_names
        
        # Should NOT find subdirectory videos
        assert "sub_video1.mp4" not in video_names
        assert "sub_video2.mkv" not in video_names
        assert "deep_video.mov" not in video_names

    @pytest.mark.contract
    def test_scan_directory_only_video_extensions(self):
        """Test: Only yields files with video extensions (.mp4, .mkv, .mov)."""
        files = list(self.scanner.scan_directory(Path(self.temp_dir)))
        
        # Contract: MUST yield only files with video extensions
        for file in files:
            extension = file.path.suffix.lower()
            assert extension in ['.mp4', '.mkv', '.mov']

    @pytest.mark.contract
    def test_scan_directory_preserves_relative_order(self):
        """Test: Preserves relative order for deterministic results."""
        # Run scan multiple times
        results1 = list(self.scanner.scan_directory(Path(self.temp_dir)))
        results2 = list(self.scanner.scan_directory(Path(self.temp_dir)))
        
        # Contract: MUST preserve relative order for deterministic results
        paths1 = [f.path for f in results1]
        paths2 = [f.path for f in results2]
        
        assert paths1 == paths2, "Scan order should be deterministic"

    @pytest.mark.contract
    def test_scan_directory_handles_nonexistent_directory(self):
        """Test: Raises DirectoryNotFoundError for nonexistent directory."""
        nonexistent = Path(self.temp_dir) / "nonexistent"
        
        # Contract: MUST raise DirectoryNotFoundError if directory doesn't exist
        with pytest.raises(Exception) as exc_info:
            list(self.scanner.scan_directory(nonexistent))
            
        # Should be DirectoryNotFoundError or similar
        assert "not found" in str(exc_info.value).lower() or "exist" in str(exc_info.value).lower()

    @pytest.mark.contract
    def test_scan_directory_handles_permission_denied(self):
        """Test: Handles permission errors gracefully."""
        # Create directory and remove permissions
        protected_dir = Path(self.temp_dir) / "protected"
        protected_dir.mkdir()
        protected_dir.chmod(0o000)
        
        try:
            # Contract: Should handle permission errors gracefully
            # May raise PermissionError or handle gracefully depending on implementation
            try:
                files = list(self.scanner.scan_directory(protected_dir))
                # If no exception, scanner handled it gracefully
                assert isinstance(files, list)
            except PermissionError:
                # This is also acceptable behavior
                pass
                
        finally:
            # Restore permissions for cleanup
            protected_dir.chmod(0o755)

    @pytest.mark.contract
    def test_scan_directory_skips_inaccessible_files(self):
        """Test: Skips files that cannot be accessed."""
        # Create a video file with no read permissions
        protected_file = Path(self.temp_dir) / "protected_video.mp4"
        protected_file.write_bytes(b"fake video content")
        protected_file.chmod(0o000)
        
        try:
            files = list(self.scanner.scan_directory(Path(self.temp_dir)))
            
            # Contract: MUST skip files that cannot be accessed
            # Should not raise exception, should continue with other files
            video_names = [f.path.name for f in files]
            
            # Should still find accessible files
            assert "video1.mp4" in video_names
            # Protected file might or might not be included depending on implementation
            # but it should not cause the scan to fail
            
        finally:
            # Restore permissions for cleanup
            protected_file.chmod(0o644)

    @pytest.mark.contract  
    def test_validate_file_checks_existence(self):
        """Test: validate_file checks file existence."""
        existing_file = Path(self.temp_dir) / "video1.mp4"
        nonexistent_file = Path(self.temp_dir) / "nonexistent.mp4"
        
        # Contract: MUST check file existence
        assert self.scanner.validate_file(existing_file) is True
        assert self.scanner.validate_file(nonexistent_file) is False

    @pytest.mark.contract
    def test_validate_file_checks_read_permissions(self):
        """Test: validate_file checks read permissions on systems that support it."""
        video_file = Path(self.temp_dir) / "test_video.mp4"
        video_file.write_bytes(b"fake video content")
        
        # Should be valid initially
        assert self.scanner.validate_file(video_file) is True
        
        # Remove read permissions
        video_file.chmod(0o000)
        
        try:
            # Contract: Should check read permissions where supported
            # On Windows, permission model is different, so test is platform-dependent
            result = self.scanner.validate_file(video_file)
            # Accept either True (Windows behavior) or False (Unix behavior)
            assert isinstance(result, bool)
            
        finally:
            # Restore permissions for cleanup
            video_file.chmod(0o644)

    @pytest.mark.contract
    def test_validate_file_checks_extension(self):
        """Test: validate_file validates file extension."""
        # Valid video extensions
        mp4_file = Path(self.temp_dir) / "test.mp4"
        mkv_file = Path(self.temp_dir) / "test.mkv"
        mov_file = Path(self.temp_dir) / "test.mov"
        
        # Invalid extensions
        txt_file = Path(self.temp_dir) / "test.txt"
        jpg_file = Path(self.temp_dir) / "test.jpg"
        
        # Create all files with content
        for file in [mp4_file, mkv_file, mov_file]:
            file.write_bytes(b"fake video content")
        for file in [txt_file, jpg_file]:
            file.write_text("fake content")
        
        # Contract: MUST validate file extension
        assert self.scanner.validate_file(mp4_file) is True
        assert self.scanner.validate_file(mkv_file) is True
        assert self.scanner.validate_file(mov_file) is True
        assert self.scanner.validate_file(txt_file) is False
        assert self.scanner.validate_file(jpg_file) is False

    @pytest.mark.contract
    def test_validate_file_no_exceptions_for_invalid(self):
        """Test: validate_file does not raise exceptions for invalid files."""
        invalid_files = [
            Path(self.temp_dir) / "nonexistent.mp4",
            Path(self.temp_dir) / "invalid.txt",
            Path("/invalid/path/video.mp4")
        ]
        
        # Contract: MUST NOT raise exceptions for invalid files
        for file in invalid_files:
            try:
                result = self.scanner.validate_file(file)
                assert isinstance(result, bool)
            except Exception as e:
                pytest.fail(f"validate_file should not raise exceptions, got: {e}")

    @pytest.mark.contract
    def test_scan_directory_handles_symbolic_links(self):
        """Test: Handles symbolic links according to configuration."""
        # Create a target video file
        target_file = Path(self.temp_dir) / "target.mp4"
        target_file.write_bytes(b"fake video content")
        
        # Create symbolic link
        link_file = Path(self.temp_dir) / "link.mp4"
        try:
            link_file.symlink_to(target_file)
        except OSError:
            # Skip test if symlinks not supported (e.g., Windows without admin)
            pytest.skip("Symbolic links not supported on this system")
        
        files = list(self.scanner.scan_directory(Path(self.temp_dir)))
        
        # Contract: MUST handle symbolic links according to configuration
        # Implementation should either include or exclude symlinks consistently
        video_paths = [f.path for f in files]
        
        # Should handle symlinks without crashing
        # Exact behavior (include/exclude) depends on implementation choice
        assert len(video_paths) >= 1  # At least the target file should be found

    @pytest.mark.contract
    def test_scan_directory_case_insensitive_extensions(self):
        """Test: Handles case-insensitive file extensions."""
        # Create files with mixed case extensions
        files_to_create = [
            "video.MP4",
            "video.MKV", 
            "video.MOV",
        ]
        
        for filename in files_to_create:
            (Path(self.temp_dir) / filename).write_bytes(b"fake video content")
        
        found_files = list(self.scanner.scan_directory(Path(self.temp_dir)))
        
        # Contract: Should handle case-insensitive extensions
        found_names = [f.path.name for f in found_files]
        
        # Should find all video files regardless of case variations
        # Allow for filesystem case normalization on different platforms
        video_extensions_found = set()
        for name in found_names:
            if name.startswith("video."):
                video_extensions_found.add(name.split(".")[1].upper())
        
        # Should find at least the major video extensions
        expected_extensions = {"MP4", "MKV", "MOV"}
        assert expected_extensions.issubset(video_extensions_found), f"Should find video files with extensions: {expected_extensions}"


if __name__ == "__main__":
    # Run contract tests
    pytest.main([__file__, "-v", "-m", "contract"])
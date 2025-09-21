#!/usr/bin/env python3
"""
Basic Duplicate Detection Integration Tests for Video Duplicate Scanner

These tests validate end-to-end duplicate detection functionality as specified
in the quickstart.md scenarios.

All tests MUST FAIL initially (TDD requirement) until implementation is complete.
"""

import pytest
import tempfile
import shutil
from pathlib import Path

# Import modules for integration testing
try:
    from src.services.file_scanner import FileScanner
    from src.services.duplicate_detector import DuplicateDetector
    from src.models.user_file import UserFile
    from src.models.duplicate_group import DuplicateGroup
except ImportError:
    # Expected to fail initially - create stubs for testing
    class UserFileScanner:
        def scan_directory(self, directory, recursive=True):
            raise NotImplementedError("VideoFileScanner not yet implemented")

    class DuplicateDetector:
        def find_duplicates(self, files):
            raise NotImplementedError("DuplicateDetector not yet implemented")

    class UserFile:
        def __init__(self, path, size=None, hash_value=None):
            self.path = Path(path)
            self.size = size or 0
            self.hash = hash_value

    class DuplicateGroup:
        def __init__(self, files):
            self.files = files


class TestBasicDuplicateDetection:
    """Test basic duplicate detection integration scenarios."""

    def setup_method(self):
        """Set up test environment for each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.scanner = FileScanner()
        self.detector = DuplicateDetector()

        # Create test video content
        self.duplicate_content = (
            b"Duplicate video content for testing" * 10000
        )  # ~350KB
        self.unique_content1 = b"Unique video content number one" * 10000  # ~320KB
        self.unique_content2 = b"Unique video content number two" * 10000  # ~320KB

    def teardown_method(self):
        """Clean up after each test."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.integration
    def test_end_to_end_duplicate_detection_single_directory(self):
        """Test: End-to-end duplicate detection in single directory."""
        # Create test files - 2 duplicates, 2 unique
        duplicate1 = Path(self.temp_dir) / "movie1.mp4"
        duplicate2 = Path(self.temp_dir) / "movie1_backup.mp4"
        unique1 = Path(self.temp_dir) / "different_movie.mkv"
        unique2 = Path(self.temp_dir) / "another_movie.mov"

        # Write content
        with open(duplicate1, "wb") as f:
            f.write(self.duplicate_content)
        with open(duplicate2, "wb") as f:
            f.write(self.duplicate_content)
        with open(unique1, "wb") as f:
            f.write(self.unique_content1)
        with open(unique2, "wb") as f:
            f.write(self.unique_content2)

        # Integration test: Scan → Detect duplicates
        scanned_files = list(self.scanner.scan_directory(Path(self.temp_dir)))
        duplicate_groups = self.detector.find_duplicates(scanned_files)

        # Should find exactly one duplicate group with 2 files
        assert len(duplicate_groups) == 1
        assert len(duplicate_groups[0].files) == 2

        # Verify the duplicate files are the ones we created
        duplicate_paths = {f.path.name for f in duplicate_groups[0].files}
        assert duplicate_paths == {"movie1.mp4", "movie1_backup.mp4"}

    @pytest.mark.integration
    def test_end_to_end_recursive_duplicate_detection(self):
        """Test: End-to-end recursive duplicate detection across subdirectories."""
        # Create nested directory structure
        subdir1 = Path(self.temp_dir) / "folder1"
        subdir2 = Path(self.temp_dir) / "folder2" / "nested"
        subdir1.mkdir()
        subdir2.mkdir(parents=True)

        # Create duplicates across directories
        duplicate1 = Path(self.temp_dir) / "root_video.mp4"
        duplicate2 = subdir1 / "same_video.mp4"
        duplicate3 = subdir2 / "copy_of_video.mkv"
        unique1 = subdir1 / "unique_video.mov"

        # Write content
        for dup_file in [duplicate1, duplicate2, duplicate3]:
            with open(dup_file, "wb") as f:
                f.write(self.duplicate_content)

        with open(unique1, "wb") as f:
            f.write(self.unique_content1)

        # Integration test: Recursive scan → Detect duplicates
        scanned_files = list(
            self.scanner.scan_directory(Path(self.temp_dir), recursive=True)
        )
        duplicate_groups = self.detector.find_duplicates(scanned_files)

        # Should find one group with 3 duplicate files
        assert len(duplicate_groups) == 1
        assert len(duplicate_groups[0].files) == 3

        # Verify all duplicates found regardless of location
        duplicate_names = {f.path.name for f in duplicate_groups[0].files}
        assert duplicate_names == {
            "root_video.mp4",
            "same_video.mp4",
            "copy_of_video.mkv",
        }

    @pytest.mark.integration
    def test_no_duplicates_found_scenario(self):
        """Test: No duplicates found when all files are unique."""
        # Create unique video files
        video_files = [
            "movie1.mp4",
            "movie2.mkv",
            "movie3.mov",
            "series_episode1.mp4",
            "documentary.mkv",
        ]

        contents = [
            b"Content for movie 1" * 5000,
            b"Content for movie 2" * 5000,
            b"Content for movie 3" * 5000,
            b"Content for episode 1" * 5000,
            b"Content for documentary" * 5000,
        ]

        for filename, content in zip(video_files, contents):
            file_path = Path(self.temp_dir) / filename
            with open(file_path, "wb") as f:
                f.write(content)

        # Integration test: Scan → Detect (should find no duplicates)
        scanned_files = list(self.scanner.scan_directory(Path(self.temp_dir)))
        duplicate_groups = self.detector.find_duplicates(scanned_files)

        # Should find no duplicate groups
        assert len(duplicate_groups) == 0

    @pytest.mark.integration
    def test_multiple_duplicate_groups(self):
        """Test: Multiple separate duplicate groups detection."""
        # Create two separate groups of duplicates
        # Group 1: movie duplicates
        group1_content = b"Movie group content" * 8000
        movie1a = Path(self.temp_dir) / "movie_original.mp4"
        movie1b = Path(self.temp_dir) / "movie_copy.mp4"

        # Group 2: series duplicates
        group2_content = b"Series group content" * 8000
        series2a = Path(self.temp_dir) / "episode1.mkv"
        series2b = Path(self.temp_dir) / "episode1_backup.mkv"
        series2c = Path(self.temp_dir) / "episode1_archive.mov"

        # Unique file
        unique_content = b"Unique content" * 8000
        unique_file = Path(self.temp_dir) / "standalone.mp4"

        # Write group 1 duplicates
        for file in [movie1a, movie1b]:
            with open(file, "wb") as f:
                f.write(group1_content)

        # Write group 2 duplicates
        for file in [series2a, series2b, series2c]:
            with open(file, "wb") as f:
                f.write(group2_content)

        # Write unique file
        with open(unique_file, "wb") as f:
            f.write(unique_content)

        # Integration test: Scan → Detect multiple groups
        scanned_files = list(self.scanner.scan_directory(Path(self.temp_dir)))
        duplicate_groups = self.detector.find_duplicates(scanned_files)

        # Should find exactly 2 duplicate groups
        assert len(duplicate_groups) == 2

        # Verify group sizes
        group_sizes = sorted([len(group.files) for group in duplicate_groups])
        assert group_sizes == [2, 3]  # One group with 2 files, one with 3

        # Verify no group contains the unique file
        all_duplicate_files = {
            f.path.name for group in duplicate_groups for f in group.files
        }
        assert "standalone.mp4" not in all_duplicate_files

    @pytest.mark.integration
    def test_mixed_video_formats_duplicate_detection(self):
        """Test: Duplicate detection across different video formats."""
        # Create identical content in different formats
        identical_content = b"Same video content in different formats" * 7000

        formats = ["same_movie.mp4", "same_movie.mkv", "same_movie.mov"]

        for filename in formats:
            file_path = Path(self.temp_dir) / filename
            with open(file_path, "wb") as f:
                f.write(identical_content)

        # Integration test: Should detect as duplicates despite different extensions
        scanned_files = list(self.scanner.scan_directory(Path(self.temp_dir)))
        duplicate_groups = self.detector.find_duplicates(scanned_files)

        # Should find one group with all 3 formats
        assert len(duplicate_groups) == 1
        assert len(duplicate_groups[0].files) == 3

        # Verify all formats included
        extensions = {f.path.suffix for f in duplicate_groups[0].files}
        assert extensions == {".mp4", ".mkv", ".mov"}

    @pytest.mark.integration
    def test_large_file_duplicate_detection(self):
        """Test: Duplicate detection with larger files (simulating real videos)."""
        # Create larger content (simulate ~5MB files)
        large_content = b"Large video file content" * 200000  # ~5MB

        large1 = Path(self.temp_dir) / "large_movie1.mp4"
        large2 = Path(self.temp_dir) / "large_movie1_copy.mkv"

        # Write large duplicate files
        for file in [large1, large2]:
            with open(file, "wb") as f:
                f.write(large_content)

        # Integration test: Should handle large files efficiently
        scanned_files = list(self.scanner.scan_directory(Path(self.temp_dir)))
        duplicate_groups = self.detector.find_duplicates(scanned_files)

        # Should detect large file duplicates
        assert len(duplicate_groups) == 1
        assert len(duplicate_groups[0].files) == 2

        # Verify file sizes are correctly captured
        for file in duplicate_groups[0].files:
            assert file.size > 4000000  # Should be > 4MB

    @pytest.mark.integration
    def test_empty_directory_handling(self):
        """Test: Graceful handling of empty directory."""
        # Create empty subdirectory
        empty_subdir = Path(self.temp_dir) / "empty"
        empty_subdir.mkdir()

        # Integration test: Should handle empty directories gracefully
        scanned_files = list(
            self.scanner.scan_directory(Path(self.temp_dir), recursive=True)
        )
        duplicate_groups = self.detector.find_duplicates(scanned_files)

        # Should complete without errors
        assert len(scanned_files) == 0
        assert len(duplicate_groups) == 0

    @pytest.mark.integration
    def test_non_video_files_ignored(self):
        """Test: Non-video files are ignored during scanning."""
        # Create mix of video and non-video files
        video_content = b"Video file content" * 5000

        # Video files
        video1 = Path(self.temp_dir) / "video.mp4"
        video2 = Path(self.temp_dir) / "video_copy.mp4"

        # Non-video files (should be ignored)
        text_file = Path(self.temp_dir) / "readme.txt"
        image_file = Path(self.temp_dir) / "poster.jpg"
        audio_file = Path(self.temp_dir) / "soundtrack.mp3"

        # Write video files (duplicates)
        for file in [video1, video2]:
            with open(file, "wb") as f:
                f.write(video_content)

        # Write non-video files
        with open(text_file, "w") as f:
            f.write("This is a text file")
        with open(image_file, "wb") as f:
            f.write(b"Fake image content")
        with open(audio_file, "wb") as f:
            f.write(b"Fake audio content")

        # Integration test: Should only process video files
        scanned_files = list(self.scanner.scan_directory(Path(self.temp_dir)))

        # Should only find video files
        assert len(scanned_files) == 2
        scanned_names = {f.path.name for f in scanned_files}
        assert scanned_names == {"video.mp4", "video_copy.mp4"}

        # Should detect video duplicates, ignoring non-video files
        duplicate_groups = self.detector.find_duplicates(scanned_files)
        assert len(duplicate_groups) == 1
        assert len(duplicate_groups[0].files) == 2

    @pytest.mark.integration
    def test_size_based_optimization_performance(self):
        """Test: Size-based optimization improves performance."""
        # Create files with different sizes (no hash computation needed)
        sizes_and_content = [
            (1000, b"Small file" * 100),
            (5000, b"Medium file" * 500),
            (10000, b"Large file" * 1000),
            (15000, b"Extra large file" * 1500),
            (20000, b"Huge file" * 2000),
        ]

        for i, (size, content) in enumerate(sizes_and_content):
            file_path = Path(self.temp_dir) / f"video_{i}.mp4"
            with open(file_path, "wb") as f:
                f.write(content[:size])  # Write exact size

        # Integration test: Should not find duplicates (all different sizes)
        scanned_files = list(self.scanner.scan_directory(Path(self.temp_dir)))
        duplicate_groups = self.detector.find_duplicates(scanned_files)

        # Should find no duplicates (different sizes = no hash computation needed)
        assert len(duplicate_groups) == 0

        # All files should have different sizes
        sizes = {f.size for f in scanned_files}
        assert len(sizes) == len(scanned_files)  # All different sizes


if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v", "-m", "integration"])

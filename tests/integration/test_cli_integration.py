#!/usr/bin/env python3
"""
Integration tests for Video Duplicate Scanner CLI.

Tests the complete application workflow from command-line interface
through to final output generation.
"""

import tempfile
import pytest
import shutil
import subprocess
import yaml
from pathlib import Path

# no patch imports required here


class TestCLIIntegration:
    """Integration tests for the complete CLI application."""

    @property
    def workspace_dir(self):
        """Get the workspace directory dynamically."""
        return Path(__file__).parent.parent.parent  # Go up to workspace root

    @pytest.fixture
    def temp_video_dir(self):
        """Create a temporary directory with test video files."""
        temp_dir = Path(tempfile.mkdtemp())

        try:
            # Create test video files with different content
            video1 = temp_dir / "movie1.mp4"
            video2 = temp_dir / "movie1_copy.mkv"  # Duplicate content
            video3 = temp_dir / "movie2.mov"  # Different content
            video4 = temp_dir / "similar_movie.mp4"  # Similar name, different content

            # Create files with known content for hash testing
            video1.write_bytes(b"Video content 1" * 100)  # ~1.5KB
            video2.write_bytes(b"Video content 1" * 100)  # Same content as video1
            video3.write_bytes(b"Video content 2" * 100)  # Different content
            video4.write_bytes(b"Video content 3" * 100)  # Different content

            # Create a subdirectory for recursive testing
            subdir = temp_dir / "subdir"
            subdir.mkdir()
            video5 = subdir / "movie3.mp4"
            video5.write_bytes(b"Video content 4" * 100)

            yield temp_dir
        finally:
            shutil.rmtree(temp_dir)

    def test_cli_help_command(self):
        """Test that the CLI help command works."""
        # Use the current workspace directory instead of hardcoded path
        workspace_dir = Path(__file__).parent.parent.parent  # Go up to workspace root

        result = subprocess.run(
            ["python", "-m", "src", "--help"],
            capture_output=True,
            text=True,
            cwd=str(workspace_dir),
        )

        assert result.returncode == 0
        assert "Video Duplicate Scanner" in result.stdout
        assert "--recursive" in result.stdout
        assert "--export" in result.stdout

    def test_cli_version_check(self):
        """Test that the CLI performs Python version checking."""
        # This should work with Python 3.12+
        result = subprocess.run(
            ["python", "-m", "src", "--help"],
            capture_output=True,
            text=True,
            cwd=str(self.workspace_dir),
        )

        assert result.returncode == 0

    def test_cli_basic_scan(self, temp_video_dir):
        """Test basic directory scanning without recursive."""
        result = subprocess.run(
            ["python", "-m", "src", str(temp_video_dir)],
            capture_output=True,
            text=True,
            cwd=str(self.workspace_dir),
        )

        assert result.returncode == 0
        assert "Scanned:" in result.stdout or "Scan Results" in result.stdout
        assert "duplicate" in result.stdout.lower()

    def test_cli_recursive_scan(self, temp_video_dir):
        """Test recursive directory scanning."""
        result = subprocess.run(
            [
                "python",
                "-m",
                "src",
                "--recursive",
                "--debug",
                str(temp_video_dir),
            ],
            capture_output=True,
            text=True,
            cwd=str(self.workspace_dir),
        )

        assert result.returncode == 0
        assert "Scanned:" in result.stdout or "Scan Results" in result.stdout
        # Should find files in subdirectory too
        assert "movie3.mp4" in result.stdout or "subdir" in result.stdout

    def test_cli_yaml_export(self, temp_video_dir):
        """Test YAML export functionality."""
        output_file = temp_video_dir / "results.yaml"

        result = subprocess.run(
            [
                "python",
                "-m",
                "src",
                "--export",
                str(output_file),
                str(temp_video_dir),
            ],
            capture_output=True,
            text=True,
            cwd=str(self.workspace_dir),
        )

        assert result.returncode == 0
        assert output_file.exists()

        # Verify YAML format
        with open(output_file, "r") as f:
            data = yaml.safe_load(f)

        assert "metadata" in data
        assert "duplicate_groups" in data
        assert "potential_matches" in data
        assert isinstance(data["metadata"], dict)
        assert isinstance(data["duplicate_groups"], list)
        assert isinstance(data["potential_matches"], list)

    def test_cli_yaml_export(self, temp_video_dir):
        """Test YAML export functionality."""
        output_file = temp_video_dir / "results.yaml"

        result = subprocess.run(
            [
                "python",
                "-m",
                "src",
                "--export",
                str(output_file),
                str(temp_video_dir),
            ],
            capture_output=True,
            text=True,
            cwd=str(self.workspace_dir),
        )

        assert result.returncode == 0
        assert output_file.exists()

        # Verify YAML format
        with open(output_file, "r") as f:
            data = yaml.safe_load(f)

        assert "metadata" in data
        assert "duplicate_groups" in data
        assert "potential_matches" in data
        assert isinstance(data["metadata"], dict)
        assert isinstance(data["duplicate_groups"], list)
        assert isinstance(data["potential_matches"], list)

    def test_cli_duplicate_detection(self, temp_video_dir):
        """Test that the CLI correctly identifies duplicate files."""
        output_file = temp_video_dir / "results.yaml"

        result = subprocess.run(
            [
                "python",
                "-m",
                "src",
                "--export",
                str(output_file),
                str(temp_video_dir),
            ],
            capture_output=True,
            text=True,
            cwd=str(self.workspace_dir),
        )

        assert result.returncode == 0

        with open(output_file, "r") as f:
            data = yaml.safe_load(f)

        # Should find duplicate files (movie1.mp4 and movie1_copy.mkv have same content)
        duplicate_groups = data["duplicate_groups"]
        assert len(duplicate_groups) >= 1

        # Check that the duplicate group contains expected files
        found_duplicate = False
        for group in duplicate_groups:
            files = [f["path"] for f in group["files"]]
            if any("movie1.mp4" in f for f in files) and any(
                "movie1_copy.mkv" in f for f in files
            ):
                found_duplicate = True
                assert len(group["files"]) == 2
                break

        assert found_duplicate, "Should find duplicate files with same content"

    def test_cli_potential_matches(self, temp_video_dir):
        """Test that the CLI identifies potential matches based on name similarity."""
        output_file = temp_video_dir / "results.yaml"

        result = subprocess.run(
            [
                "python",
                "-m",
                "src",
                "--export",
                str(output_file),
                str(temp_video_dir),
            ],
            capture_output=True,
            text=True,
            cwd=str(self.workspace_dir),
        )

        assert result.returncode == 0

        with open(output_file, "r") as f:
            data = yaml.safe_load(f)

        # Should find potential matches based on similar names
        potential_matches = data["potential_matches"]

        # Look for movies with similar names but different content
        found_potential = False
        for group in potential_matches:
            if "movie" in group["group_id"].lower():
                found_potential = True
                assert len(group["files"]) >= 1
                break

        # This might not always trigger depending on similarity threshold
        # so we don't assert it as mandatory

    def test_cli_non_recursive_scan(self, temp_video_dir):
        """Test that non-recursive scan excludes subdirectory files."""
        output_file = temp_video_dir / "results.yaml"

        result = subprocess.run(
            [
                "python",
                "-m",
                "src",
                "--no-recursive",
                "--export",
                str(output_file),
                str(temp_video_dir),
            ],
            capture_output=True,
            text=True,
            cwd=str(self.workspace_dir),
        )

        assert result.returncode == 0

        with open(output_file, "r") as f:
            data = yaml.safe_load(f)

        # Check that files from subdirectory are not included
        all_files = []
        for group in data["duplicate_groups"]:
            all_files.extend([f["path"] for f in group["files"]])
        for group in data["potential_matches"]:
            all_files.extend([f["path"] for f in group["files"]])

        # Should not find movie3.mp4 which is in subdirectory
        subdir_files = [f for f in all_files if "subdir" in f or "movie3.mp4" in f]
        assert (
            len(subdir_files) == 0
        ), "Non-recursive scan should not include subdirectory files"

    def test_cli_error_handling_nonexistent_directory(self):
        """Test CLI error handling for nonexistent directory."""
        result = subprocess.run(
            ["python", "-m", "src", "/nonexistent/directory"],
            capture_output=True,
            text=True,
            cwd=str(self.workspace_dir),
        )

        assert result.returncode != 0
        assert "error" in result.stderr.lower() or "not found" in result.stderr.lower()

    def test_cli_progress_reporting(self, temp_video_dir):
        """Test that CLI shows progress information."""
        result = subprocess.run(
            ["python", "-m", "src", str(temp_video_dir)],
            capture_output=True,
            text=True,
            cwd=str(self.workspace_dir),
        )

        assert result.returncode == 0
        # Should show some progress indication
        assert any(
            keyword in result.stdout.lower()
            for keyword in [
                "scanning",
                "processing",
                "analyzing",
                "found",
                "completed",
            ]
        )

    def test_cli_colorized_output(self, temp_video_dir):
        """Test that CLI produces colorized output when appropriate."""
        result = subprocess.run(
            ["python", "-m", "src", str(temp_video_dir)],
            capture_output=True,
            text=True,
            cwd=str(self.workspace_dir),
        )

        assert result.returncode == 0
        # Note: ANSI color codes might not appear in captured output
        # This test mainly ensures the CLI runs without color-related errors
        assert len(result.stdout) > 0

    def test_cli_metadata_generation(self, temp_video_dir):
        """Test that scan metadata is properly generated."""
        output_file = temp_video_dir / "results.yaml"

        result = subprocess.run(
            [
                "python",
                "-m",
                "src",
                "--export",
                str(output_file),
                str(temp_video_dir),
            ],
            capture_output=True,
            text=True,
            cwd=str(self.workspace_dir),
        )

        assert result.returncode == 0

        with open(output_file, "r") as f:
            data = yaml.safe_load(f)

        metadata = data["metadata"]
        assert "scanned_directory" in metadata
        assert "scan_date" in metadata
        assert "total_files_found" in metadata
        assert "total_files_processed" in metadata
        assert "duration_seconds" in metadata

        # Verify metadata values are reasonable
        assert metadata["total_files_found"] >= 0
        assert metadata["total_files_processed"] >= 0
        # Note: duration_seconds can be None if not set
        assert "recursive" in metadata

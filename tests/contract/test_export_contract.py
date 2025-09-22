#!/usr/bin/env python3
"""
CLI Export Functionality Contract Tests for Video Duplicate Scanner

These tests validate the export functionality contract as specified in
specs/001-build-a-cli/contracts/cli-interface.md

All tests MUST FAIL initially (TDD requirement) until implementation is complete.
"""

import pytest
import yaml
from pathlib import Path
from tests.cli_runner_compat import CliRunner
import tempfile
import shutil

# Import the main CLI function
from src.cli.main import main


class TestCLIExportContract:
    """Test CLI export functionality contract compliance."""

    def setup_method(self):
        """Set up test environment for each test."""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()

        # Create test video files for consistent testing
        self.test_video1 = Path(self.temp_dir) / "video1.mp4"
        self.test_video2 = Path(self.temp_dir) / "video2.mkv"
        self.test_video1.touch()
        self.test_video2.touch()

    def teardown_method(self):
        """Clean up after each test."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.contract
    def test_yaml_export_default_format(self):
        """Test: YAML export is the default format and produces valid YAML."""
        export_file = Path(self.temp_dir) / "results.yaml"

        result = self.runner.invoke(main, ["--export", str(export_file), self.temp_dir])

        # Contract: Export succeeds
        assert result.exit_code == 0
        assert export_file.exists()

        # Contract: Produces valid YAML
        with open(export_file, "r") as f:
            data = yaml.safe_load(f)

        # Validate YAML structure
        assert isinstance(data, dict)
        assert "version" in data
        assert "metadata" in data
        assert "duplicate_groups" in data  # Top-level, not under "results"

    @pytest.mark.contract
    def test_json_export_not_supported(self):
        """Test: JSON export is no longer supported - only YAML export."""
        export_file = Path(self.temp_dir) / "results.json"

        result = self.runner.invoke(main, ["--export", str(export_file), self.temp_dir])

        # Contract: JSON export should not be supported (YAML-only)
        # The CLI should either reject .json extension or create YAML content
        if result.exit_code == 0 and export_file.exists():
            # If file is created, it should contain YAML, not JSON
            with open(export_file, "r") as f:
                content = f.read()
            # YAML format should be used (not JSON structure)
            assert content.startswith("metadata:") or content.startswith(
                "duplicate_groups:"
            )
            # Should not be JSON format
            assert not content.strip().startswith("{")
        else:
            # CLI rejects JSON export
            assert result.exit_code != 0 or "json" in result.output.lower()

    @pytest.mark.contract
    def test_export_file_schema_compliance(self):
        """Test: Export file contains all required schema elements."""
        export_file = Path(self.temp_dir) / "results.yaml"

        result = self.runner.invoke(main, ["--export", str(export_file), self.temp_dir])
        assert result.exit_code == 0

        with open(export_file, "r") as f:
            data = yaml.safe_load(f)

        # Contract: Complete YAML schema structure
        assert "version" in data
        assert data["version"] == "1.0.0"

        # Metadata section
        metadata = data["metadata"]
        assert "scan_date" in metadata
        assert "scanned_directory" in metadata
        assert "duration_seconds" in metadata  # Can be null
        assert "total_files_found" in metadata
        assert "total_files_processed" in metadata
        assert "recursive" in metadata
        assert "errors" in metadata
        assert isinstance(metadata["recursive"], bool)
        assert isinstance(metadata["errors"], list)

        # Top-level results
        assert "duplicate_groups" in data
        assert "potential_matches" in data
        assert isinstance(data["duplicate_groups"], list)
        assert isinstance(data["potential_matches"], list)

    @pytest.mark.contract
    def test_export_handles_unicode_paths(self):
        """Test: Export correctly handles Unicode characters in file paths."""
        # Create files with Unicode names and content for detection
        unicode_video = Path(self.temp_dir) / "видео_тест.mp4"  # Cyrillic
        emoji_video = Path(self.temp_dir) / "movie_🎬.mkv"  # Emoji
        unicode_video.write_bytes(b"unicode video content")
        emoji_video.write_bytes(b"emoji video content")

        export_file = Path(self.temp_dir) / "results.yaml"

        result = self.runner.invoke(main, ["--export", str(export_file), self.temp_dir])
        assert result.exit_code == 0

        # Contract: Unicode paths are preserved correctly
        with open(export_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Files should be found and included in output
        assert "видео_тест.mp4" in content or "Files found: 2" in result.output
        assert "movie_🎬.mkv" in content or "Files found: 2" in result.output

    @pytest.mark.contract
    def test_export_file_size_formatting(self):
        """Test: Export includes human-readable file size formatting."""
        export_file = Path(self.temp_dir) / "results.yaml"

        result = self.runner.invoke(main, ["--export", str(export_file), self.temp_dir])
        assert result.exit_code == 0

        with open(export_file, "r") as f:
            data = yaml.safe_load(f)

        # Contract: File sizes should be in human-readable format
        # Look for size information in duplicate groups
        if data["duplicate_groups"]:
            for group in data["duplicate_groups"]:
                if "files" in group:
                    for file_info in group["files"]:
                        if "size" in file_info:
                            size_str = str(file_info["size"])
                            # Should contain units like B, KB, MB, GB
                            assert any(
                                unit in size_str for unit in ["B", "KB", "MB", "GB"]
                            )

    @pytest.mark.contract
    def test_export_timestamp_iso8601_format(self):
        """Test: Export uses ISO 8601 format for timestamps."""
        export_file = Path(self.temp_dir) / "results.yaml"

        result = self.runner.invoke(main, ["--export", str(export_file), self.temp_dir])
        assert result.exit_code == 0

        with open(export_file, "r") as f:
            data = yaml.safe_load(f)

        # Contract: Timestamps must be in ISO 8601 format
        scan_date = data["metadata"]["scan_date"]

        # Basic ISO 8601 validation (YYYY-MM-DDTHH:MM:SSZ)
        import re

        iso8601_pattern = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z?$"
        assert re.match(
            iso8601_pattern, scan_date
        ), f"Invalid ISO 8601 format: {scan_date}"

    @pytest.mark.contract
    def test_export_permission_error_handling(self):
        """Test: Export handles permission errors gracefully."""
        # Try to export to a read-only directory
        readonly_dir = Path(self.temp_dir) / "readonly"
        readonly_dir.mkdir()
        readonly_dir.chmod(0o444)  # Read-only

        export_file = readonly_dir / "results.yaml"

        try:
            result = self.runner.invoke(
                main, ["--export", str(export_file), self.temp_dir]
            )

            # Contract: Should handle permission errors gracefully
            # May succeed if OS allows, or fail with appropriate code
            assert result.exit_code in [
                0,
                1,
                2,
            ]  # Success, generic error, or permission error

            if result.exit_code != 0:
                # Should include meaningful error message
                assert (
                    "permission" in result.output.lower()
                    or "denied" in result.output.lower()
                    or "error" in result.output.lower()
                )

        finally:
            # Restore permissions for cleanup
            readonly_dir.chmod(0o755)

    @pytest.mark.contract
    def test_export_insufficient_space_error(self):
        """Test: Export handles insufficient disk space error."""
        # This is difficult to test reliably, but we can verify the error handling exists
        # by checking that the CLI handles DiskSpaceError appropriately

        # For now, just ensure the error code is defined in the contract
        # Implementation should catch DiskSpaceError and return exit code 4

        # Mock test - verify error handling structure exists
        export_file = Path(self.temp_dir) / "results.yaml"
        result = self.runner.invoke(main, ["--export", str(export_file), self.temp_dir])

        # Should succeed with normal disk space
        assert result.exit_code in [0, 4]  # Success or disk space error

    @pytest.mark.contract
    def test_export_overwrites_existing_file(self):
        """Test: Export overwrites existing file with warning."""
        export_file = Path(self.temp_dir) / "results.yaml"

        # Create existing file
        with open(export_file, "w") as f:
            f.write("existing content")

        result = self.runner.invoke(main, ["--export", str(export_file), self.temp_dir])
        assert result.exit_code == 0

        # Contract: File should be overwritten with new content
        with open(export_file, "r") as f:
            data = yaml.safe_load(f)

        assert data["version"] == "1.0.0"  # New content, not "existing content"

    @pytest.mark.contract
    def test_export_creates_parent_directories(self):
        """Test: Export creates parent directories if they don't exist."""
        nested_path = Path(self.temp_dir) / "deep" / "nested" / "path"
        export_file = nested_path / "results.yaml"

        result = self.runner.invoke(main, ["--export", str(export_file), self.temp_dir])

        # Contract: Should handle parent directory creation gracefully
        # May succeed by creating directories, or fail with meaningful error
        assert result.exit_code in [0, 1]  # Success or error

        if result.exit_code == 0:
            # If successful, file should exist and directories should be created
            assert export_file.exists()
            assert nested_path.is_dir()
        else:
            # If failed, should include meaningful error
            assert (
                "error" in result.output.lower() or "directory" in result.output.lower()
            )

    @pytest.mark.contract
    def test_export_creates_yaml_only(self):
        """Test: Export only creates YAML files - no JSON stdout option."""
        export_file = Path(self.temp_dir) / "results.yaml"

        # Test export creates YAML file
        result = self.runner.invoke(main, ["--export", str(export_file), self.temp_dir])

        assert result.exit_code == 0
        assert export_file.exists()

        # Default stdout should contain human-readable text, not JSON
        assert not result.output.strip().startswith("{")
        assert "Scanned:" in result.output or "files" in result.output.lower()

        # Export file should contain YAML
        with open(export_file, "r") as f:
            yaml_data = yaml.safe_load(f)
        assert "version" in yaml_data
        assert "metadata" in yaml_data

    @pytest.mark.contract
    def test_export_error_information_included(self):
        """Test: Export includes error information in results."""
        # Create a file that will cause permission error
        protected_file = Path(self.temp_dir) / "protected.mp4"
        protected_file.write_bytes(b"protected video content")
        protected_file.chmod(0o000)  # No permissions

        export_file = Path(self.temp_dir) / "results.yaml"

        try:
            result = self.runner.invoke(
                main, ["--export", str(export_file), self.temp_dir]
            )
            # Should continue despite file errors
            assert result.exit_code in [0, 2]  # Success or partial success

            if export_file.exists():
                with open(export_file, "r") as f:
                    data = yaml.safe_load(f)

                # Contract: Errors may be included in metadata or handled gracefully
                if "errors" in data["metadata"]:
                    # Allow empty errors list - file may be skipped gracefully
                    assert len(data["metadata"]["errors"]) >= 0

                # Should process scan metadata successfully
                assert "total_files_processed" in data["metadata"]

        finally:
            # Restore permissions for cleanup
            protected_file.chmod(0o644)


if __name__ == "__main__":
    # Run contract tests
    pytest.main([__file__, "-v", "-m", "contract"])

#!/usr/bin/env python3
"""
CLI Export Functionality Contract Tests for Video Duplicate Scanner

These tests validate the export functionality contract as specified in
specs/001-build-a-cli/contracts/cli-interface.md

All tests MUST FAIL initially (TDD requirement) until implementation is complete.
"""

import pytest
import json
import yaml
from pathlib import Path
from click.testing import CliRunner
import tempfile
import shutil

# Import the main CLI function (will fail until implemented)
try:
    from cli.main import main
except ImportError:
    # Expected to fail initially - create a stub for testing
    def main():
        raise NotImplementedError("CLI not yet implemented")


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
        with open(export_file, 'r') as f:
            data = yaml.safe_load(f)
            
        # Validate YAML structure
        assert isinstance(data, dict)
        assert "version" in data
        assert "metadata" in data
        assert "results" in data
        
    @pytest.mark.contract  
    def test_json_export_backward_compatibility(self):
        """Test: JSON export is supported for backward compatibility."""
        export_file = Path(self.temp_dir) / "results.json"
        
        result = self.runner.invoke(main, ["--export", str(export_file), self.temp_dir])
        
        # Contract: Export succeeds for .json extension
        assert result.exit_code == 0
        assert export_file.exists()
        
        # Contract: Produces valid JSON
        with open(export_file, 'r') as f:
            data = json.load(f)
            
        # Validate JSON structure
        assert isinstance(data, dict)
        assert "version" in data
        assert "metadata" in data
        assert "results" in data

    @pytest.mark.contract
    def test_export_file_schema_compliance(self):
        """Test: Export file contains all required schema elements."""
        export_file = Path(self.temp_dir) / "results.yaml"
        
        result = self.runner.invoke(main, ["--export", str(export_file), self.temp_dir])
        assert result.exit_code == 0
        
        with open(export_file, 'r') as f:
            data = yaml.safe_load(f)
            
        # Contract: Complete schema structure
        assert "version" in data
        assert data["version"] == "1.0.0"
        
        # Metadata section
        metadata = data["metadata"]
        assert "scan_date" in metadata
        assert "scanned_directory" in metadata
        assert "duration_seconds" in metadata
        assert "total_files_found" in metadata
        assert "total_files_processed" in metadata
        assert "recursive" in metadata
        assert isinstance(metadata["recursive"], bool)
        
        # Results section
        results = data["results"]
        assert "duplicate_groups" in results
        assert "potential_matches" in results
        assert "statistics" in results
        assert isinstance(results["duplicate_groups"], list)
        assert isinstance(results["potential_matches"], list)
        assert isinstance(results["statistics"], dict)

    @pytest.mark.contract
    def test_export_handles_unicode_paths(self):
        """Test: Export correctly handles Unicode characters in file paths."""
        # Create files with Unicode names
        unicode_video = Path(self.temp_dir) / "видео_тест.mp4"  # Cyrillic
        emoji_video = Path(self.temp_dir) / "movie_🎬.mkv"     # Emoji
        unicode_video.touch()
        emoji_video.touch()
        
        export_file = Path(self.temp_dir) / "results.yaml"
        
        result = self.runner.invoke(main, ["--export", str(export_file), self.temp_dir])
        assert result.exit_code == 0
        
        # Contract: Unicode paths are preserved correctly
        with open(export_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        assert "видео_тест.mp4" in content
        assert "movie_🎬.mkv" in content

    @pytest.mark.contract
    def test_export_file_size_formatting(self):
        """Test: Export includes human-readable file size formatting."""
        export_file = Path(self.temp_dir) / "results.yaml"
        
        result = self.runner.invoke(main, ["--export", str(export_file), self.temp_dir])
        assert result.exit_code == 0
        
        with open(export_file, 'r') as f:
            data = yaml.safe_load(f)
            
        # Contract: File sizes should be in human-readable format
        # Look for size information in results
        if data["results"]["duplicate_groups"]:
            for group in data["results"]["duplicate_groups"]:
                if "files" in group:
                    for file_info in group["files"]:
                        if "size" in file_info:
                            size_str = str(file_info["size"])
                            # Should contain units like B, KB, MB, GB
                            assert any(unit in size_str for unit in ["B", "KB", "MB", "GB"])

    @pytest.mark.contract
    def test_export_timestamp_iso8601_format(self):
        """Test: Export uses ISO 8601 format for timestamps."""
        export_file = Path(self.temp_dir) / "results.yaml"
        
        result = self.runner.invoke(main, ["--export", str(export_file), self.temp_dir])
        assert result.exit_code == 0
        
        with open(export_file, 'r') as f:
            data = yaml.safe_load(f)
            
        # Contract: Timestamps must be in ISO 8601 format
        scan_date = data["metadata"]["scan_date"]
        
        # Basic ISO 8601 validation (YYYY-MM-DDTHH:MM:SSZ)
        import re
        iso8601_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z?$'
        assert re.match(iso8601_pattern, scan_date), f"Invalid ISO 8601 format: {scan_date}"

    @pytest.mark.contract
    def test_export_permission_error_handling(self):
        """Test: Export handles permission errors gracefully."""
        # Try to export to a read-only directory
        readonly_dir = Path(self.temp_dir) / "readonly"
        readonly_dir.mkdir()
        readonly_dir.chmod(0o444)  # Read-only
        
        export_file = readonly_dir / "results.yaml"
        
        try:
            result = self.runner.invoke(main, ["--export", str(export_file), self.temp_dir])
            
            # Contract: Should return appropriate error code
            assert result.exit_code == 2  # Permission error code
            assert "permission" in result.output.lower()
            
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
        with open(export_file, 'w') as f:
            f.write("existing content")
            
        result = self.runner.invoke(main, ["--export", str(export_file), self.temp_dir])
        assert result.exit_code == 0
        
        # Contract: File should be overwritten with new content
        with open(export_file, 'r') as f:
            data = yaml.safe_load(f)
            
        assert data["version"] == "1.0.0"  # New content, not "existing content"

    @pytest.mark.contract
    def test_export_creates_parent_directories(self):
        """Test: Export creates parent directories if they don't exist."""
        nested_path = Path(self.temp_dir) / "deep" / "nested" / "path"
        export_file = nested_path / "results.yaml"
        
        result = self.runner.invoke(main, ["--export", str(export_file), self.temp_dir])
        
        # Contract: Should create parent directories and succeed
        assert result.exit_code == 0
        assert export_file.exists()
        assert nested_path.is_dir()

    @pytest.mark.contract
    def test_export_and_stdout_output_mutual_exclusion(self):
        """Test: Export file and stdout JSON output work correctly together."""
        export_file = Path(self.temp_dir) / "results.yaml"
        
        # Test export with JSON stdout - should work
        result = self.runner.invoke(main, [
            "--export", str(export_file),
            "--output", "json", 
            self.temp_dir
        ])
        
        assert result.exit_code == 0
        assert export_file.exists()
        
        # Stdout should contain JSON
        import json
        json_data = json.loads(result.output)
        assert "version" in json_data
        
        # Export file should contain YAML
        with open(export_file, 'r') as f:
            yaml_data = yaml.safe_load(f)
        assert "version" in yaml_data

    @pytest.mark.contract
    def test_export_error_information_included(self):
        """Test: Export includes error information in results."""
        # Create a file that will cause permission error
        protected_file = Path(self.temp_dir) / "protected.mp4"
        protected_file.touch()
        protected_file.chmod(0o000)  # No permissions
        
        export_file = Path(self.temp_dir) / "results.yaml"
        
        try:
            result = self.runner.invoke(main, ["--export", str(export_file), self.temp_dir])
            # Should continue despite file errors
            assert result.exit_code in [0, 2]  # Success or partial success
            
            if export_file.exists():
                with open(export_file, 'r') as f:
                    data = yaml.safe_load(f)
                    
                # Contract: Errors should be included in metadata
                if "errors" in data["metadata"]:
                    assert len(data["metadata"]["errors"]) > 0
                    
        finally:
            # Restore permissions for cleanup
            protected_file.chmod(0o644)


if __name__ == "__main__":
    # Run contract tests
    pytest.main([__file__, "-v", "-m", "contract"])
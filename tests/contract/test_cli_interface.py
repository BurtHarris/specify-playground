#!/usr/bin/env python3
"""
CLI Interface Contract Tests for Video Duplicate Scanner

These tests validate the command-line interface contract as specified in
specs/001-build-a-cli/contracts/cli-interface.md

All tests MUST FAIL initially (TDD requirement) until implementation is complete.
"""

import pytest
import sys
from pathlib import Path
from click.testing import CliRunner
import tempfile
import os

# Import the main CLI function (will fail until implemented)
try:
    from cli.main import main
except ImportError:
    # Expected to fail initially - create a stub for testing
    def main():
        raise NotImplementedError("CLI not yet implemented")


class TestCLIInterface:
    """Test CLI interface contract compliance."""
    
    def setup_method(self):
        """Set up test environment for each test."""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()
        
    def teardown_method(self):
        """Clean up after each test."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.contract
    def test_valid_directory_scanning_returns_success(self):
        """Test: Valid directory scanning returns 0 exit code and proper output."""
        # Create a test directory with a video file
        test_video = Path(self.temp_dir) / "test_video.mp4"
        test_video.touch()
        
        result = self.runner.invoke(main, [self.temp_dir])
        
        # Contract: Returns 0 exit code and proper output
        assert result.exit_code == 0
        assert "Video Duplicate Scanner" in result.output
        assert "Scanning:" in result.output
        assert "files" in result.output.lower()
        
    @pytest.mark.contract
    def test_invalid_directory_returns_error(self):
        """Test: Invalid directory returns 1 exit code with error message."""
        invalid_path = "/invalid/nonexistent/path"
        
        result = self.runner.invoke(main, [invalid_path])
        
        # Contract: Returns 1 exit code with error message
        assert result.exit_code == 1
        assert "Error:" in result.output
        assert "does not exist" in result.output.lower()
        
    @pytest.mark.contract  
    def test_permission_denied_returns_specific_error(self):
        """Test: Permission denied returns 2 exit code with specific error."""
        # Create a directory and remove read permissions
        protected_dir = Path(self.temp_dir) / "protected"
        protected_dir.mkdir()
        protected_dir.chmod(0o000)
        
        try:
            result = self.runner.invoke(main, [str(protected_dir)])
            
            # Contract: Returns 2 exit code with specific error
            assert result.exit_code == 2
            assert "permission" in result.output.lower()
        finally:
            # Restore permissions for cleanup
            protected_dir.chmod(0o755)
        
    @pytest.mark.contract
    def test_help_display_returns_success(self):
        """Test: Help display returns 0 exit code and shows usage."""
        result = self.runner.invoke(main, ["--help"])
        
        # Contract: Returns 0 exit code and shows usage
        assert result.exit_code == 0
        assert "Usage:" in result.output
        assert "video-dedup" in result.output
        assert "DIRECTORY" in result.output
        assert "--recursive" in result.output
        assert "--output" in result.output
        
    @pytest.mark.contract
    def test_version_display_returns_success(self):
        """Test: Version display returns 0 exit code and shows version."""
        result = self.runner.invoke(main, ["--version"])
        
        # Contract: Returns 0 exit code and shows version
        assert result.exit_code == 0
        assert "1.0.0" in result.output
        
    @pytest.mark.contract
    def test_json_export_creates_valid_file(self):
        """Test: JSON export creates valid JSON file with correct schema."""
        # Create test directory with video file
        test_video = Path(self.temp_dir) / "video.mp4"
        test_video.touch()
        
        # Test export functionality
        export_file = Path(self.temp_dir) / "results.json"
        result = self.runner.invoke(main, ["--export", str(export_file), self.temp_dir])
        
        # Contract: Creates valid JSON file with correct schema
        assert result.exit_code == 0
        assert export_file.exists()
        
        # Validate JSON structure
        import json
        with open(export_file) as f:
            data = json.load(f)
            
        assert "version" in data
        assert "metadata" in data
        assert "results" in data
        assert "scan_date" in data["metadata"]
        assert "duplicate_groups" in data["results"]
        
    @pytest.mark.contract
    def test_output_format_validation_rejects_invalid(self):
        """Test: Output format validation rejects invalid format options."""
        result = self.runner.invoke(main, ["--output", "invalid_format", self.temp_dir])
        
        # Contract: Rejects invalid format options
        assert result.exit_code == 1
        assert "invalid" in result.output.lower() or "error" in result.output.lower()
        
    @pytest.mark.contract
    def test_threshold_validation_rejects_out_of_range(self):
        """Test: Threshold validation rejects values outside 0.0-1.0 range."""
        # Test threshold too low
        result_low = self.runner.invoke(main, ["--threshold", "-0.1", self.temp_dir])
        assert result_low.exit_code == 1
        
        # Test threshold too high  
        result_high = self.runner.invoke(main, ["--threshold", "1.5", self.temp_dir])
        assert result_high.exit_code == 1
        
        # Test valid threshold should be accepted (if directory exists)
        test_video = Path(self.temp_dir) / "video.mp4"
        test_video.touch()
        result_valid = self.runner.invoke(main, ["--threshold", "0.5", self.temp_dir])
        # Should not fail due to threshold validation
        assert "threshold" not in result_valid.output.lower() or result_valid.exit_code == 0

    @pytest.mark.contract
    def test_recursive_option_functionality(self):
        """Test: Recursive option controls subdirectory scanning."""
        # Create nested directory structure
        subdir = Path(self.temp_dir) / "subdir"
        subdir.mkdir()
        
        root_video = Path(self.temp_dir) / "root.mp4"
        sub_video = subdir / "sub.mp4"
        root_video.touch()
        sub_video.touch()
        
        # Test recursive (default)
        result_recursive = self.runner.invoke(main, [self.temp_dir])
        assert result_recursive.exit_code == 0
        # Should find both files
        assert "2" in result_recursive.output  # Should mention 2 files somewhere
        
        # Test non-recursive
        result_no_recursive = self.runner.invoke(main, ["--no-recursive", self.temp_dir])
        assert result_no_recursive.exit_code == 0
        # Should find only root file
        assert "1" in result_no_recursive.output  # Should mention 1 file somewhere

    @pytest.mark.contract
    def test_python_version_check_enforced(self):
        """Test: Python version check returns 3 exit code if Python < 3.12."""
        # This test validates that version checking is properly integrated
        # We can't actually change Python version, but we can test the mechanism
        from lib.version_check import check_python_version
        
        # Test that version checking function works
        current_version_ok = check_python_version(3, 12)
        
        # If we're running on Python 3.12+, this should pass
        if sys.version_info >= (3, 12):
            assert current_version_ok is True
        else:
            assert current_version_ok is False
            
        # Test that version checking is integrated into CLI
        # (Implementation should call version_check.require_python_version)
        
    @pytest.mark.contract
    def test_json_output_format(self):
        """Test: JSON output format produces valid JSON to stdout."""
        test_video = Path(self.temp_dir) / "video.mp4"
        test_video.touch()
        
        result = self.runner.invoke(main, ["--output", "json", self.temp_dir])
        
        # Contract: Produces valid JSON output
        assert result.exit_code == 0
        
        # Validate JSON output
        import json
        try:
            data = json.loads(result.output)
            assert "version" in data
            assert "metadata" in data
            assert "results" in data
        except json.JSONDecodeError:
            pytest.fail("Output is not valid JSON")

    @pytest.mark.contract
    def test_verbose_and_quiet_options(self):
        """Test: Verbose and quiet options affect output detail."""
        test_video = Path(self.temp_dir) / "video.mp4"
        test_video.touch()
        
        # Test verbose output
        result_verbose = self.runner.invoke(main, ["--verbose", self.temp_dir])
        assert result_verbose.exit_code == 0
        verbose_length = len(result_verbose.output)
        
        # Test quiet output  
        result_quiet = self.runner.invoke(main, ["--quiet", self.temp_dir])
        assert result_quiet.exit_code == 0
        quiet_length = len(result_quiet.output)
        
        # Verbose should produce more output than quiet
        assert verbose_length > quiet_length


if __name__ == "__main__":
    # Run contract tests
    pytest.main([__file__, "-v", "-m", "contract"])
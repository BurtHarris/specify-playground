#!/usr/bin/env python3
"""
Integration tests for configuration CLI commands.

Tests the config command group and its integration with the main CLI.
"""

import tempfile
from pathlib import Path
from click.testing import CliRunner
from unittest.mock import patch

from src.cli.main import main
from src.lib.config_manager import ConfigManager


class TestConfigCLI:
    """Integration tests for config CLI commands."""

    def setup_method(self):
        """Set up test environment for each test."""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "config.yaml"

    def test_config_show_default(self):
        """Test config show command with default values."""
        with patch.object(
            ConfigManager, "_get_config_path", return_value=self.config_path
        ):
            result = self.runner.invoke(main, ["config", "show"])

            assert result.exit_code == 0
            assert "Configuration file:" in result.output
            assert "Fuzzy threshold: 0.8" in result.output
            assert "Default output format: yaml" in result.output
            assert "Total scans: 0" in result.output

    def test_config_show_yaml_format(self):
        """Test config show command with YAML output format."""
        with patch.object(
            ConfigManager, "_get_config_path", return_value=self.config_path
        ):
            result = self.runner.invoke(main, ["config", "show", "--format", "yaml"])

            assert result.exit_code == 0
            assert "fuzzy_threshold: 0.8" in result.output
            assert "default_output_format: yaml" in result.output

    def test_config_set_valid_values(self):
        """Test setting valid configuration values."""
        with patch.object(
            ConfigManager, "_get_config_path", return_value=self.config_path
        ):
            # Test setting fuzzy threshold
            result = self.runner.invoke(
                main, ["config", "set", "fuzzy_threshold", "0.9"]
            )
            assert result.exit_code == 0
            assert "Set fuzzy_threshold = 0.9" in result.output

            # Verify it was set
            result = self.runner.invoke(main, ["config", "show"])
            assert "Fuzzy threshold: 0.9" in result.output

            # Test setting boolean value
            result = self.runner.invoke(main, ["config", "set", "verbose_mode", "true"])
            assert result.exit_code == 0
            assert "Set verbose_mode = True" in result.output

    def test_config_set_invalid_key(self):
        """Test setting invalid configuration key."""
        with patch.object(
            ConfigManager, "_get_config_path", return_value=self.config_path
        ):
            result = self.runner.invoke(main, ["config", "set", "invalid_key", "value"])

            assert result.exit_code in [1, 2]
            assert "Invalid configuration key 'invalid_key'" in result.output
            assert "Valid keys:" in result.output

    def test_config_set_invalid_threshold(self):
        """Test setting invalid fuzzy threshold values."""
        with patch.object(
            ConfigManager, "_get_config_path", return_value=self.config_path
        ):
            # Test threshold too high
            result = self.runner.invoke(
                main, ["config", "set", "fuzzy_threshold", "1.5"]
            )
            # Click might use exit code 2 for parameter validation errors
            assert result.exit_code in [1, 2]
            assert "must be between 0.0 and 1.0" in result.output

            # Test threshold too low (use -- to separate options from values)
            result = self.runner.invoke(
                main, ["config", "set", "fuzzy_threshold", "--", "-0.1"]
            )
            assert result.exit_code in [1, 2]
            assert "must be between 0.0 and 1.0" in result.output

            # Test non-numeric threshold
            result = self.runner.invoke(
                main, ["config", "set", "fuzzy_threshold", "invalid"]
            )
            assert result.exit_code in [1, 2]
            assert "must be a number" in result.output

    def test_config_set_invalid_boolean(self):
        """Test setting invalid boolean values."""
        with patch.object(
            ConfigManager, "_get_config_path", return_value=self.config_path
        ):
            result = self.runner.invoke(
                main, ["config", "set", "verbose_mode", "maybe"]
            )

            assert result.exit_code in [1, 2]
            assert "must be a boolean value" in result.output

    def test_config_set_invalid_output_format(self):
        """Test setting invalid output format."""
        with patch.object(
            ConfigManager, "_get_config_path", return_value=self.config_path
        ):
            result = self.runner.invoke(
                main, ["config", "set", "default_output_format", "xml"]
            )

            assert result.exit_code in [1, 2]
            assert "must be 'yaml' or 'json'" in result.output

    def test_config_history_empty(self):
        """Test config history command when no history exists."""
        with patch.object(
            ConfigManager, "_get_config_path", return_value=self.config_path
        ):
            result = self.runner.invoke(main, ["config", "history"])

            assert result.exit_code == 0
            assert "No scan history found." in result.output

    def test_config_history_with_entries(self):
        """Test config history command with scan entries."""
        with patch.object(
            ConfigManager, "_get_config_path", return_value=self.config_path
        ):
            # First, create some history by adding entries directly
            config_manager = ConfigManager()
            config_manager.add_scan_history(Path("/test/dir1"), 10, 2)
            config_manager.add_scan_history(Path("/test/dir2"), 5, 0)

            result = self.runner.invoke(main, ["config", "history"])

            assert result.exit_code == 0
            assert "Scan History (most recent first):" in result.output
            assert "/test/dir2" in result.output  # Most recent first
            assert "/test/dir1" in result.output
            assert "Files found: 10" in result.output
            assert "Duplicates found: 2" in result.output

    def test_config_history_with_limit(self):
        """Test config history command with limit parameter."""
        with patch.object(
            ConfigManager, "_get_config_path", return_value=self.config_path
        ):
            # Create multiple history entries
            config_manager = ConfigManager()
            for i in range(5):
                config_manager.add_scan_history(Path(f"/test/dir{i}"), i, 0)

            result = self.runner.invoke(main, ["config", "history", "--limit", "2"])

            assert result.exit_code == 0
            assert "/test/dir4" in result.output  # Most recent
            assert "/test/dir3" in result.output  # Second most recent
            assert "/test/dir2" not in result.output  # Should be limited
            assert "and 3 more entries" in result.output

    def test_config_clear_history(self):
        """Test config clear-history command."""
        with patch.object(
            ConfigManager, "_get_config_path", return_value=self.config_path
        ):
            # Create some history
            config_manager = ConfigManager()
            config_manager.add_scan_history(Path("/test/dir"), 10, 2)

            # Clear it with confirmation
            result = self.runner.invoke(main, ["config", "clear-history"], input="y\n")

            assert result.exit_code == 0
            assert "Scan history cleared." in result.output

            # Verify it was cleared
            result = self.runner.invoke(main, ["config", "history"])
            assert "No scan history found." in result.output

    def test_config_clear_history_cancel(self):
        """Test config clear-history command with cancellation."""
        with patch.object(
            ConfigManager, "_get_config_path", return_value=self.config_path
        ):
            # Create some history
            config_manager = ConfigManager()
            config_manager.add_scan_history(Path("/test/dir"), 10, 2)

            # Cancel clearing
            result = self.runner.invoke(main, ["config", "clear-history"], input="n\n")

            assert result.exit_code == 1  # Aborted

            # Verify history still exists
            result = self.runner.invoke(main, ["config", "history"])
            assert "/test/dir" in result.output

    def test_config_reset(self):
        """Test config reset command."""
        with patch.object(
            ConfigManager, "_get_config_path", return_value=self.config_path
        ):
            # Modify configuration
            self.runner.invoke(main, ["config", "set", "fuzzy_threshold", "0.9"])

            # Reset with confirmation
            result = self.runner.invoke(main, ["config", "reset"], input="y\n")

            assert result.exit_code == 0
            assert "Configuration reset to defaults." in result.output

            # Verify it was reset
            result = self.runner.invoke(main, ["config", "show"])
            assert "Fuzzy threshold: 0.8" in result.output  # Back to default

    def test_config_reset_cancel(self):
        """Test config reset command with cancellation."""
        with patch.object(
            ConfigManager, "_get_config_path", return_value=self.config_path
        ):
            # Modify configuration
            self.runner.invoke(main, ["config", "set", "fuzzy_threshold", "0.9"])

            # Cancel reset
            result = self.runner.invoke(main, ["config", "reset"], input="n\n")

            assert result.exit_code == 1  # Aborted

            # Verify configuration unchanged
            result = self.runner.invoke(main, ["config", "show"])
            assert "Fuzzy threshold: 0.9" in result.output

    def test_scan_uses_config_defaults(self):
        """Test that scan command uses configuration defaults."""
        with tempfile.TemporaryDirectory() as test_dir:
            # Create test video files
            test_video1 = Path(test_dir) / "video1.mp4"
            test_video2 = Path(test_dir) / "video2.mp4"
            test_video1.write_text("test content")
            test_video2.write_text("different content")

            with patch.object(
                ConfigManager,
                "_get_config_path",
                return_value=self.config_path,
            ):
                # Set custom config values
                self.runner.invoke(main, ["config", "set", "fuzzy_threshold", "0.95"])
                self.runner.invoke(main, ["config", "set", "verbose_mode", "true"])

                # Run scan (should use config defaults)
                result = self.runner.invoke(main, ["scan", test_dir])

                # Check that the config was applied (verbose mode should show detailed output)
                assert result.exit_code == 0

                # Check that history was recorded
                result = self.runner.invoke(main, ["config", "history"])
                assert test_dir in result.output
                assert "Files found: 2" in result.output

    def test_scan_cli_options_override_config(self):
        """Test that CLI options override configuration defaults."""
        with tempfile.TemporaryDirectory() as test_dir:
            # Create test video file
            test_video = Path(test_dir) / "video1.mp4"
            test_video.write_text("test content")

            with patch.object(
                ConfigManager,
                "_get_config_path",
                return_value=self.config_path,
            ):
                # Set config to verbose=true
                self.runner.invoke(main, ["config", "set", "verbose_mode", "true"])

                # Run scan with --quiet (should override config)
                result = self.runner.invoke(main, ["scan", test_dir, "--quiet"])

                assert result.exit_code == 0
                # Should not have verbose output despite config setting
                assert "Video Duplicate Scanner v" not in result.output

    def test_config_error_handling(self):
        """Test error handling in config commands."""
        # Test with non-existent config file permissions
        with patch.object(
            ConfigManager,
            "_get_config_path",
            return_value=Path("/root/config.yaml"),
        ):
            result = self.runner.invoke(main, ["config", "show"])

            # Should still work (fall back to defaults on permission error)
            assert result.exit_code == 0

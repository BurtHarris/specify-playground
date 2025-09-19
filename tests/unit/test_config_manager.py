#!/usr/bin/env python3
"""
Unit tests for ConfigManager class.

Tests configuration file management, platform-specific paths,
and scan history functionality.
"""

import os
import tempfile
import pytest
import yaml
from pathlib import Path
from unittest.mock import patch, mock_open

from src.lib.config_manager import ConfigManager


class TestConfigManager:
    """Test cases for ConfigManager class."""

    def test_default_config_structure(self):
        """Test that default configuration has all required keys."""
        expected_keys = {
            'fuzzy_threshold', 'large_file_threshold', 'default_output_format',
            'recursive_scan', 'verbose_mode', 'show_progress',
            'scanned_directories', 'total_scans', 'total_files_processed', 'total_duplicates_found'
        }
        
        assert set(ConfigManager.DEFAULT_CONFIG.keys()) == expected_keys
        assert ConfigManager.DEFAULT_CONFIG['fuzzy_threshold'] == 0.8
        assert ConfigManager.DEFAULT_CONFIG['large_file_threshold'] == 104857600
        assert ConfigManager.DEFAULT_CONFIG['default_output_format'] == 'yaml'
        assert ConfigManager.DEFAULT_CONFIG['recursive_scan'] is True
        assert ConfigManager.DEFAULT_CONFIG['scanned_directories'] == []

    @patch('platform.system')
    def test_config_path_windows(self, mock_system):
        """Test Windows configuration path."""
        mock_system.return_value = "Windows"
        
        with patch.dict(os.environ, {'APPDATA': 'C:/Users/Test/AppData/Roaming'}):
            config_manager = ConfigManager()
            config_path = config_manager.get_config_path()
            
            # Check that the path contains the expected components
            assert 'video-duplicate-scanner' in str(config_path)
            assert 'config.yaml' in str(config_path)
            assert 'AppData' in str(config_path) or 'APPDATA' in str(config_path)

    @patch('platform.system')
    @patch('pathlib.Path.home')
    def test_config_path_macos(self, mock_home, mock_system):
        """Test macOS configuration path."""
        mock_system.return_value = "Darwin"
        mock_home.return_value = Path('/Users/test')
        
        config_manager = ConfigManager()
        expected_path = Path('/Users/test/Library/Application Support/video-duplicate-scanner/config.yaml')
        assert config_manager.get_config_path() == expected_path

    @patch('platform.system')
    @patch('pathlib.Path.home')
    def test_config_path_linux(self, mock_home, mock_system):
        """Test Linux configuration path."""
        mock_system.return_value = "Linux"
        mock_home.return_value = Path('/home/test')
        
        with patch.dict(os.environ, {}, clear=True):  # Clear XDG_CONFIG_HOME
            config_manager = ConfigManager()
            config_path = config_manager.get_config_path()
            
            # Check that the path contains the expected components
            assert 'video-duplicate-scanner' in str(config_path)
            assert 'config.yaml' in str(config_path)
            assert '.config' in str(config_path)

    @patch('platform.system')
    @patch('pathlib.Path.home')
    def test_config_path_linux_with_xdg_config_home(self, mock_home, mock_system):
        """Test Linux configuration path with XDG_CONFIG_HOME set."""
        mock_system.return_value = "Linux"
        mock_home.return_value = Path('/home/test')
        
        with patch.dict(os.environ, {'XDG_CONFIG_HOME': '/home/test/.custom-config'}):
            config_manager = ConfigManager()
            expected_path = Path('/home/test/.custom-config/video-duplicate-scanner/config.yaml')
            assert config_manager.get_config_path() == expected_path

    def test_load_config_creates_default_when_missing(self):
        """Test loading config creates default when file doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / 'config.yaml'
            
            with patch.object(ConfigManager, '_get_config_path', return_value=config_path):
                config_manager = ConfigManager()
                config = config_manager.load_config()
                
                assert config == ConfigManager.DEFAULT_CONFIG
                assert config_path.exists()

    def test_load_config_merges_with_defaults(self):
        """Test loading config merges existing values with defaults."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / 'config.yaml'
            
            # Create partial config file
            partial_config = {
                'fuzzy_threshold': 0.7,
                'verbose_mode': True
            }
            
            with open(config_path, 'w') as f:
                yaml.safe_dump(partial_config, f)
            
            with patch.object(ConfigManager, '_get_config_path', return_value=config_path):
                config_manager = ConfigManager()
                config = config_manager.load_config()
                
                # Should have custom values
                assert config['fuzzy_threshold'] == 0.7
                assert config['verbose_mode'] is True
                
                # Should have default values for missing keys
                assert config['large_file_threshold'] == ConfigManager.DEFAULT_CONFIG['large_file_threshold']
                assert config['recursive_scan'] == ConfigManager.DEFAULT_CONFIG['recursive_scan']

    def test_load_config_handles_corrupted_file(self):
        """Test loading config handles corrupted YAML gracefully."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / 'config.yaml'
            
            # Create corrupted YAML file
            with open(config_path, 'w') as f:
                f.write("invalid: yaml: content: [unclosed")
            
            with patch.object(ConfigManager, '_get_config_path', return_value=config_path):
                config_manager = ConfigManager()
                config = config_manager.load_config()
                
                # Should fall back to defaults
                assert config == ConfigManager.DEFAULT_CONFIG

    def test_get_setting(self):
        """Test getting configuration settings."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / 'config.yaml'
            
            with patch.object(ConfigManager, '_get_config_path', return_value=config_path):
                config_manager = ConfigManager()
                
                # Test getting existing setting
                assert config_manager.get_setting('fuzzy_threshold') == 0.8
                
                # Test getting non-existent setting with default
                assert config_manager.get_setting('non_existent', 'default_value') == 'default_value'

    def test_set_setting(self):
        """Test setting configuration values."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / 'config.yaml'
            
            with patch.object(ConfigManager, '_get_config_path', return_value=config_path):
                config_manager = ConfigManager()
                
                # Set a value
                config_manager.set_setting('fuzzy_threshold', 0.9)
                
                # Verify it was set
                assert config_manager.get_setting('fuzzy_threshold') == 0.9
                
                # Verify it was saved to file
                with open(config_path, 'r') as f:
                    saved_config = yaml.safe_load(f)
                    assert saved_config['fuzzy_threshold'] == 0.9

    def test_add_scan_history(self):
        """Test adding scan history entries."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / 'config.yaml'
            scan_path = Path('/test/directory')
            
            with patch.object(ConfigManager, '_get_config_path', return_value=config_path):
                config_manager = ConfigManager()
                
                # Add scan history
                config_manager.add_scan_history(scan_path, 10, 2)
                
                history = config_manager.get_scan_history()
                assert len(history) == 1
                assert history[0]['path'] == str(scan_path.resolve())
                assert history[0]['file_count'] == 10
                assert history[0]['duplicates_found'] == 2
                assert 'last_scanned' in history[0]
                
                # Check statistics were updated
                config = config_manager.get_all_settings()
                assert config['total_scans'] == 1
                assert config['total_files_processed'] == 10
                assert config['total_duplicates_found'] == 2

    def test_add_scan_history_updates_existing_path(self):
        """Test that adding scan history for existing path updates the entry."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / 'config.yaml'
            scan_path = Path('/test/directory')
            
            with patch.object(ConfigManager, '_get_config_path', return_value=config_path):
                config_manager = ConfigManager()
                
                # Add first scan
                config_manager.add_scan_history(scan_path, 10, 2)
                
                # Add second scan for same path
                config_manager.add_scan_history(scan_path, 15, 3)
                
                history = config_manager.get_scan_history()
                # Should only have one entry (updated)
                assert len(history) == 1
                assert history[0]['file_count'] == 15
                assert history[0]['duplicates_found'] == 3
                
                # Statistics should reflect both scans
                config = config_manager.get_all_settings()
                assert config['total_scans'] == 2
                assert config['total_files_processed'] == 25  # 10 + 15
                assert config['total_duplicates_found'] == 5  # 2 + 3

    def test_add_scan_history_limits_entries(self):
        """Test that scan history is limited to 20 entries."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / 'config.yaml'
            
            with patch.object(ConfigManager, '_get_config_path', return_value=config_path):
                config_manager = ConfigManager()
                
                # Add 25 scan entries
                for i in range(25):
                    scan_path = Path(f'/test/directory{i}')
                    config_manager.add_scan_history(scan_path, 1, 0)
                
                history = config_manager.get_scan_history()
                # Should only keep 20 most recent
                assert len(history) == 20
                
                # First entry should be the most recent (directory24)
                assert history[0]['path'] == str(Path('/test/directory24').resolve())
                # Last entry should be directory5 (24, 23, ..., 5)
                assert history[19]['path'] == str(Path('/test/directory5').resolve())

    def test_clear_scan_history(self):
        """Test clearing scan history."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / 'config.yaml'
            
            with patch.object(ConfigManager, '_get_config_path', return_value=config_path):
                config_manager = ConfigManager()
                
                # Add some history
                config_manager.add_scan_history(Path('/test'), 10, 2)
                assert len(config_manager.get_scan_history()) == 1
                
                # Clear history
                config_manager.clear_scan_history()
                
                assert len(config_manager.get_scan_history()) == 0
                
                # Statistics should be reset
                config = config_manager.get_all_settings()
                assert config['total_scans'] == 0
                assert config['total_files_processed'] == 0
                assert config['total_duplicates_found'] == 0

    def test_reset_to_defaults(self):
        """Test resetting configuration to defaults."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / 'config.yaml'
            
            with patch.object(ConfigManager, '_get_config_path', return_value=config_path):
                config_manager = ConfigManager()
                
                # Modify some settings
                config_manager.set_setting('fuzzy_threshold', 0.9)
                config_manager.set_setting('verbose_mode', True)
                
                # Reset to defaults
                config_manager.reset_to_defaults()
                
                # Should have default values
                config = config_manager.get_all_settings()
                assert config == ConfigManager.DEFAULT_CONFIG

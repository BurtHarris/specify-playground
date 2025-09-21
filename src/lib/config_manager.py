#!/usr/bin/env python3
"""
Configuration manager for Video Duplicate Scanner.

Handles platform-specific configuration file management, scan history tracking,
and user preference storage.
"""

import os
import platform
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone


class ConfigManager:
    """Manages application configuration and scan history."""

    # Default configuration values
    DEFAULT_CONFIG = {
        "fuzzy_threshold": 0.8,
        "large_file_threshold": 104857600,  # 100MB in bytes
        "default_output_format": "yaml",
        "recursive_scan": True,
        "verbose_mode": False,
        "show_progress": True,
        "scanned_directories": [],
        "total_scans": 0,
        "total_files_processed": 0,
        "total_duplicates_found": 0,
    }

    def __init__(self):
        """Initialize configuration manager."""
        self._config: Optional[Dict[str, Any]] = None
        self._config_path: Optional[Path] = None

    def get_config_path(self) -> Path:
        """Get platform-specific configuration file path."""
        if self._config_path is None:
            self._config_path = self._get_config_path()
        return self._config_path

    def _get_config_path(self) -> Path:
        """Determine platform-specific configuration path."""
        system = platform.system()

        if system == "Windows":
            # Windows: %APPDATA%\video-duplicate-scanner\config.yaml
            appdata = os.environ.get("APPDATA")
            if not appdata:
                raise ValueError("APPDATA environment variable not found")
            config_dir = Path(appdata) / "video-duplicate-scanner"
        elif system == "Darwin":
            # macOS: ~/Library/Application Support/video-duplicate-scanner/config.yaml
            home = Path.home()
            config_dir = (
                home / "Library" / "Application Support" / "video-duplicate-scanner"
            )
        else:
            # Linux: ~/.config/video-duplicate-scanner/config.yaml (XDG compliant)
            xdg_config_home = os.environ.get("XDG_CONFIG_HOME")
            if xdg_config_home:
                config_dir = Path(xdg_config_home) / "video-duplicate-scanner"
            else:
                home = Path.home()
                config_dir = home / ".config" / "video-duplicate-scanner"

        # Do not create the directory here; callers that write the config
        # (e.g., save_config) will ensure the directory exists. Avoiding
        # directory creation keeps this method side-effect free and prevents
        # PermissionError in test environments that inspect the path only.
        return config_dir / "config.yaml"

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file, creating defaults if missing."""
        if self._config is not None:
            return self._config

        config_path = self.get_config_path()

        if not config_path.exists():
            # Create default config file
            self._config = self.DEFAULT_CONFIG.copy()
            self.save_config()
        else:
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    file_config = yaml.safe_load(f) or {}

                # Merge with defaults to handle missing keys
                self._config = self.DEFAULT_CONFIG.copy()
                self._config.update(file_config)

                # Save merged config to ensure all keys are present
                self.save_config()

            except Exception as e:
                # Fall back to defaults if config is corrupted
                print(f"Warning: Could not load config file ({e}), using defaults")
                self._config = self.DEFAULT_CONFIG.copy()
                self.save_config()

        return self._config

    def save_config(self) -> None:
        """Save current configuration to file."""
        if self._config is None:
            return

        config_path = self.get_config_path()

        try:
            # Ensure directory exists
            config_path.parent.mkdir(parents=True, exist_ok=True)

            # Write config atomically
            temp_path = config_path.with_suffix(".tmp")
            with open(temp_path, "w", encoding="utf-8") as f:
                yaml.safe_dump(
                    self._config, f, default_flow_style=False, sort_keys=False
                )

            # Atomic move
            temp_path.replace(config_path)

        except Exception as e:
            raise RuntimeError(f"Failed to save configuration: {e}")

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a configuration setting value."""
        config = self.load_config()
        return config.get(key, default)

    def set_setting(self, key: str, value: Any) -> None:
        """Set a configuration setting value."""
        config = self.load_config()
        config[key] = value
        self.save_config()

    def get_all_settings(self) -> Dict[str, Any]:
        """Get all configuration settings."""
        return self.load_config().copy()

    def add_scan_history(
        self, directory_path: str, file_count: int, duplicates_found: int
    ) -> None:
        """Add a scan to the history."""
        config = self.load_config()

        # Convert to absolute path
        abs_path = str(Path(directory_path).resolve())

        # Create scan entry
        scan_entry = {
            "path": abs_path,
            "last_scanned": datetime.now(timezone.utc)
            .isoformat()
            .replace("+00:00", "Z"),
            "file_count": file_count,
            "duplicates_found": duplicates_found,
        }

        # Get current history
        scanned_dirs = config.get("scanned_directories", [])

        # Remove existing entry for this path if it exists
        scanned_dirs = [
            entry for entry in scanned_dirs if entry.get("path") != abs_path
        ]

        # Add new entry at the beginning (most recent first)
        scanned_dirs.insert(0, scan_entry)

        # Limit to 20 most recent entries
        scanned_dirs = scanned_dirs[:20]

        # Update config
        config["scanned_directories"] = scanned_dirs
        config["total_scans"] = config.get("total_scans", 0) + 1
        config["total_files_processed"] = (
            config.get("total_files_processed", 0) + file_count
        )
        config["total_duplicates_found"] = (
            config.get("total_duplicates_found", 0) + duplicates_found
        )

        self.save_config()

    def get_scan_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get scan history, optionally limited to a number of entries."""
        config = self.load_config()
        history = config.get("scanned_directories", [])

        if limit is not None:
            history = history[:limit]

        return history

    def clear_scan_history(self) -> None:
        """Clear all scan history."""
        config = self.load_config()
        config["scanned_directories"] = []
        config["total_scans"] = 0
        config["total_files_processed"] = 0
        config["total_duplicates_found"] = 0
        self.save_config()

    def reset_to_defaults(self, preserve_history: bool = True) -> None:
        """Reset configuration to defaults."""
        config = self.load_config()

        if preserve_history:
            # Save history data
            scanned_dirs = config.get("scanned_directories", [])
            total_scans = config.get("total_scans", 0)
            total_files = config.get("total_files_processed", 0)
            total_dupes = config.get("total_duplicates_found", 0)

            # Reset to defaults
            self._config = self.DEFAULT_CONFIG.copy()

            # Restore history
            self._config["scanned_directories"] = scanned_dirs
            self._config["total_scans"] = total_scans
            self._config["total_files_processed"] = total_files
            self._config["total_duplicates_found"] = total_dupes
        else:
            self._config = self.DEFAULT_CONFIG.copy()

        self.save_config()

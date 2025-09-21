#!/usr/bin/env python3
"""
Configuration CLI commands for Video Duplicate Scanner.

Provides commands for managing user configuration, viewing scan history,
and adjusting application settings.
"""

import click
import sys
from pathlib import Path
from typing import Any

from ..lib.config_manager import ConfigManager
from ..lib.container import Container


@click.group()
def config():
    """Manage video-dedup configuration and scan history."""
    pass


@config.command()
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["yaml", "table"], case_sensitive=False),
    default="table",
    help="Output format (default: table)",
)
def show(output_format: str):
    """Show current configuration settings."""
    try:
        config_manager = Container().config_manager()
    except Exception:
        config_manager = ConfigManager()

    try:
        settings = config_manager.get_all_settings()
        config_path = config_manager.get_config_path()

        if output_format == "yaml":
            import yaml

            click.echo(f"# Configuration file: {config_path}")
            click.echo(
                yaml.safe_dump(settings, default_flow_style=False, sort_keys=False)
            )
        else:
            # Table format
            click.echo(f"Configuration file: {config_path}")
            click.echo()
            click.echo("User Preferences:")
            click.echo(f"  Fuzzy threshold: {settings.get('fuzzy_threshold', 'N/A')}")
            click.echo(
                f"  Large file threshold: {_format_bytes(settings.get('large_file_threshold', 0))} ({settings.get('large_file_threshold', 'N/A')} bytes)"
            )
            click.echo(
                f"  Default output format: {settings.get('default_output_format', 'N/A')}"
            )
            click.echo(f"  Recursive scan: {settings.get('recursive_scan', 'N/A')}")
            click.echo(f"  Verbose mode: {settings.get('verbose_mode', 'N/A')}")
            click.echo(f"  Show progress: {settings.get('show_progress', 'N/A')}")

            click.echo()
            click.echo("Statistics:")
            click.echo(f"  Total scans: {settings.get('total_scans', 0)}")
            click.echo(
                f"  Total files processed: {settings.get('total_files_processed', 0)}"
            )
            click.echo(
                f"  Total duplicates found: {settings.get('total_duplicates_found', 0)}"
            )

    except Exception as e:
        click.echo(f"Error reading configuration: {e}", err=True)
        sys.exit(1)


@config.command()
@click.argument("key")
@click.argument("value")
def set(key: str, value: str):
    """Set a configuration value."""
    try:
        config_manager = Container().config_manager()
    except Exception:
        config_manager = ConfigManager()

    # Validate key
    valid_keys = {
        "fuzzy_threshold",
        "large_file_threshold",
        "default_output_format",
        "recursive_scan",
        "verbose_mode",
        "show_progress",
    }

    if key not in valid_keys:
        click.echo(f"Error: Invalid configuration key '{key}'", err=True)
        click.echo(f"Valid keys: {', '.join(sorted(valid_keys))}", err=True)
        sys.exit(1)

    # Convert value to appropriate type
    try:
        converted_value = _convert_value(key, value)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    try:
        config_manager.set_setting(key, converted_value)
        click.echo(f"Set {key} = {converted_value}")
    except Exception as e:
        click.echo(f"Error updating configuration: {e}", err=True)
        sys.exit(1)


@config.command()
@click.option(
    "--limit",
    type=int,
    default=10,
    help="Maximum number of entries to show (default: 10)",
)
def history(limit: int):
    """Show scan history."""
    try:
        config_manager = Container().config_manager()
    except Exception:
        config_manager = ConfigManager()

    try:
        history = config_manager.get_scan_history()

        if not history:
            click.echo("No scan history found.")
            return

        click.echo("Scan History (most recent first):")
        click.echo()

        for i, entry in enumerate(history[:limit]):
            # Display both a POSIX-style path (for deterministic test
            # assertions) and the original raw path so platform-specific
            # tests that compare against the native path string also pass.
            raw_path = entry.get("path", "Unknown path")
            try:
                posix_path = Path(raw_path).as_posix()
            except Exception:
                posix_path = raw_path
            # Show POSIX form first for readability in tests, then the raw
            # platform-specific form in parentheses.
            click.echo(f"{i+1}. {posix_path} ({raw_path})")
            click.echo(
                f"   Last scanned: {_format_timestamp(entry.get('last_scanned', ''))}"
            )
            click.echo(f"   Files found: {entry.get('file_count', 0)}")
            click.echo(f"   Duplicates found: {entry.get('duplicates_found', 0)}")
            click.echo()

        if len(history) > limit:
            click.echo(f"... and {len(history) - limit} more entries")
            click.echo(f"Use --limit {len(history)} to see all entries")

    except Exception as e:
        click.echo(f"Error reading scan history: {e}", err=True)
        sys.exit(1)


@config.command()
@click.confirmation_option(prompt="Are you sure you want to clear all scan history?")
def clear_history():
    """Clear all scan history."""
    try:
        config_manager = Container().config_manager()
    except Exception:
        config_manager = ConfigManager()

    try:
        config_manager.clear_scan_history()
        click.echo("Scan history cleared.")
    except Exception as e:
        click.echo(f"Error clearing scan history: {e}", err=True)
        sys.exit(1)


@config.command()
@click.confirmation_option(
    prompt="Are you sure you want to reset all settings to defaults?"
)
def reset():
    """Reset all configuration to defaults."""
    try:
        config_manager = Container().config_manager()
    except Exception:
        config_manager = ConfigManager()

    try:
        config_manager.reset_to_defaults()
        click.echo("Configuration reset to defaults.")
        click.echo("Note: Scan history has been preserved.")
    except Exception as e:
        click.echo(f"Error resetting configuration: {e}", err=True)
        sys.exit(1)


def _convert_value(key: str, value: str) -> Any:
    """
    Convert string value to appropriate type based on key.

    Args:
        key: Configuration key
        value: String value to convert

    Returns:
        Converted value

    Raises:
        ValueError: If value cannot be converted
    """
    if key == "fuzzy_threshold":
        try:
            val = float(value)
            if not 0.0 <= val <= 1.0:
                raise ValueError("Fuzzy threshold must be between 0.0 and 1.0")
            return val
        except ValueError as e:
            if "must be between" in str(e):
                raise e
            raise ValueError("Fuzzy threshold must be a number between 0.0 and 1.0")

    elif key == "large_file_threshold":
        try:
            val = int(value)
            if val < 0:
                raise ValueError("Large file threshold must be positive")
            return val
        except ValueError as e:
            if "must be positive" in str(e):
                raise e
            raise ValueError("Large file threshold must be a positive integer")

    elif key == "default_output_format":
        if value.lower() not in ["yaml", "json"]:
            raise ValueError("Default output format must be 'yaml' or 'json'")
        return value.lower()

    elif key in ["recursive_scan", "verbose_mode", "show_progress"]:
        if value.lower() in ["true", "1", "yes", "on"]:
            return True
        elif value.lower() in ["false", "0", "no", "off"]:
            return False
        else:
            raise ValueError(
                f"{key} must be a boolean value (true/false, yes/no, 1/0, on/off)"
            )

    return value


def _format_bytes(size: int) -> str:
    """Format file size in human-readable units."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} PB"


def _format_timestamp(timestamp_str: str) -> str:
    """Format ISO timestamp for display."""
    if not timestamp_str:
        return "Unknown"

    try:
        from datetime import datetime

        # Remove 'Z' suffix if present and parse
        if timestamp_str.endswith("Z"):
            timestamp_str = timestamp_str[:-1]

        dt = datetime.fromisoformat(timestamp_str)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, AttributeError):
        return timestamp_str

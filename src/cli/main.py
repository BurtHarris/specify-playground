#!/usr/bin/env python3
"""
Main CLI entry point for Video Duplicate Scanner.

This module provides the command-line interface using Click framework
with Python version validation and comprehensive error handling for universal file duplicate detection.
"""

import sys
import os
from pathlib import Path
from typing import Optional

import click


# Default click.Group is sufficient; implicit directory invocation is
# handled inside the main() function by inspecting ctx.args when no
# subcommand is invoked. Custom group logic caused Click dispatch
# inconsistencies during tests and is unnecessary.


class CommandFirstGroup(click.Group):
    """A Click Group that prefers known subcommand names over consuming
    a top-level positional argument. If the first argument matches a
    registered subcommand, resolve it as a command so subcommands like
    'config' are not accidentally parsed as the DIRECTORY argument.
    """
    def resolve_command(self, ctx, args):
        if args:
            potential = args[0]
            # Ensure a string form for membership checks since Click may
            # coerce positional args to Path objects when path_type=Path.
            try:
                potential_str = potential if isinstance(potential, str) else str(potential)
            except Exception:
                potential_str = str(potential)

            # If the first token is a registered subcommand, dispatch to it.
            if os.environ.get('SPECIFY_DEBUG_ARGV') == '1':
                try:
                    print(f"[CommandFirstGroup] args={args}, potential={potential!r}, commands={list(self.commands.keys())}")
                except Exception:
                    pass
            if potential_str in self.commands:
                if os.environ.get('SPECIFY_DEBUG_ARGV') == '1':
                    print(f"[CommandFirstGroup] resolving to subcommand {potential_str}")
                return potential_str, self.commands[potential_str], args[1:]

            # If the first token looks like an existing directory and a
            # 'scan' subcommand exists, treat this as implicit 'scan' so
            # programmatic invocations (CliRunner) work without the shim.
            try:
                if 'scan' in self.commands and not potential_str.startswith('-'):
                    from pathlib import Path as _Path
                    p = _Path(potential)
                    if p.exists() and p.is_dir():
                        return 'scan', self.commands['scan'], args
            except Exception:
                # Fall through to default resolution on any error
                pass
            # If the first token is an option (starts with '-') and a 'scan'
            # subcommand exists, treat the invocation as targeting 'scan'
            # so that options like --progress and --export are parsed by the
            # scan subcommand instead of being treated as unknown commands.
            try:
                if potential_str.startswith('-') and 'scan' in self.commands:
                    if os.environ.get('SPECIFY_DEBUG_ARGV') == '1':
                        print(f"[CommandFirstGroup] treating leading option {potential_str} as scan subcommand")
                    return 'scan', self.commands['scan'], args
            except Exception:
                pass
        return super().resolve_command(ctx, args)

# Python version check BEFORE any other imports
def check_python_version():
    """Check Python version requirement (3.12+) before proceeding."""
    if sys.version_info < (3, 12):
        click.echo(f"Error: Python 3.12 or higher is required.", err=True)
        click.echo(f"Current version: Python {sys.version.split()[0]}", err=True)
        click.echo("Please upgrade Python to continue.", err=True)
        sys.exit(3)

# Perform version check first
check_python_version()

# Now safe to import our modules
from ..services.file_scanner import FileScanner, DirectoryNotFoundError
from ..services.duplicate_detector import DuplicateDetector
from ..services.progress_reporter import ProgressReporter
from ..services.result_exporter import ResultExporter, DiskSpaceError
from ..models.scan_result import ScanResult
from ..models.scan_metadata import ScanMetadata
from ..lib.config_manager import ConfigManager
from .config_commands import config


# Version constant
__version__ = "1.0.0"


def format_size(bytes_size: int) -> str:
    """Format file size in human-readable units."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024
    return f"{bytes_size:.1f} PB"


@click.group(cls=CommandFirstGroup, invoke_without_command=True, context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
@click.pass_context
@click.version_option(version=__version__, prog_name='Video Duplicate Scanner')
def main(ctx: click.Context):
    """
    Video Duplicate Scanner CLI

    Scans directories for duplicate files of any type using size comparison
    followed by hash computation for performance optimization.

    Supports all file types with configurable filtering.

    Use 'file-dedup scan DIRECTORY' to scan a directory.
    Use 'file-dedup config' commands to manage configuration.
    
        Scan options (also available when invoking `python -m src --help`):
            --recursive / --no-recursive    Scan subdirectories recursively
            --export PATH                    Export results to YAML file at PATH
            --threshold FLOAT                Fuzzy matching threshold (0.0-1.0)
            --verbose / --quiet              Verbose output with detailed progress
            --progress / --no-progress      Show progress bar
            --color / --no-color            Colorized output
    """
    # If invoked without a subcommand, show help. When help was explicitly
    # requested at the top level (e.g. `python -m src --help`), also include
    # the `scan` subcommand help so options like --recursive and --export are
    # visible to users and integration tests that expect them in top-level
    # help output.
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help(), color=ctx.color)
        # If user asked for help (top-level --help/-h) then append scan help
        # so scan-specific options are visible in the module-level help.
        argv = list(ctx.args) if ctx.args is not None else []
        # Also consider raw sys.argv presence of -h/--help
        import sys as _sys
        raw_help = any(a in (_sys.argv[1:] if len(_sys.argv) > 1 else []) for a in ('--help', '-h'))
        if ('--help' in argv or '-h' in argv) or raw_help:
            try:
                if 'scan' in getattr(main, 'commands', {}):
                    scan_cmd = main.commands['scan']
                    try:
                        # Use the command's get_help API to render help text with
                        # the current top-level context as parent so option
                        # formatting and help text include parameter descriptions.
                        scan_ctx = click.Context(scan_cmd, info_name='scan', parent=ctx)
                        help_text = scan_cmd.get_help(scan_ctx)
                        click.echo('\n' + help_text, color=ctx.color)
                    except Exception:
                        # Fallback: attempt to build a simple header
                        click.echo('\nScan command help:\n  run `python -m src scan --help` for details', color=ctx.color)
            except Exception:
                # If anything goes wrong retrieving subcommand help, ignore
                # and exit after printing group help.
                pass
        ctx.exit()


@main.command()
@click.argument('directory', type=click.Path(exists=True, file_okay=False, dir_okay=True, readable=True, path_type=Path))
@click.option('--db-path', type=click.Path(dir_okay=False, writable=False, path_type=Path), default=None,
              help='Path to SQLite DB for caching hashes (default: in-memory)')
@click.option('--patterns', type=str, default=None,
              help='Comma-separated glob patterns to include (e.g. "*.txt,*.jpg")')
@click.option('--recursive/--no-recursive', default=None, help='Scan subdirectories recursively (default: from config)')
@click.option('--export', type=click.Path(dir_okay=False, writable=True, path_type=Path), help='Export results to YAML file at specified path')
@click.option('--threshold', type=float, default=None, help='Fuzzy matching threshold (0.0-1.0) (default: from config)')
@click.option('--verbose/--quiet', default=None, help='Verbose output with detailed progress (default: from config)')
@click.option('--progress/--no-progress', default=None, help='Show progress bar (default: from config or auto-detect TTY)')
@click.option('--color/--no-color', default=None, help='Colorized output (default: auto-detect)')
def scan(directory: Path, db_path: Optional[Path], patterns: Optional[str], recursive: Optional[bool], export: Optional[Path], 
    threshold: Optional[float], verbose: Optional[bool], progress: Optional[bool], color: Optional[bool]):
    """Scan DIRECTORY for duplicate files of any type."""
    # Load configuration for defaults
    config_manager = ConfigManager()
    try:
        config_settings = config_manager.load_config()
    except Exception as e:
        click.echo(f"Warning: Could not load configuration: {e}", err=True)
        click.echo("Using built-in defaults.", err=True)
        config_settings = ConfigManager.DEFAULT_CONFIG.copy()
    
    # Use config defaults where CLI options weren't specified
    if recursive is None:
        recursive = config_settings.get('recursive_scan', True)
    if threshold is None:
        threshold = config_settings.get('fuzzy_threshold', 0.8)
    if verbose is None:
        verbose = config_settings.get('verbose_mode', False)
    if progress is None and config_settings.get('show_progress') is not None:
        progress = config_settings.get('show_progress')
    
    # Normalize patterns argument
    if patterns:
        pattern_list = [p.strip() for p in patterns.split(',') if p.strip()]
    else:
        pattern_list = None

    # Run the scan
    _run_scan(directory, db_path, pattern_list, recursive, export, threshold, verbose, progress, color, config_manager)


def _run_scan(directory: Path, db_path: Optional[Path], patterns: Optional[list], recursive: bool, export: Optional[Path], 
              threshold: float, verbose: bool, progress: Optional[bool], color: Optional[bool],
              config_manager: ConfigManager) -> None:
    """Execute the universal file duplicate scan."""
    try:
        # Validate threshold range
        if not 0.0 <= threshold <= 1.0:
            click.echo("Error: Threshold must be between 0.0 and 1.0", err=True)
            sys.exit(1)

        # Set up progress reporting
        if progress is None:
            # Auto-detect: progress only when TTY and not in quiet mode
            show_progress = sys.stdout.isatty() and verbose
        else:
            # User explicitly requested progress on/off
            show_progress = progress

        # Initialize services
        progress_reporter = ProgressReporter(enabled=show_progress)
        scanner = FileScanner(db_path=db_path, patterns=patterns, recursive=recursive)
        detector = DuplicateDetector()
        exporter = ResultExporter()

        # Start scan
        if verbose:
            click.echo(f"Universal File Duplicate Scanner v{__version__}")
            click.echo(f"Scanning: {directory} ({'recursive' if recursive else 'non-recursive'})")
            click.echo()

        # Perform directory scan
        scan_result = _perform_scan(
            scanner=scanner,
            detector=detector,
            reporter=progress_reporter,
            directory=directory,
            recursive=recursive,
            threshold=threshold,
            verbose=verbose,
        )

        # Output results (quiet mode shows basic results, verbose shows detailed)
        _display_text_results(scan_result, verbose, color, directory)

        # Export if requested
        if export:
            try:
                # Always export as YAML
                exporter.export_yaml(scan_result, export)

                if verbose:
                    click.echo(f"\nResults exported to: {export}")
            except DiskSpaceError as e:
                click.echo(f"Error: {e}", err=True)
                sys.exit(4)
            except PermissionError as e:
                click.echo(f"Error: Cannot write to {export}: Permission denied", err=True)
                sys.exit(2)

        # Update scan history before completing
        try:
            duplicates_found = len(scan_result.duplicate_groups)
            file_count = scan_result.metadata.total_files_found
            config_manager.add_scan_history(directory, file_count, duplicates_found)
        except Exception as e:
            if verbose:
                click.echo(f"Warning: Could not update scan history: {e}", err=True)

        # Exit with appropriate code
        if scan_result.metadata.errors:
            # Had errors but completed - show error summary
            click.echo(f"Warning: {len(scan_result.metadata.errors)} errors occurred during scanning:", err=True)
            if verbose:
                for error in scan_result.metadata.errors[:5]:  # Show first 5 errors
                    click.echo(f"  Error: {error.get('error', 'Unknown error')}", err=True)
                if len(scan_result.metadata.errors) > 5:
                    click.echo(f"  ... and {len(scan_result.metadata.errors) - 5} more errors", err=True)
            else:
                click.echo(f"  Use --verbose to see error details", err=True)
            sys.exit(0)
        else:
            # Clean success
            sys.exit(0)

    except DirectoryNotFoundError as e:
        click.echo(f"Error: Directory '{directory}' does not exist or is not accessible.", err=True)
        click.echo("Use --help for usage information.", err=True)
        sys.exit(1)
    except PermissionError as e:
        click.echo(f"Error: Permission denied accessing directory '{directory}'", err=True)
        sys.exit(2)
    except KeyboardInterrupt:
        click.echo("\nScan interrupted by user.", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def _perform_scan(scanner: FileScanner, detector: DuplicateDetector, 
                 reporter: ProgressReporter, directory: Path, recursive: bool,
                 threshold: float, verbose: bool) -> ScanResult:
    """
    Perform the actual scan operation with progress reporting.
    
    Args:
    scanner: FileScanner instance
        detector: DuplicateDetector instance  
        reporter: ProgressReporter instance
        directory: Directory to scan
        recursive: Whether to scan recursively
        threshold: Fuzzy matching threshold
        verbose: Whether to show verbose output
        
    Returns:
        ScanResult with complete scan data
    """
    from datetime import datetime
    import time
    
    # Initialize metadata
    metadata = ScanMetadata(scan_paths=[directory], recursive=recursive)
    metadata.start_time = datetime.now()
    scan_start = time.time()
    
    # Scan for files
    if verbose:
        click.echo(f"Scanning directory: {directory}")
    
    files = list(scanner.scan_directory(directory, recursive=recursive, metadata=metadata, progress_reporter=reporter))
    metadata.total_files_found = len(files)
    
    if not files:
        if verbose:
            click.echo("No files found.")
        
        # Complete metadata for empty scan
        metadata.end_time = datetime.now()
        metadata.total_files_processed = 0
        
        # Return empty result
        result = ScanResult(metadata=metadata)
        return result
    
    if verbose:
        click.echo(f"Found {len(files)} files")
    
    # Calculate total size
    total_size = sum(f.size for f in files)
    metadata.total_size_scanned = total_size
    
    # Start progress for duplicate detection
    reporter.start_progress(len(files), "Detecting duplicates")
    
    try:
        # Find duplicates
        if verbose:
            click.echo("Detecting duplicates...")
        
        duplicate_groups = detector.find_duplicates(files, reporter, verbose, metadata=metadata)
        
        # Update progress
        reporter.update_progress(len(files), "Finding potential matches")
        
        # Find potential matches
        if verbose:
            click.echo(f"Finding potential matches (threshold: {threshold})...")
        
        potential_matches = detector.find_potential_matches(files, threshold=threshold, verbose=verbose)
        
    finally:
        reporter.finish_progress()
    
    # Complete metadata
    metadata.end_time = datetime.now()
    metadata.total_files_processed = len(files)
    
    # Calculate duplicate statistics
    total_duplicate_files = sum(len(group.files) for group in duplicate_groups)
    total_duplicate_size = sum(group.total_size for group in duplicate_groups)
    total_wasted_space = sum(group.wasted_space for group in duplicate_groups)
    
    metadata.total_size_duplicates = total_duplicate_size
    metadata.total_size_wasted = total_wasted_space
    
    # Create scan result
    result = ScanResult(metadata=metadata)
    result.duplicate_groups = duplicate_groups
    result.potential_match_groups = potential_matches
    
    return result


def _display_text_results(scan_result: ScanResult, verbose: bool, color: bool, scan_directory: Path) -> None:
    """Display scan results in human-readable text format."""
    metadata = scan_result.metadata
    
    # Auto-detect color if not specified
    if color is None:
        color = sys.stdout.isatty()
    
    # Color functions
    def header(text: str) -> str:
        return click.style(text, fg='cyan', bold=True) if color else text
    
    def success(text: str) -> str:
        return click.style(text, fg='green') if color else text
    
    def warning(text: str) -> str:
        return click.style(text, fg='yellow') if color else text
    
    def error(text: str) -> str:
        return click.style(text, fg='red') if color else text
    
    def info(text: str) -> str:
        return click.style(text, fg='blue') if color else text
    
    def get_relative_path(file_path: Path) -> str:
        """Get path relative to scan directory, fallback to absolute if not possible."""
        try:
            return str(file_path.relative_to(scan_directory))
        except ValueError:
            # File is not under scan directory, return absolute path
            return str(file_path)
    
    # Summary header
    if verbose:
        click.echo(f"\n{header('=== Scan Results ===')}")
        click.echo(f"Scanned: {info(', '.join(str(p) for p in metadata.scan_paths))}")
        click.echo(f"Files found: {info(str(metadata.total_files_found))}")
        
        if metadata.end_time and metadata.start_time:
            duration = (metadata.end_time - metadata.start_time).total_seconds()
            click.echo(f"Scan duration: {info(f'{duration:.2f} seconds')}")
        
        click.echo(f"Total size: {info(format_size(metadata.total_size_scanned))}")
        
        # Duplicate groups (verbose mode)
        if scan_result.duplicate_groups:
            click.echo(f"\n{header(f'=== Duplicate Groups ({len(scan_result.duplicate_groups)}) ===')}")
            
            total_wasted = sum(group.wasted_space for group in scan_result.duplicate_groups)
            click.echo(f"Total wasted space: {warning(format_size(total_wasted))}")
            
            for i, group in enumerate(scan_result.duplicate_groups, 1):
                click.echo(f"\n{warning(f'Group {i}')}: {len(group.files)} files")
                click.echo(f"  Size: {format_size(group.file_size)} each")
                click.echo(f"  Wasted: {warning(format_size(group.wasted_space))}")
                
                for file in group.files:
                    click.echo(f"    {get_relative_path(file.path)}")
        else:
            click.echo(f"\n{success('No duplicate groups found.')}")
        
        # Potential matches (verbose mode)
        if scan_result.potential_match_groups:
            click.echo(f"\n{header(f'=== Potential Matches ({len(scan_result.potential_match_groups)}) ===')}")
            
            for i, group in enumerate(scan_result.potential_match_groups, 1):
                click.echo(f"\n{info(f'Group {i}')}: {len(group.files)} files (similarity: {group.average_similarity:.2f})")
                
                for file in group.files:
                    click.echo(f"    {get_relative_path(file.path)} ({format_size(file.size)})")
        else:
            click.echo(f"\n{success('No potential matches found.')}")
    else:
        # Quiet mode - minimal output
        click.echo(f"Scanned: {', '.join(str(p) for p in metadata.scan_paths)}")
        click.echo(f"Files found: {metadata.total_files_found}")
        
        # Just show count of duplicates/matches in quiet mode
        if scan_result.duplicate_groups:
            click.echo(f"Duplicate groups found: {len(scan_result.duplicate_groups)}")
        else:
            click.echo("No duplicate groups found.")
            
        if scan_result.potential_match_groups:
            click.echo(f"Potential matches found: {len(scan_result.potential_match_groups)}")
        else:
            click.echo("No potential matches found.")


def format_size(bytes_size: int) -> str:
    """Format file size in human-readable units."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024
    return f"{bytes_size:.1f} PB"


# Add config command group
main.add_command(config)


if __name__ == '__main__':
    main()


# Alias for testing and external imports
cli = main
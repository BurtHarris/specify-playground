#!/usr/bin/env python3
"""
Main CLI entry point for Video Duplicate Scanner.

This module provides the command-line interface using Click framework
with Python version validation and comprehensive error handling.
"""

import sys
import os
from pathlib import Path
from typing import Optional

import click

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
from ..services.video_file_scanner import VideoFileScanner, DirectoryNotFoundError
from ..services.duplicate_detector import DuplicateDetector
from ..services.progress_reporter import ProgressReporter
from ..services.result_exporter import ResultExporter, DiskSpaceError
from ..models.scan_result import ScanResult
from ..models.scan_metadata import ScanMetadata


# Version constant
__version__ = "1.0.0"


@click.command()
@click.argument('directory', type=click.Path(exists=True, file_okay=False, dir_okay=True, readable=True, path_type=Path))
@click.option('--recursive/--no-recursive', default=True, help='Scan subdirectories recursively (default: True)')
@click.option('--output', type=click.Choice(['json', 'text']), default='text', help='Output format (default: text)')
@click.option('--export', type=click.Path(dir_okay=False, writable=True, path_type=Path), help='Export results to JSON file at specified path')
@click.option('--threshold', type=float, default=0.8, help='Fuzzy matching threshold (0.0-1.0) (default: 0.8)')
@click.option('--verbose/--quiet', default=False, help='Verbose output with detailed progress')
@click.option('--progress/--no-progress', default=None, help='Show progress bar (default: auto-detect TTY)')
@click.option('--color/--no-color', default=None, help='Colorized output (default: auto-detect)')
@click.version_option(version=__version__, prog_name='video-dedup')
def main(directory: Path, recursive: bool, output: str, export: Optional[Path], 
         threshold: float, verbose: bool, progress: Optional[bool], color: Optional[bool]):
    """
    Video Duplicate Scanner CLI
    
    Scans DIRECTORY for duplicate video files using size comparison
    followed by hash computation for performance optimization.
    
    Supports .mp4, .mkv, and .mov video formats.
    """
    try:
        # Validate threshold range
        if not 0.0 <= threshold <= 1.0:
            click.echo("Error: Threshold must be between 0.0 and 1.0", err=True)
            sys.exit(1)
        
        # Set up progress reporting
        if progress is None:
            # Auto-detect TTY unless explicitly disabled
            show_progress = sys.stdout.isatty() and not verbose
        else:
            show_progress = progress
        
        # Initialize services
        progress_reporter = ProgressReporter(enabled=show_progress)
        scanner = VideoFileScanner()
        detector = DuplicateDetector()
        exporter = ResultExporter()
        
        # Start scan
        if verbose:
            click.echo(f"Video Duplicate Scanner v{__version__}")
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
            verbose=verbose
        )
        
        # Output results
        if output == 'text':
            _display_text_results(scan_result, verbose, color)
        elif output == 'json':
            _display_json_results(scan_result)
        
        # Export if requested
        if export:
            try:
                if export.suffix.lower() == '.json':
                    exporter.export_json(scan_result, export)
                elif export.suffix.lower() in ['.yaml', '.yml']:
                    exporter.export_yaml(scan_result, export)
                else:
                    # Default to JSON if no extension or unknown extension
                    exporter.export_json(scan_result, export)
                
                if verbose:
                    click.echo(f"\nResults exported to: {export}")
            except DiskSpaceError as e:
                click.echo(f"Error: {e}", err=True)
                sys.exit(4)
            except PermissionError as e:
                click.echo(f"Error: Cannot write to {export}: Permission denied", err=True)
                sys.exit(2)
        
        # Exit with appropriate code
        if scan_result.metadata.errors:
            # Had errors but completed
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
        click.echo("\\nScan interrupted by user.", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def _perform_scan(scanner: VideoFileScanner, detector: DuplicateDetector, 
                 reporter: ProgressReporter, directory: Path, recursive: bool,
                 threshold: float, verbose: bool) -> ScanResult:
    """
    Perform the actual scan operation with progress reporting.
    
    Args:
        scanner: VideoFileScanner instance
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
    
    # Scan for video files
    if verbose:
        click.echo(f"Scanning directory: {directory}")
    
    video_files = list(scanner.scan_directory(directory, recursive=recursive))
    metadata.total_files_found = len(video_files)
    
    if not video_files:
        if verbose:
            click.echo("No video files found.")
        
        # Complete metadata for empty scan
        metadata.end_time = datetime.now()
        metadata.total_files_processed = 0
        
        # Return empty result
        result = ScanResult(metadata=metadata)
        return result
    
    if verbose:
        click.echo(f"Found {len(video_files)} video files")
    
    # Calculate total size
    total_size = sum(f.size for f in video_files)
    metadata.total_size_scanned = total_size
    
    # Start progress for duplicate detection
    reporter.start_progress(len(video_files), "Detecting duplicates")
    
    try:
        # Find duplicates
        if verbose:
            click.echo("Detecting duplicates...")
        
        duplicate_groups = detector.find_duplicates(video_files)
        
        # Update progress
        reporter.update_progress(len(video_files), "Finding potential matches")
        
        # Find potential matches
        if verbose:
            click.echo(f"Finding potential matches (threshold: {threshold})...")
        
        potential_matches = detector.find_potential_matches(video_files, threshold=threshold)
        
    finally:
        reporter.finish_progress()
    
    # Complete metadata
    metadata.end_time = datetime.now()
    metadata.total_files_processed = len(video_files)
    
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


def _display_text_results(scan_result: ScanResult, verbose: bool, color: bool) -> None:
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
    
    # Summary header
    click.echo(f"\n{header('=== Scan Results ===')}")
    click.echo(f"Scanned: {info(', '.join(str(p) for p in metadata.scan_paths))}")
    click.echo(f"Files found: {info(str(metadata.total_files_found))}")
    
    if metadata.end_time and metadata.start_time:
        duration = (metadata.end_time - metadata.start_time).total_seconds()
        click.echo(f"Scan duration: {info(f'{duration:.2f} seconds')}")
    
    # Format file sizes
    def format_size(bytes_size: int) -> str:
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_size < 1024:
                return f"{bytes_size:.1f} {unit}"
            bytes_size /= 1024
        return f"{bytes_size:.1f} PB"
    
    click.echo(f"Total size: {info(format_size(metadata.total_size_scanned))}")
    
    # Duplicate groups
    if scan_result.duplicate_groups:
        click.echo(f"\n{header(f'=== Duplicate Groups ({len(scan_result.duplicate_groups)}) ===')}")
        
        total_wasted = sum(group.wasted_space for group in scan_result.duplicate_groups)
        click.echo(f"Total wasted space: {warning(format_size(total_wasted))}")
        
        for i, group in enumerate(scan_result.duplicate_groups, 1):
            click.echo(f"\n{warning(f'Group {i}')}: {len(group.files)} files")
            click.echo(f"  Size: {format_size(group.total_size)} each")
            click.echo(f"  Wasted: {warning(format_size(group.wasted_space))}")
            
            for file in group.files:
                click.echo(f"    {file.path}")
    else:
        click.echo(f"\n{success('No duplicate groups found.')}")
    
    # Potential matches
    if scan_result.potential_match_groups:
        click.echo(f"\n{header(f'=== Potential Matches ({len(scan_result.potential_match_groups)}) ===')}")
        
        for i, group in enumerate(scan_result.potential_match_groups, 1):
            click.echo(f"\n{info(f'Group {i}')}: {len(group.files)} files (similarity: {group.similarity_score:.2f})")
            
            for file in group.files:
                click.echo(f"    {file.path} ({format_size(file.size)})")
    else:
        click.echo(f"\n{success('No potential matches found.')}")


def _display_json_results(scan_result: ScanResult) -> None:
    """Display scan results in JSON format."""
    import json
    exporter = ResultExporter()
    data = exporter._prepare_export_data(scan_result)
    click.echo(json.dumps(data, indent=2))


if __name__ == '__main__':
    main()
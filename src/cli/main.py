#!/usr/bin/env python3
"""
Main CLI entry point for Video Duplicate Scanner.

This module provides the command-line interface using Click framework
with Python version validation and comprehensive error handling for universal file duplicate detection.
"""

import sys
import os
import logging
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
                potential_str = (
                    potential if isinstance(potential, str) else str(potential)
                )
            except Exception:
                potential_str = str(potential)

            # If the first token is a registered subcommand, dispatch to it.
            if os.environ.get("SPECIFY_DEBUG_ARGV") == "1":
                try:
                    print(
                        f"[CommandFirstGroup] args={args}, potential={potential!r}, commands={list(self.commands.keys())}"
                    )
                except Exception:
                    pass
            if potential_str in self.commands:
                if os.environ.get("SPECIFY_DEBUG_ARGV") == "1":
                    print(
                        f"[CommandFirstGroup] resolving to subcommand {potential_str}"
                    )
                return potential_str, self.commands[potential_str], args[1:]

            # If the first token looks like an existing directory and a
            # 'scan' subcommand exists, treat this as implicit 'scan' so
            # programmatic invocations (CliRunner) work without the shim.
            try:
                if "scan" in self.commands and not potential_str.startswith("-"):
                    from pathlib import Path as _Path

                    p = _Path(potential)
                    if p.exists() and p.is_dir():
                        return "scan", self.commands["scan"], args
            except Exception:
                # Fall through to default resolution on any error
                pass
            # If the first token is an option (starts with '-') and a 'scan'
            # subcommand exists, treat the invocation as targeting 'scan'
            # so that options like --progress and --export are parsed by the
            # scan subcommand instead of being treated as unknown commands.
            try:
                if potential_str.startswith("-") and "scan" in self.commands:
                    if os.environ.get("SPECIFY_DEBUG_ARGV") == "1":
                        print(
                            f"[CommandFirstGroup] treating leading option {potential_str} as scan subcommand"
                        )
                    return "scan", self.commands["scan"], args
            except Exception:
                pass
        return super().resolve_command(ctx, args)


# Python version check BEFORE any other imports
def check_python_version():
    """Check Python version requirement (3.12+) before proceeding."""
    if sys.version_info < (3, 12):
        click.echo("Error: Python 3.12 or higher is required.", err=True)
        click.echo(f"Current version: Python {sys.version.split()[0]}", err=True)
        click.echo("Please upgrade Python to continue.", err=True)
        sys.exit(3)


# Perform version check first
check_python_version()


def enforce_utf8_stdio() -> None:
    """Ensure stdout/stderr use UTF-8 and set PYTHONIOENCODING for child processes.

    This is a best-effort, defensive change to avoid UnicodeEncodeError when
    printing emoji or other non-encodable characters on Windows consoles.
    If reconfigure is available on the stream, prefer it; otherwise set the
    environment variable so child processes inherit UTF-8 behaviour.
    """
    try:
        for _name in ("stdout", "stderr"):
            _stream = getattr(sys, _name, None)
            if _stream is None:
                continue
            try:
                # Python 3.7+ exposes reconfigure on TextIOBase wrappers
                if hasattr(_stream, "reconfigure"):
                    _stream.reconfigure(encoding="utf-8", errors="backslashreplace", newline="\n")
            except Exception:
                # Best-effort only; do not raise during CLI startup
                # If the stream cannot be reconfigured, continue silently; the
                # reconfigure step is a convenience and errors here should not
                # block CLI startup.
                pass
    except Exception:
        # Never let encoding helpers break CLI startup
        pass


# Enforce UTF-8 on stdio as early as possible so diagnostic printing cannot
# abort long-running scans due to platform console encodings (e.g., cp1252).


# Now safe to import our modules
from ..services.file_scanner import FileScanner, DirectoryNotFoundError
from ..services.duplicate_detector import DuplicateDetector
from ..services.progress_reporter import ProgressReporter
from ..services.result_exporter import ResultExporter, DiskSpaceError
from ..models.scan_result import ScanResult
from ..models.scan_metadata import ScanMetadata
from ..lib.config_manager import ConfigManager
from .config_commands import config
from .db_commands import db as db_commands
from ..lib.container import Container


# Version constant
__version__ = "1.0.0"


def format_size(bytes_size: int) -> str:
    """Format file size in human-readable units."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes_size < 1024:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024
    return f"{bytes_size:.1f} PB"


def _reconfigure_logger_for_stdout(logger: logging.Logger) -> None:
    """Ensure INFO/DEBUG messages are written to stdout rather than stderr.

    Removes any StreamHandler targeting stderr and adds a stdout StreamHandler
    if none is present. This is a best-effort operation and does not raise
    on failure.
    """
    try:
        for h in list(logger.handlers):
            try:
                if isinstance(h, logging.StreamHandler) and getattr(h, "stream", None) is sys.stderr:
                    logger.removeHandler(h)
            except Exception:
                pass

        # If Rich is available, prefer RichHandler so logs and progress
        # bars share the same Console and render cleanly together.
        try:
            from rich.logging import RichHandler
            from rich.console import Console

            console = Console()
            rich_handler = RichHandler(console=console, rich_tracebacks=True)
            # Remove existing stream handlers that write to stderr
            for h in list(logger.handlers):
                try:
                    if isinstance(h, logging.StreamHandler) and getattr(h, "stream", None) is sys.stderr:
                        logger.removeHandler(h)
                except Exception:
                    pass
            # Add RichHandler if not already present
            has_rich = any(h.__class__.__name__ == "RichHandler" for h in logger.handlers)
            if not has_rich:
                logger.addHandler(rich_handler)
            # Ensure a StreamHandler targeting sys.stdout exists so tests that
            # capture stdout see log messages there; RichHandler may render to
            # its own console but some test environments assert presence of a
            # stdout StreamHandler specifically.
            has_stdout = any(
                isinstance(h, logging.StreamHandler) and getattr(h, "stream", None) is sys.stdout
                for h in logger.handlers
            )
            if not has_stdout:
                sh = logging.StreamHandler(stream=sys.stdout)
                sh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s"))
                logger.addHandler(sh)
        except Exception:
            # Fall back to a simple stdout StreamHandler if Rich isn't available
            has_stdout = any(
                isinstance(h, logging.StreamHandler) and getattr(h, "stream", None) is sys.stdout
                for h in logger.handlers
            )
            if not has_stdout:
                sh = logging.StreamHandler(stream=sys.stdout)
                sh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s"))
                logger.addHandler(sh)
    except Exception:
        # Never let logging reconfiguration break CLI startup
        pass


@click.group(cls=CommandFirstGroup)
@click.version_option(version=__version__)
def cli():
    """Specify CLI entrypoint."""


@cli.group()
def scan_group():
    """Scan for duplicate files in a directory."""


@scan_group.command()
@click.argument("directory", type=click.Path(exists=True, file_okay=False, path_type=str))
@click.option("--recursive/--no-recursive", default=True, help="Recurse into subdirectories")
@click.option("--patterns", default="*", help="File glob patterns to include, comma-separated")
@click.option("--db-path", default=None, help="Path to SQLite DB for caching hashes")
@click.option("--verbose", is_flag=True, default=False, help="Print per-file progress to stdout")
@click.option("--debug", is_flag=True, default=False, help="Enable DEBUG log level")
@click.option("--warning", is_flag=True, default=False, help="Enable WARNING log level (disables INFO output)")
@click.option("--export", default=None, help="Path to write scan results (YAML)")
def run(directory, recursive, patterns, db_path, verbose, debug, warning, export):
    """Run a scan of DIRECTORY for duplicates and potential matches."""
    # Build DI container with default providers
    try:
        container = Container()
    except Exception:
        container = None

    # Enforce at most one verbosity switch for this CLI invocation
    # (choose one of --verbose, --debug, or --warning). The logger level
    # is provided by the container configuration and internal code reads
    # the logger level rather than relying on CLI parameters.
    try:
        # Allow explicit debug+warning combination: prefer debug and emit a warning.
        if debug and warning:
            click.echo(
                "Warning: both --debug and --warning specified; using --debug (most verbose)",
                err=True,
            )
            # Prefer debug mode; disable warning mode
            warning = False
        elif sum(bool(x) for x in (verbose, debug, warning)) > 1:
            click.echo(
                "Error: At most one of --verbose, --debug, or --warning may be specified; choose one.",
                err=True,
            )
            sys.exit(2)
    except Exception:
        pass

    # Do not set logger level here; the container's logger configuration
    # defines the effective level. Internal code will read container.logger().level.
    try:
        _ = container.logger() if container is not None else None
    except Exception:
        pass

    # (Mutual-exclusivity is enforced at the higher-level `scan` entrypoint)

    # Route INFO/DEBUG output to stdout by default unless --warning was set.
    try:
        if container is not None:
            logger = container.logger()
            use_stdout = verbose or (not warning)
            if use_stdout:
                _reconfigure_logger_for_stdout(logger)
    except Exception:
        logger = None

    # Create scanner from container providers when available
    try:
        db_instance = container.database(db_path) if container is not None else None
    except Exception:
        db_instance = None

    try:
        hasher_fn = container.hasher() if container is not None else None
    except Exception:
        hasher_fn = None

    scanner = FileScanner(db=db_instance, patterns=patterns.split(","), recursive=recursive, hasher=hasher_fn, logger=(container.logger() if container else None))

    try:
        result: ScanResult = scanner.scan(Path(directory))
    except DirectoryNotFoundError as exc:
        click.echo(f"Directory not found: {exc}", err=True)
        sys.exit(2)
    except Exception as exc:
        click.echo(f"Scan failed: {exc}", err=True)
        sys.exit(4)

    # Export results when requested
    if export:
        try:
            exporter = ResultExporter()
            exporter.export(result, Path(export))
        except DiskSpaceError:
            click.echo("Disk space error while writing export", err=True)
            sys.exit(5)
        except Exception as exc:
            click.echo(f"Failed to export results: {exc}", err=True)
            sys.exit(6)

    # Print a short summary to stdout
    click.echo(f"Found {len(result.duplicate_groups)} duplicate groups and {len(result.potential_match_groups)} potential match groups")


cli.add_command(config)
cli.add_command(db_commands)


def main(argv: list | None = None) -> int:
    """CLI entry point for programmatic invocation. Returns exit code."""
    try:
        cli.main(args=argv, prog_name="specify", standalone_mode=False)
        return 0
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else 0
    except Exception as exc:
        click.echo(f"Unhandled error: {exc}", err=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

@click.group(
    cls=CommandFirstGroup,
    invoke_without_command=True,
    context_settings={
        "allow_extra_args": True,
        "ignore_unknown_options": True,
    },
)
@click.pass_context
@click.version_option(version=__version__, prog_name="Video Duplicate Scanner")
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
    # Ensure child processes inherit UTF-8 when the CLI starts. This is a
    # defensive measure for shells that don't default to UTF-8; it is set
    # here (rather than module import time) so tests can control environment
    # if needed and to avoid side-effects during import.
    try:
        os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    except Exception:
        # Non-fatal if environment cannot be mutated in restricted contexts
        pass

    # Require Rich for consistent console rendering. Fail early with a
    # clear error if Rich is not available to avoid silent degraded
    # behaviour across different environments.
    try:
        import rich  # type: ignore
    except Exception:
        click.echo("Error: 'rich' package is required for this CLI. Please install it (e.g. pip install rich).", err=True)
        ctx.exit(2)

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

        raw_help = any(
            a in (_sys.argv[1:] if len(_sys.argv) > 1 else []) for a in ("--help", "-h")
        )
        if ("--help" in argv or "-h" in argv) or raw_help:
            try:
                if "scan" in getattr(main, "commands", {}):
                    scan_cmd = main.commands["scan"]
                    try:
                        # Use the command's get_help API to render help text with
                        # the current top-level context as parent so option
                        # formatting and help text include parameter descriptions.
                        scan_ctx = click.Context(scan_cmd, info_name="scan", parent=ctx)
                        help_text = scan_cmd.get_help(scan_ctx)
                        click.echo("\n" + help_text, color=ctx.color)
                    except Exception:
                        # Fallback: attempt to build a simple header
                        click.echo(
                            "\nScan command help:\n  run `python -m src scan --help` for details",
                            color=ctx.color,
                        )
            except Exception:
                # If anything goes wrong retrieving subcommand help, ignore
                # and exit after printing group help.
                pass
        ctx.exit()


@main.command()
@click.argument(
    "directory",
    type=click.Path(
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        path_type=Path,
    ),
)
@click.option(
    "--db-path",
    type=click.Path(dir_okay=False, writable=False, path_type=Path),
    default=None,
    help="Path to SQLite DB for caching hashes (default: in-memory)",
)
@click.option(
    "--patterns",
    type=str,
    default=None,
    help='Comma-separated glob patterns to include (e.g. "*.txt,*.jpg")',
)
@click.option(
    "--recursive/--no-recursive",
    default=None,
    help="Scan subdirectories recursively (default: from config)",
)
@click.option(
    "--export",
    type=click.Path(dir_okay=False, writable=True, path_type=Path),
    help="Export results to YAML file at specified path",
)
@click.option(
    "--threshold",
    type=float,
    default=None,
    help="Fuzzy matching threshold (0.0-1.0) (default: from config)",
)
@click.option(
    "--verbose/--quiet",
    default=None,
    help="Verbose output with detailed progress (default: from config)",
)
@click.option(
    "--progress/--no-progress",
    default=None,
    help="Show progress bar (default: from config or auto-detect TTY)",
)
@click.option(
    "--color/--no-color",
    default=None,
    help="Colorized output (default: auto-detect)",
)
@click.option("--debug", default=None, is_flag=True, help="Enable DEBUG log level (overrides config)")
@click.option("--warning", default=None, is_flag=True, help="Enable WARNING log level (overrides config)")
def scan(
    directory: Path,
    db_path: Optional[Path],
    patterns: Optional[str],
    recursive: Optional[bool],
    export: Optional[Path],
    threshold: Optional[float],
    verbose: Optional[bool],
    progress: Optional[bool],
    color: Optional[bool],
    debug: Optional[bool],
    warning: Optional[bool],
):
    """Scan DIRECTORY for duplicate files of any type."""
    # Load configuration for defaults via IoC container when available so
    # tests can override and share a single instance. Fall back to direct
    # construction if the container is unavailable.
    try:
        container = Container()
        config_manager = container.config_manager()
    except Exception:
        config_manager = ConfigManager()

    try:
        config_settings = config_manager.load_config()
    except Exception as e:
        click.echo(f"Warning: Could not load configuration: {e}", err=True)
        click.echo("Using built-in defaults.", err=True)
        config_settings = ConfigManager.DEFAULT_CONFIG.copy()

    # Detect whether flags were explicitly provided by the caller.
    verbose_provided = verbose is not None
    debug_provided = debug is not None
    warning_provided = warning is not None
    # info flag removed; logger level comes from container configuration

    # Use config defaults where CLI options weren't specified
    if recursive is None:
        recursive = config_settings.get("recursive_scan", True)
    if threshold is None:
        threshold = config_settings.get("fuzzy_threshold", 0.8)
    if verbose is None:
        verbose = config_settings.get("verbose_mode", False)
    if progress is None and config_settings.get("show_progress") is not None:
        progress = config_settings.get("show_progress")

    # Normalize patterns argument
    if patterns:
        pattern_list = [p.strip() for p in patterns.split(",") if p.strip()]
    else:
        pattern_list = None

    # Run the scan
    # Allow the specific pair --debug + --warning by emitting a warning and
    # preferring DEBUG; only error when --verbose is combined with another
    # verbosity flag.
    # Enforce at most one level-switch across verbose/debug/warning
    try:
        # Allow explicit debug+warning only when both were explicitly requested and prefer debug
        if debug_provided and warning_provided and debug and warning:
            click.echo("Warning: both --debug and --warning specified; using --debug (most verbose)", err=True)
            debug = True
            warning = False
        elif sum(bool(x) for x in (verbose_provided and verbose, debug_provided and debug, warning_provided and warning)) > 1:
            click.echo(
                "Error: At most one of --verbose, --debug, or --warning may be specified; choose one.",
                err=True,
            )
            sys.exit(2)
    except Exception:
        pass

    if debug and not verbose:
        verbose = True

    _run_scan(
        directory,
        db_path,
        pattern_list,
        recursive,
        export,
        threshold,
        verbose,
        progress,
        color,
        config_manager,
        debug,
        warning,
    )


def _run_scan(
    directory: Path,
    db_path: Optional[Path],
    patterns: Optional[list],
    recursive: bool,
    export: Optional[Path],
    threshold: float,
    verbose: bool,
    progress: Optional[bool],
    color: Optional[bool],
    config_manager: ConfigManager,
    debug: Optional[bool] = None,
    warning: Optional[bool] = None,
) -> None:
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
        # Use dependency-injector container to create collaborators so they
        # can be swapped or configured centrally (IoC). The container is
        # lightweight and provides a ProgressReporter factory.
        container = Container()
        # (Mutual-exclusivity of --verbose/--debug is enforced at the
        # user-facing entrypoint; do not re-check here to avoid false
        # positives when debug implies verbose internally.)
        # Configure logger level from debug/warning flags: DEBUG, WARNING, else INFO
        try:
            # Determine logger level from the container logger instance so
            # internal functions do not rely on CLI flag parameters. This
            # keeps configuration centralized and easier to test.
            logger = container.logger()
            level = getattr(logger, 'level', None)
            # If the container logger has no explicit level, default to INFO
            if level is None:
                level = logging.INFO
        except Exception:
            logger = None
            level = logging.INFO
        progress_reporter = container.progress_reporter_factory(enabled=show_progress)
        # Build DB and hasher from the container when available so tests and
        # callers can provide alternate implementations. `database` provider
        # accepts a db_path and returns an instance; `hasher` is a callable.
        try:
            db_instance = (
                container.database(db_path)
                if db_path is not None
                else container.database()
            )
        except Exception:
            # Fall back to default behavior if container factory fails
            db_instance = None

        try:
            hasher_fn = container.hasher()
        except Exception:
            hasher_fn = None

        # Obtain the container-provided logger and, when verbose mode is
        # requested (or the user set log-level to INFO/DEBUG), ensure the
        # logger writes human-visible INFO/DEBUG messages to STDOUT so CLI
        # runs and tests that capture stdout see the per-file listings.
        try:
            logger = container.logger()
            # Route INFO/DEBUG to stdout (or Rich Console) unless logger level is WARNING or higher
            use_stdout = verbose or (level <= logging.INFO)

            if use_stdout:
                # Reconfigure logger to use Rich or stdout StreamHandler
                _reconfigure_logger_for_stdout(logger)
                # If Rich is available, try to provide the same Console to the
                # ProgressReporter so progress and logs share the render surface.
                try:
                    from rich.console import Console

                    # If the logger has a RichHandler, extract its console if possible
                    rich_console = None
                    for h in logger.handlers:
                        if h.__class__.__name__ == "RichHandler":
                            # RichHandler stores the console attribute
                            rich_console = getattr(h, "console", None)
                            break
                    # If we found a Rich console, pass it to the progress reporter
                    if rich_console is not None:
                        try:
                            progress_reporter = container.progress_reporter_factory(enabled=show_progress, console=rich_console)
                        except TypeError:
                            # ProgressReporter factory does not accept a console kwarg
                            progress_reporter = container.progress_reporter_factory(enabled=show_progress)
                    else:
                        progress_reporter = container.progress_reporter_factory(enabled=show_progress)
                except Exception:
                    progress_reporter = container.progress_reporter_factory(enabled=show_progress)
        except Exception:
            # Fall back to None if logger creation/reconfiguration fails
            logger = None

        scanner = FileScanner(
            db_path=db_path,
            patterns=patterns,
            recursive=recursive,
            db=db_instance,
            hasher=hasher_fn,
            logger=logger,
        )

    # Construct DuplicateDetector with injected ProgressReporter so the
    # detector can use a shared reporter instance without callers needing
    # to pass it on every call. Per-call reporter argument still takes precedence.
        detector = DuplicateDetector(progress_reporter=progress_reporter)
        exporter = ResultExporter()

        # Start scan
        if verbose:
            click.echo(f"Universal File Duplicate Scanner v{__version__}")
            click.echo(
                f"Scanning: {directory} ({'recursive' if recursive else 'non-recursive'})"
            )
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

    # Output results (quiet mode shows basic results, verbose shows group summaries,
    # debug shows per-file details and discovered-file samples)
        _display_text_results(scan_result, verbose, debug, color, directory)

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
                click.echo(
                    f"Error: Cannot write to {export}: Permission denied",
                    err=True,
                )
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
            click.echo(
                f"Warning: {len(scan_result.metadata.errors)} errors occurred during scanning:",
                err=True,
            )
            if verbose:
                for error in scan_result.metadata.errors[:5]:  # Show first 5 errors
                    click.echo(
                        f"  Error: {error.get('error', 'Unknown error')}",
                        err=True,
                    )
                if len(scan_result.metadata.errors) > 5:
                    click.echo(
                        f"  ... and {len(scan_result.metadata.errors) - 5} more errors",
                        err=True,
                    )
            else:
                click.echo("  Use --verbose to see error details", err=True)
            sys.exit(0)
        else:
            # Clean success
            sys.exit(0)

    except DirectoryNotFoundError as e:
        click.echo(
            f"Error: Directory '{directory}' does not exist or is not accessible.",
            err=True,
        )
        click.echo("Use --help for usage information.", err=True)
        sys.exit(1)
    except PermissionError as e:
        click.echo(
            f"Error: Permission denied accessing directory '{directory}'",
            err=True,
        )
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


def _perform_scan(
    scanner: FileScanner,
    detector: DuplicateDetector,
    reporter: ProgressReporter,
    directory: Path,
    recursive: bool,
    threshold: float,
    verbose: bool,
) -> ScanResult:
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

    files = list(
        scanner.scan_directory(
            directory,
            recursive=recursive,
            metadata=metadata,
            progress_reporter=reporter,
        )
    )
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

        duplicate_groups = detector.find_duplicates(
            files, reporter, verbose, metadata=metadata, db=scanner.db
        )

        # Update progress
        reporter.update_progress(len(files), "Finding potential matches")

        # Find potential matches
        if verbose:
            click.echo(f"Finding potential matches (threshold: {threshold})...")

        potential_matches = detector.find_potential_matches(
            files, threshold=threshold, verbose=verbose
        )

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


def _display_text_results(
    scan_result: ScanResult, verbose: bool, debug: bool, color: bool, scan_directory: Path
) -> None:
    """Display scan results in human-readable text format."""
    metadata = scan_result.metadata

    # Auto-detect color if not specified
    if color is None:
        color = sys.stdout.isatty()

    # Color functions
    def header(text: str) -> str:
        return click.style(text, fg="cyan", bold=True) if color else text

    def success(text: str) -> str:
        return click.style(text, fg="green") if color else text

    def warning(text: str) -> str:
        return click.style(text, fg="yellow") if color else text

    def error(text: str) -> str:
        return click.style(text, fg="red") if color else text

    def info(text: str) -> str:
        return click.style(text, fg="blue") if color else text

    def get_relative_path(file_path: Path) -> str:
        """Get path relative to scan directory, fallback to absolute if not possible."""
        try:
            return str(file_path.relative_to(scan_directory))
        except ValueError:
            # File is not under scan directory, return absolute path
            return str(file_path)

    # Summary header
    if verbose:
        # In verbose mode only print the scan header, totals, and duplicate group
        # summary. Potential matches and per-file listings remain debug-only to
        # avoid overwhelming output.
        click.echo(f"\n{header('=== Scan Results ===')}")
        click.echo(f"Scanned: {info(', '.join(str(p) for p in metadata.scan_paths))}")
        click.echo(f"Files found: {info(str(metadata.total_files_found))}")

        if metadata.end_time and metadata.start_time:
            duration = (metadata.end_time - metadata.start_time).total_seconds()
            click.echo(f"Scan duration: {info(f'{duration:.2f} seconds')}")

        click.echo(f"Total size: {info(format_size(metadata.total_size_scanned))}")

        # Duplicate groups (verbose mode) — always show group summaries here.
        if scan_result.duplicate_groups:
            click.echo(
                f"\n{header(f'=== Duplicate Groups ({len(scan_result.duplicate_groups)}) ===')}"
            )

            total_wasted = sum(group.wasted_space for group in scan_result.duplicate_groups)
            click.echo(f"Total wasted space: {warning(format_size(total_wasted))}")

            for i, group in enumerate(scan_result.duplicate_groups, 1):
                click.echo(f"\n{warning(f'Group {i}')}: {len(group.files)} files")
                click.echo(f"  Size: {format_size(group.file_size)} each")
                click.echo(f"  Wasted: {warning(format_size(group.wasted_space))}")

                # Only list individual files when debug mode is enabled.
                if debug:
                    for file in group.files:
                        click.echo(f"    {get_relative_path(file.path)}")
        else:
            click.echo(f"\n{success('No duplicate groups found.')}")

        # Potential matches are intentionally not shown in verbose mode; they
        # remain visible only when --debug is used.
        if debug:
            if scan_result.potential_match_groups:
                click.echo(
                    f"\n{header(f'=== Potential Matches ({len(scan_result.potential_match_groups)}) ===')}"
                )

                for i, group in enumerate(scan_result.potential_match_groups, 1):
                    click.echo(
                        f"\n{info(f'Group {i}')}: {len(group.files)} files (similarity: {group.average_similarity:.2f})"
                    )

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
            click.echo(
                f"Potential matches found: {len(scan_result.potential_match_groups)}"
            )
        else:
            click.echo("No potential matches found.")


# Add config command group
main.add_command(config)
# Add db maintenance commands
main.add_command(db_commands)


if __name__ == "__main__":
    main()


# Alias for testing and external imports
cli = main

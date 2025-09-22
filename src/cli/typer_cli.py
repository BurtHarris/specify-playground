"""Typer-based CLI adapter that delegates to the existing Click commands.

This module provides an alternate entrypoint using Typer while reusing
the existing scan implementation in `src.cli.main` to avoid duplicating
business logic.
"""
from pathlib import Path
from typing import Optional

import typer

from .main import _run_scan, Container, ConfigManager

_typer_app = typer.Typer(name="specify-typer")


@_typer_app.command()
def scan(
    directory: Path = typer.Argument(..., exists=True, file_okay=False, dir_okay=True),
    db_path: Optional[Path] = typer.Option(None, help="Path to SQLite DB for caching hashes"),
    patterns: Optional[str] = typer.Option(None, help='Comma-separated glob patterns to include (e.g. "*.txt,*.jpg")'),
    recursive: Optional[bool] = typer.Option(None, help="Scan subdirectories recursively (default from config)"),
    export: Optional[Path] = typer.Option(None, help="Export results to YAML file at specified path"),
    threshold: Optional[float] = typer.Option(None, help="Fuzzy matching threshold (0.0-1.0)"),
    verbose: Optional[bool] = typer.Option(None, help="Verbose output with detailed progress"),
    progress: Optional[bool] = typer.Option(None, help="Show progress bar (default: auto-detect TTY)"),
    color: Optional[bool] = typer.Option(None, help="Colorized output (default: auto-detect)"),
    debug: Optional[bool] = typer.Option(None, help="Enable DEBUG log level (overrides config)"),
    warning: Optional[bool] = typer.Option(None, help="Enable WARNING log level (overrides config)"),
):
    """Scan DIRECTORY for duplicate files using existing scan implementation."""
    # Use the same ConfigManager and Container semantics as the Click CLI
    try:
        container = Container()
        # Apply central logger level overrides based on CLI flags so all
        # container-provided collaborators share the same logging level.
        try:
            if debug:
                container.config.logger.level.from_value("DEBUG")
            elif warning:
                container.config.logger.level.from_value("WARNING")
            elif verbose:
                container.config.logger.level.from_value("INFO")
        except Exception:
            pass
        config_manager = container.config_manager()
    except Exception:
        config_manager = ConfigManager()

    # Normalize pattern list
    pattern_list = [p.strip() for p in patterns.split(",")] if patterns else None

    # Coerce defaults if user omitted boolean tri-state options
    if recursive is None:
        recursive = config_manager.load_config().get("recursive_scan", True)
    if threshold is None:
        threshold = config_manager.load_config().get("fuzzy_threshold", 0.8)
    if verbose is None:
        verbose = config_manager.load_config().get("verbose_mode", False)

    # Delegate to the existing runner and propagate its integer exit code.
    rc = _run_scan(
        directory=directory,
        db_path=db_path,
        patterns=pattern_list,
        recursive=recursive,
        export=export,
        threshold=threshold,
        verbose=verbose,
        progress=progress,
        color=color,
        config_manager=config_manager,
        debug=debug,
        warning=warning,
    )

    # Typer expects commands to either return normally or raise SystemExit
    # for non-zero exit codes. Convert integer return codes into SystemExit
    # only at this top-level adapter boundary so library code does not call
    # sys.exit directly and tests can call _run_scan() safely.
    if isinstance(rc, int) and rc != 0:
        raise SystemExit(rc)


# Provide a safe callable `app` that wraps the Typer instance and
# converts SystemExit into a normal return value for programmatic
# test invocations. The original Typer object is kept as `_typer_app`.

# Export the Typer instance as `app` for compatibility with tests that
# expect a Typer object to be importable from this module.
class _TyperAppProxy:
    """Proxy around the Typer app that swallows SystemExit when the app
    is called programmatically (e.g. in tests). Attribute access is
    delegated to the underlying Typer instance so tests can inspect
    internals like `callback`.
    """

    def __init__(self, inner):
        self._inner = inner

    def __call__(self, *args, **kwargs):
        try:
            return self._inner(*args, **kwargs)
        except SystemExit:
            # Convert SystemExit into its integer exit code so
            # programmatic callers (tests) can observe non-zero
            # exit conditions without the process actually exiting.
            exc = None
            try:
                import sys as _sys

                # Prefer to capture the caught exception if available
                exc = _sys.exc_info()[1]
            except Exception:
                exc = None
            code = 0
            try:
                if exc is not None and hasattr(exc, "code"):
                    code = int(exc.code) if isinstance(exc.code, int) else 0
            except Exception:
                code = 0
            return code

    def __getattr__(self, name):
        return getattr(self._inner, name)


app = _TyperAppProxy(_typer_app)


def cli_main(argv: Optional[list] = None) -> int:
    """Entry point for running the Typer CLI from the command line.

    This keeps a separate small wrapper name to avoid colliding with the
    Click-based `main` in `src.cli.main` when both modules are imported in
    tests or programmatically.
    """
    try:
        app(prog_name="specify-typer", args=argv or [])
        return 0
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else 0


if __name__ == "__main__":
    raise SystemExit(cli_main())

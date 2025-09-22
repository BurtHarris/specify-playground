import tempfile
from pathlib import Path

import typer


def test_typer_scan_command_imports_and_runs_minimally(tmp_path: Path):
    # Create an empty temporary directory to scan
    scan_dir = tmp_path / "scan-me"
    scan_dir.mkdir()

    # Import the Typer app and invoke the scan command with the temp dir
    from src.cli.typer_cli import app

    # Run the command programmatically; Typer returns normally if no SystemExit
    result = app.callback.__closure__
    # Call main entry with args pointing to the temp directory
    # The test ensures no raised exceptions during invocation
    app(args=[str(scan_dir)])

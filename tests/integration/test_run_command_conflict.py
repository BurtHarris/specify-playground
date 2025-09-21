from click.testing import CliRunner
from pathlib import Path

from src.cli.main import main


def test_run_command_conflict_warns_and_shows_verbose_header(tmp_path):
    runner = CliRunner()
    d = tmp_path / "empty"
    d.mkdir()

    # Use the higher-level 'main' entrypoint which includes the rich scan command
    # Do not combine --verbose with --debug; per-file output is debug-only.
    result = runner.invoke(main, ["scan", str(d), "--debug", "--warning"], catch_exceptions=False)

    assert "both --debug and --warning specified" in result.output
    assert result.exit_code == 0

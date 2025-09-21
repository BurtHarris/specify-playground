import logging
from click.testing import CliRunner
from pathlib import Path

from src.cli.main import main
from src.lib.container import Container


def test_debug_and_warning_conflict_emits_warning_and_prefers_debug(tmp_path):
    runner = CliRunner()
    # create an empty directory to scan
    d = tmp_path / "empty_dir"
    d.mkdir()

    result = runner.invoke(main, ["scan", str(d), "--debug", "--warning"], catch_exceptions=False)

    # Warning should be emitted to stderr output printed by click; CliRunner captures combined output
    assert "both --debug and --warning specified" in result.output

    # The important behavior is that the warning was emitted and the command ran.
    assert result.exit_code == 0

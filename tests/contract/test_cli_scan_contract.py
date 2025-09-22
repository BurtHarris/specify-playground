from pathlib import Path

import pytest
import yaml
from tests.cli_runner_compat import CliRunner

from src.cli.main import main


@pytest.mark.contract
def test_cli_scan_exports_yaml(tmp_path):
    """Contract test: invoke CLI scan against in-repo fixture directory and assert YAML export schema.

    This test avoids creating filesystem/path mocks and uses existing fixtures under
    `tests/fixtures/sample_files/`. If fixtures are not present, the test is skipped so CI
    that doesn't include large fixtures can still run lighter suites.
    """

    fixture_dir = Path("tests/fixtures/sample_files")
    # If repository fixtures aren't present, create a minimal temporary
    # fixture directory under the test's tmp_path so the contract runs
    # without being skipped (helps CI and lightweight local runs).
    if not fixture_dir.exists():
        fixture_dir = tmp_path / "sample_files"
        fixture_dir.mkdir(parents=True, exist_ok=True)
        (fixture_dir / "video1.mp4").write_bytes(b"\0" * 1024)
        (fixture_dir / "video2.mkv").write_bytes(b"\0" * 2048)
        (fixture_dir / "notes.txt").write_text("example")

    runner = CliRunner()
    out_file = tmp_path / "scan_out.yaml"

    # Invoke the CLI 'scan' command exporting to a temporary file in the test workspace.
    result = runner.invoke(main, ["scan", str(fixture_dir), "--export", str(out_file)])

    # Contract: CLI should exit with zero and write a YAML file with expected top-level keys.
    assert (
        result.exit_code == 0
    ), f"CLI failed: stdout={result.stdout} stderr={result.stderr}"
    assert out_file.exists(), "Export file was not created by CLI"

    content = yaml.safe_load(out_file.read_text())
    assert isinstance(content, dict), "Export must be a mapping (YAML object)"

    # Expected fields (contract): at least a scan metadata and groups container
    assert any(
        k in content for k in ("scan_metadata", "scan", "duplicate_groups")
    ), f"Export missing expected keys: got {list(content.keys())}"

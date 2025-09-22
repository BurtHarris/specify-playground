import subprocess
import yaml
import shutil
from pathlib import Path

import pytest


@pytest.mark.integration
def test_series_behavior_integration(tmp_path):
    """
    Integration test: run the CLI to export YAML and validate that:
      - Exact byte-identical files with series-like names are reported as duplicates
      - Series-like files with differing content/sizes are NOT reported as potential matches
    """
    # Prepare files
    scan_dir = tmp_path / "scan"
    scan_dir.mkdir()

    # Exact duplicate pair (same content) with series-like names
    dup1 = scan_dir / "series part 1.mp4"
    dup2 = scan_dir / "series part 2.mp4"
    dup1.write_bytes(b"SAMECONTENT")
    dup2.write_bytes(b"SAMECONTENT")

    # Series-like pair with different content/sizes (should be excluded from potential matches)
    var1 = scan_dir / "other series part 1.mp4"
    var2 = scan_dir / "other series part 2.mp4"
    var1.write_bytes(b"A" * 1000)
    var2.write_bytes(b"B" * 2000)

    export_file = tmp_path / "results.yaml"

    # Run CLI exporter
    result = subprocess.run(
        ["python", "-m", "src", "--export", str(export_file), str(scan_dir)],
        capture_output=True,
        text=True,
        cwd=str(Path.cwd()),
    )

    assert result.returncode == 0, f"CLI failed: {result.stderr}\n{result.stdout}"
    assert export_file.exists()

    with open(export_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    # Validate structure
    assert "duplicate_groups" in data
    assert "potential_matches" in data

    # The duplicate pair (same content) should appear in duplicate_groups
    dup_found = False
    for group in data.get("duplicate_groups", []):
        paths = [p.get("path") for p in group.get("files", [])]
        if str(dup1) in paths and str(dup2) in paths:
            dup_found = True
            break
    assert dup_found, "Exact duplicates inside a series were not exported as duplicates"

    # The var1/var2 pair (different content and sizes) should NOT be present as a potential match
    potential_contains_var_pair = False
    for group in data.get("potential_match_groups", []):
        paths = [p.get("path") for p in group.get("files", [])]
        if str(var1) in paths and str(var2) in paths:
            potential_contains_var_pair = True
            break

    assert not potential_contains_var_pair, "Series-like differing files were incorrectly reported as potential matches"

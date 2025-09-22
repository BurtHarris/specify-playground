import time
from pathlib import Path

from src.models.scan_metadata import ScanMetadata


def test_to_dict_and_timing():
    md = ScanMetadata([Path("/tmp"), Path("./")], recursive=False)
    assert md.scan_paths
    md.start_scan()
    time.sleep(0.01)
    md.increment_processed(1024)
    md.increment_hashed(__import__("datetime").timedelta(milliseconds=5))
    md.update_duplicate_stats(0, 0)
    md.end_scan()

    d = md.to_dict()
    assert "timing" in d
    assert d["file_statistics"]["total_files_processed"] == 1
    assert d["performance_metrics"]["total_hash_time_seconds"] >= 0


def test_error_and_skipped_records():
    md = ScanMetadata([Path(".")])
    md.add_error(Path("/nope"), "permission denied", error_type="permission")
    md.add_skipped_file(Path("/skip"), "pattern")

    d = md.to_dict()
    assert len(d["errors"]) == 1
    assert len(d["skipped_files"]) == 1
    assert d["file_statistics"]["total_files_error"] == 1
    assert d["file_statistics"]["total_files_skipped"] == 1

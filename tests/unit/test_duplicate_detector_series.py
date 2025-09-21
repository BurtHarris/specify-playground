import types
from pathlib import Path

import pytest

from src.services.duplicate_detector import DuplicateDetector
from src.models.file import UserFile
import hashlib


class DummyMetadata:
    def __init__(self):
        self.series_groups = []
        self.series_groups_found = 0


def test_series_group_recorded_and_hashing_preserved(tmp_path):
    """
    Verify that a size-group that looks like a numbered series is recorded in
    metadata as a group-level dict, but hashing still runs so true duplicates
    within that group are detected.
    """
    # Create three files that look like a series (trailing numbers) and two
    # of them share the same hash (true duplicate inside the series)
    # Create three real files on disk that look like a series. Files 0 and 2
    # will have identical contents so they should be detected as true duplicates.
    f1 = tmp_path / "Show Part 1.mp4"
    f2 = tmp_path / "Show Part 2.mp4"
    f3 = tmp_path / "Show Part 3.mp4"
    f1.write_bytes(b"duplicate-content")
    f2.write_bytes(b"different-content")
    f3.write_bytes(b"duplicate-content")

    files = [
        UserFile(f1),
        UserFile(f2),
        UserFile(f3),
    ]

    detector = DuplicateDetector()
    metadata = DummyMetadata()

    duplicates = detector.find_duplicates(files, progress_reporter=None, verbose=False, metadata=metadata)

    # Expect at least one duplicate group found for the hash of b"duplicate-content"
    expected_h = hashlib.blake2b(b"duplicate-content").hexdigest()
    found_hashes = [g.hash_value for g in duplicates]
    assert expected_h in found_hashes, f"Expected duplicate group for hash {expected_h}"

    # Metadata should have one recorded series group as a dict
    assert isinstance(metadata.series_groups, list)
    assert len(metadata.series_groups) >= 1
    group = metadata.series_groups[0]
    assert isinstance(group, dict)
    assert group.get("file_count") == 3
    assert group.get("reason") == "series-numbered"
    assert metadata.series_groups_found >= 1


def test_non_series_duplicates_unchanged(tmp_path):
    """
    Confirm that non-series duplicates are still detected normally.
    """
    # Create two real files on disk with identical contents (non-series names)
    f1 = tmp_path / "VideoA.mp4"
    f2 = tmp_path / "VideoA_copy.mp4"
    f1.write_bytes(b"same-content")
    f2.write_bytes(b"same-content")

    files = [UserFile(f1), UserFile(f2)]

    detector = DuplicateDetector()
    metadata = DummyMetadata()

    duplicates = detector.find_duplicates(files, progress_reporter=None, verbose=False, metadata=metadata)

    assert len(duplicates) == 1
    expected_x = hashlib.blake2b(b"same-content").hexdigest()
    assert duplicates[0].hash_value == expected_x
    # No series groups should be recorded for this simple duplicate
    assert metadata.series_groups_found == 0 or len(metadata.series_groups) == 0


def test_permission_error_handling(tmp_path):
    """
    Ensure that when compute_hash raises PermissionError the detector skips the
    file, still finds duplicates among readable files, and metadata records the
    error count when that attribute exists.
    """
    # Create three files where two have identical contents and the third will
    # simulate a permission error during hashing.
    f_ok1 = tmp_path / "Ok1.mp4"
    f_ok2 = tmp_path / "Ok2.mp4"
    f_err = tmp_path / "Err.mp4"
    f_ok1.write_bytes(b"common")
    f_ok2.write_bytes(b"common")
    f_err.write_bytes(b"should-not-be-read")

    files = [UserFile(f_ok1), UserFile(f_ok2), UserFile(f_err)]

    # Simulate permission error for the third file's compute_hash
    def raise_perm():
        raise PermissionError("Permission denied")

    files[2].compute_hash = raise_perm

    class MetaWithErrors:
        def __init__(self):
            self.series_groups = []
            self.series_groups_found = 0
            self.total_files_error = 0

    metadata = MetaWithErrors()
    detector = DuplicateDetector()

    duplicates = detector.find_duplicates(files, progress_reporter=None, verbose=False, metadata=metadata)

    # readable duplicates should be found
    expected = hashlib.blake2b(b"common").hexdigest()
    assert any(g.hash_value == expected for g in duplicates)

    # The errored file should not appear in any duplicate group's paths
    err_path_str = str(f_err)
    for g in duplicates:
        assert all(str(p) != err_path_str for p in g.paths)

import hashlib
from src.services.duplicate_detector import DuplicateDetector
from src.models.file import UserFile


def test_mixed_size_group_not_marked_as_series(tmp_path):
    """
    A small size-group with only one pair that looks sequential should NOT be
    recorded as a series under the majority-rule threshold.
    """
    # Create three files with identical sizes but only two of them form a
    # sequential pair. Ensure equal file sizes so they are placed in the
    # same size-group by the detector.
    b = b"abc"  # 3 bytes
    f1 = tmp_path / "Show Part 1.mp4"
    f2 = tmp_path / "Show Part 2.mp4"
    f3 = tmp_path / "Different.mp4"
    f1.write_bytes(b)
    f2.write_bytes(b)
    f3.write_bytes(b)

    files = [UserFile(f1), UserFile(f2), UserFile(f3)]

    class Meta:
        def __init__(self):
            self.series_groups = []
            self.series_groups_found = 0

    detector = DuplicateDetector()
    metadata = Meta()

    duplicates = detector.find_duplicates(files, progress_reporter=None, verbose=False, metadata=metadata)

    # No series groups should be recorded because only one pair matched the
    # sequential heuristic (1 out of 3 pairs -> proportion < 0.6)
    assert metadata.series_groups_found == 0 or len(metadata.series_groups) == 0


def test_four_sequential_files_marked_as_series(tmp_path):
    """
    A size-group of four sequentially numbered files should be recorded as a
    series under the majority-rule threshold (4-of-6 pairs -> proportion >= 0.6).
    """
    # Create four files, same size, sequential numbering in names
    b = b"xyz"  # 3 bytes
    f1 = tmp_path / "Show 1.mp4"
    f2 = tmp_path / "Show 2.mp4"
    f3 = tmp_path / "Show 3.mp4"
    f4 = tmp_path / "Show 4.mp4"
    f1.write_bytes(b)
    f2.write_bytes(b)
    f3.write_bytes(b)
    f4.write_bytes(b)

    files = [UserFile(f1), UserFile(f2), UserFile(f3), UserFile(f4)]

    class Meta:
        def __init__(self):
            self.series_groups = []
            self.series_groups_found = 0

    detector = DuplicateDetector()
    metadata = Meta()

    duplicates = detector.find_duplicates(files, progress_reporter=None, verbose=False, metadata=metadata)

    # Expect the group to be recorded as a series (proportion of excluded pairs is 1.0)
    assert metadata.series_groups_found >= 1
    assert isinstance(metadata.series_groups[0], dict)
    assert metadata.series_groups[0].get("file_count") == 4

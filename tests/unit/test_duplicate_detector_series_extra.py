import tempfile
from pathlib import Path

import pytest

from src.services.duplicate_detector import DuplicateDetector
from src.models.file import UserFile


def _make_temp_file_with_name(dir: Path, name: str, content: bytes = b"x") -> Path:
    p = dir / name
    p.write_bytes(content)
    return p


def test_is_series_pair_variants():
    det = DuplicateDetector()
    n1 = "ich bringe dir bdsm bei - episode 2"
    n2 = "ich bringe dir bdsm bei - episode 3"
    assert det._is_series_pair(n1, n2)

    n3 = "peitsche - chapter 02"
    n4 = "peitsche - chapter 03"
    assert det._is_series_pair(n3, n4)

    # trailing numeric tokens
    n5 = "movie title 1"
    n6 = "movie title 2"
    assert det._is_series_pair(n5, n6)


def test_find_potential_matches_excludes_series_by_size(tmp_path):
    # Create two files that look like a series and end with numeric tokens
    f1 = _make_temp_file_with_name(tmp_path, "series part 1.mp4", b"a" * 1000)
    f2 = _make_temp_file_with_name(tmp_path, "series part 2.mp4", b"b" * 2000)
    try:
        uf1 = UserFile(f1)
        uf2 = UserFile(f2)

        det = DuplicateDetector()
        # Use a low threshold so names are considered similar
        groups = det.find_potential_matches([uf1, uf2], threshold=0.5, verbose=True)

        # Since sizes differ by >10% and names look like series, they should be excluded
        assert len(groups) == 0
    finally:
        f1.unlink(missing_ok=True)
        f2.unlink(missing_ok=True)


def test_exact_duplicates_within_series_are_found(tmp_path):
    # Two files with same content but series-like names should still be detected as duplicates
    f1 = _make_temp_file_with_name(tmp_path, "series part 1.mp4", b"dupcontent")
    f2 = _make_temp_file_with_name(tmp_path, "series part 2.mp4", b"dupcontent")
    try:
        uf1 = UserFile(f1)
        uf2 = UserFile(f2)

        det = DuplicateDetector()
        dups = det.find_duplicates([uf1, uf2], verbose=True)

        # They should be grouped as duplicates because hashing is performed regardless
        assert any(len(g.files) >= 2 for g in dups)
    finally:
        f1.unlink(missing_ok=True)
        f2.unlink(missing_ok=True)

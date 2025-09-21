import tempfile
import shutil
from pathlib import Path
import logging

import pytest

from src.services.duplicate_detector import DuplicateDetector
from src.models.user_file import UserFile


class MockDB:
    def __init__(self, ok=True):
        self.is_initialized = ok
        self.calls = []

    def set_cached_hash(self, path, size, mtime, hashval):
        self.calls.append((str(path), size, mtime, hashval))

    def ping(self):
        if not self.is_initialized:
            raise RuntimeError("not initialized")
        return True


def make_temp_files(tmpdir: Path):
    files = []
    for name, text in (
        ("doc1.txt", "hello world"),
        ("doc2.txt", "hello world"),
        ("unique.txt", "unique content here"),
    ):
        p = tmpdir / name
        p.write_text(text, encoding="utf-8")
        files.append(UserFile(p))
    return files


def run_detector_with_db(db):
    tmpdir = Path(tempfile.mkdtemp())
    try:
        files = make_temp_files(tmpdir)
        detector = DuplicateDetector()
        return detector.find_duplicates(files, progress_reporter=None, verbose=True, metadata=None, db=db)
    finally:
        shutil.rmtree(tmpdir)


def test_detector_with_mock_db_initialised(caplog):
    caplog.set_level(logging.INFO)
    db = MockDB(ok=True)
    groups = run_detector_with_db(db)
    assert isinstance(groups, list)
    assert len(groups) >= 0
    assert "Database updated with scan results." in caplog.text


def test_detector_with_db_none_warns(caplog):
    caplog.set_level(logging.WARNING)
    groups = run_detector_with_db(None)
    assert isinstance(groups, list)
    assert "No database provided; scan results were not persisted." in caplog.text


def test_detector_with_bad_db_raises():
    db = MockDB(ok=False)
    with pytest.raises(RuntimeError):
        run_detector_with_db(db)

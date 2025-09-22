import logging
import tempfile
import shutil
from pathlib import Path
import pytest

from src.services.duplicate_detector import DuplicateDetector
from src.models.file import UserFile


class MockDBGood:
    def __init__(self):
        self.db_path = Path(tempfile.mktemp(suffix=".db"))
        self.is_initialized = True
        self._conn = None
    def ping(self):
        return True
    def set_cached_hash(self, path, size, mtime, hashval):
        return None


class MockDBMissing(FileNotFoundError):
    pass


class MockDBNotInitialized:
    def __init__(self):
        self.db_path = Path(tempfile.mktemp(suffix=".db"))
        self.is_initialized = False
    def ping(self):
        raise RuntimeError("not initialized")
    def set_cached_hash(self, *args, **kwargs):
        pass


class MockDBCorrupt:
    def __init__(self):
        self.db_path = Path(tempfile.mktemp(suffix=".db"))
    def get_cached_hash(self, *args, **kwargs):
        import sqlite3
        raise sqlite3.DatabaseError("file is not a database")
    def set_cached_hash(self, *args, **kwargs):
        pass


def make_files(tmpdir: Path):
    files = []
    for name, text in (("a.txt", "x"), ("b.txt", "x"), ("c.txt", "y")):
        p = tmpdir / name
        p.write_text(text, encoding="utf-8")
        files.append(UserFile(p))
    return files


def test_db_ok_logs_info(caplog, tmp_path):
    caplog.set_level(logging.INFO)
    tmpdir = tmp_path / "detector_test"
    tmpdir.mkdir()
    files = make_files(tmpdir)
    db = MockDBGood()
    detector = DuplicateDetector()
    groups = detector.find_duplicates(files, verbose=True, db=db)
    # When DB is OK an INFO about update should be present
    assert any("Database updated with scan results" in r.getMessage() for r in caplog.records)


def test_db_none_warns(caplog, tmp_path):
    caplog.set_level(logging.WARNING)
    tmpdir = tmp_path / "detector_test2"
    tmpdir.mkdir()
    files = make_files(tmpdir)
    detector = DuplicateDetector()
    groups = detector.find_duplicates(files, verbose=True, db=None)
    assert any("No database provided; scan results were not persisted" in r.getMessage() for r in caplog.records)


def test_db_not_initialized_raises(tmp_path):
    tmpdir = tmp_path / "detector_test3"
    tmpdir.mkdir()
    files = make_files(tmpdir)
    db = MockDBNotInitialized()
    detector = DuplicateDetector()
    with pytest.raises(Exception):
        detector.find_duplicates(files, verbose=True, db=db)


def test_db_corrupt_regenerates_and_warns(caplog, tmp_path, monkeypatch):
    caplog.set_level(logging.WARNING)
    tmpdir = tmp_path / "detector_test4"
    tmpdir.mkdir()
    files = make_files(tmpdir)
    db = MockDBCorrupt()
    detector = DuplicateDetector()
    # The detector tries to import FileDatabase and recreate; ensure schema.sql exists
    schema = Path(__file__).resolve().parents[2] / "src" / "services" / "schema.sql"
    if not schema.exists():
        schema.write_text("CREATE TABLE directories(id INTEGER PRIMARY KEY); CREATE TABLE file_hashes(id INTEGER PRIMARY KEY, directory_id INTEGER, path TEXT, size INTEGER, mtime REAL, hash TEXT);")
    detector.find_duplicates(files, verbose=True, db=db)
    assert any("Corrupt database regenerated" in (r.getMessage() or "") for r in caplog.records)

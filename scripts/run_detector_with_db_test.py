"""
Quick runner to exercise DuplicateDetector.find_duplicates under two cases:
1) with a mock DB that reports initialized
2) with db=None

Creates tiny temp files (documents) in a tempdir, runs the detector, and prints concise outputs.
"""
import tempfile
import os
import shutil
from pathlib import Path
import logging

# Ensure project packages importable
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.services.duplicate_detector import DuplicateDetector
from src.models.user_file import UserFile

# Minimal mock DB that appears initialized
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
        st = p.stat()
        files.append(UserFile(p))
    return files


def run_case(db, description):
    print("\n---", description)
    tmpdir = Path(tempfile.mkdtemp())
    try:
        files = make_temp_files(tmpdir)
        detector = DuplicateDetector()
        try:
            groups = detector.find_duplicates(files, progress_reporter=None, verbose=True, metadata=None, db=db)
            print(f"Returned {len(groups)} duplicate groups")
        except Exception as e:
            print(f"Raised exception: {e!r}")
    finally:
        shutil.rmtree(tmpdir)


if __name__ == '__main__':
    # Configure basic logging to stdout
    logging.basicConfig(level=logging.DEBUG)

    mock_db = MockDB(ok=True)
    run_case(mock_db, "Run with mock DB (initialized)")

    run_case(None, "Run with db=None (should warn but not raise)")

    # Also run with failing DB to demonstrate RuntimeError
    bad_db = MockDB(ok=False)
    run_case(bad_db, "Run with mock DB (not initialized) - should raise")

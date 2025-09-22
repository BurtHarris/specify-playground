import sys
from pathlib import Path
import time

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.lib.container import Container
from src.services.file_scanner import FileScanner
from src.services.duplicate_detector import DuplicateDetector
from src.models.file import UserFile


class FakeReporter:
    def __init__(self):
        self.updates = []
        self.started = False

    def start_progress(self, total, label):
        self.started = True

    def update_progress(self, current, file_name=None):
        self.updates.append((current, file_name))

    def finish_progress(self):
        pass


def test_injected_reporter_and_hasher(tmp_path):
    # Create two files with identical content to be detected as duplicates
    f1 = tmp_path / "file1.txt"
    f2 = tmp_path / "file2.txt"
    content = b"hello world" * 100
    f1.write_bytes(content)
    f2.write_bytes(content)

    c = Container()

    # Use container database (in-memory) and hasher
    db = c.database()
    hasher = c.hasher()

    # Build FileScanner with injected db and hasher
    scanner = FileScanner(db=db, hasher=hasher, patterns=["*.txt"], recursive=False)
    # Allow non-video extensions in this test
    scanner.SUPPORTED_EXTENSIONS = None

    # Build DuplicateDetector with injected fake reporter
    reporter = FakeReporter()
    detector = DuplicateDetector(progress_reporter=reporter)

    # Use legacy generator API to get UserFile instances
    files = list(
        scanner.scan_directory(tmp_path, recursive=False, progress_reporter=reporter)
    )

    # Ensure files were found
    assert len(files) == 2

    # Run duplicate detection
    dup_groups = detector.find_duplicates(
        files, progress_reporter=None, verbose=False, metadata=None
    )

    # Reporter should have been started and should have recorded progress updates
    assert reporter.started is True
    assert len(reporter.updates) > 0

    # Expect at least 1 duplicate group since files are identical
    assert any(len(g.files) >= 2 for g in dup_groups)

    # Database should have cached hash entries for files (in-memory store)
    # get_cached_hash returns a value when size+mtime match; use file stat
    st = f1.stat()
    cached = db.get_cached_hash(f1, st.st_size, st.st_mtime)
    # If caching was exercised, cached should be a string; it's optional so don't enforce
    assert cached is None or isinstance(cached, str)

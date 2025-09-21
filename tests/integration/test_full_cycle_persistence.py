import sqlite3
import tempfile
import sqlite3
from pathlib import Path

from src.services.duplicate_detector import DuplicateDetector
from src.models.file import UserFile
from src.services.file_database import get_database
from src.services.file_scanner import FileScanner


def create_db_from_schema(db_path: Path):
    # schema is at repo/src/services/schema.sql
    schema = Path(__file__).resolve().parents[2] / 'src' / 'services' / 'schema.sql'
    if not schema.exists():
        schema = Path('src') / 'services' / 'schema.sql'
    conn = sqlite3.connect(str(db_path))
    try:
        conn.executescript(schema.read_text(encoding='utf-8'))
        conn.commit()
    finally:
        conn.close()


def test_full_cycle_persistence(tmp_path: Path):
    # Prepare temp files
    dir_path = tmp_path / 'files'
    dir_path.mkdir()
    file1 = dir_path / 'a.txt'
    file2 = dir_path / 'b.txt'
    content = b"hello world"
    file1.write_bytes(content)
    file2.write_bytes(content)

    # Wrap in UserFile
    uf1 = UserFile(path=file1)
    uf2 = UserFile(path=file2)

    # Create fresh DB
    db_path = tmp_path / 'spec_scan_test.db'
    create_db_from_schema(db_path)

    # Obtain a FileDatabase instance pointing at the new DB
    db = get_database(db_path)

    # Run detector
    detector = DuplicateDetector()
    groups = detector.find_duplicates([uf1, uf2], verbose=False, db=db)

    # Ensure duplicate group found
    assert any(len(getattr(g, 'files', [])) >= 2 for g in groups), "Expected at least one duplicate group"

    # Inspect DB for persisted hashes
    conn = sqlite3.connect(str(db_path))
    try:
        cur = conn.cursor()
        cur.execute('SELECT COUNT(*) FROM file_hashes')
        count = cur.fetchone()[0]
    finally:
        conn.close()

    assert count >= 2, f"Expected at least 2 rows in file_hashes, got {count}"


def test_cache_reuse(tmp_path: Path):
    # Prepare temp files
    dir_path = tmp_path / 'files'
    dir_path.mkdir()
    file1 = dir_path / 'a.txt'
    file2 = dir_path / 'b.txt'
    content = b"hello world"
    file1.write_bytes(content)
    file2.write_bytes(content)

    # Create fresh DB
    db_path = tmp_path / 'spec_scan_test.db'
    create_db_from_schema(db_path)
    db = get_database(db_path)

    # Instrumented hasher to count calls
    calls = []

    def fake_hasher(path, chunk_size=1024 * 1024):
        calls.append(str(path))
        # return a deterministic fake hash
        return f"fakehash-{path.name}"

    scanner = FileScanner(db_path=db_path, hasher=fake_hasher, db=db)

    # First run should call the hasher for each file
    results1 = scanner.scan([dir_path])
    assert len(calls) == 2, f"Hasher should have been called for 2 files, called: {len(calls)}"

    # DB should now contain entries
    conn = sqlite3.connect(str(db_path))
    try:
        cur = conn.cursor()
        cur.execute('SELECT COUNT(*) FROM file_hashes')
        count = cur.fetchone()[0]
    finally:
        conn.close()
    assert count >= 2

    # Clear call list and run again; hasher should NOT be called if cache used
    calls.clear()
    results2 = scanner.scan([dir_path])
    assert len(calls) == 0, f"Hasher should not be called on second run when cache exists, called: {len(calls)}"

    # Hash values should match between runs
    hashes1 = {r['path']: r['hash'] for r in results1}
    hashes2 = {r['path']: r['hash'] for r in results2}
    assert hashes1 == hashes2

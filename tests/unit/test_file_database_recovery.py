import sqlite3
import tempfile
from pathlib import Path
import logging

from src.services.file_database import get_database, FileDatabase, InMemoryFileDatabase


def test_get_database_creates_new_db(tmp_path, caplog):
    caplog.set_level(logging.INFO)
    db_path = tmp_path / "new_test.db"
    # Ensure file does not exist
    if db_path.exists():
        db_path.unlink()

    db = get_database(db_path)
    # Should return a FileDatabase connected to the file
    assert isinstance(db, FileDatabase)
    assert db.db_path == db_path
    # The file should now exist
    assert db_path.exists()


def test_get_database_regenerates_corrupt_db(tmp_path, caplog):
    caplog.set_level(logging.WARNING)
    db_path = tmp_path / "corrupt_test.db"
    # Create a file that's not a valid sqlite DB
    db_path.write_text("not a sqlite db", encoding="utf-8")

    db = get_database(db_path)
    # If corruption was detected, a fresh FileDatabase should be returned
    assert isinstance(db, FileDatabase)
    # Original corrupt file should have been moved to a .corrupt backup or removed
    corrupt_backup = db_path.with_suffix(db_path.suffix + ".corrupt")
    assert not db_path.exists() or corrupt_backup.exists()
    # A warning about regeneration should be emitted
    assert any("Corrupt database regenerated" in r.getMessage() for r in caplog.records)


def test_get_database_falls_back_to_memory_on_init_failure(tmp_path):
    # Simulate schema init failure by creating a path where init_schema will fail
    db_path = tmp_path / "badinit.db"
    # Create directory at the path to cause connect() to fail
    db_path.mkdir()
    db = get_database(db_path)
    assert isinstance(db, InMemoryFileDatabase)

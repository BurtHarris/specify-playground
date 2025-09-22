"""SQLite-backed cache for file hashes and scan metadata.

This is a minimal skeleton implementing the public surface required by
the current tests and the task plan (connect, init_schema, get_cached_hash,
set_cached_hash). Full implementation will follow in later tasks.
"""

import sqlite3
from pathlib import Path
from typing import Optional

from src.lib.exceptions import DatabaseCorruptError, DatabaseNotConfiguredError


class FileDatabase:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = Path(db_path) if db_path else None
        self._conn: Optional[sqlite3.Connection] = None

    def connect(self):
        if self.db_path is None:
            raise DatabaseNotConfiguredError("Database path not set")
        try:
            self._conn = sqlite3.connect(str(self.db_path))
            self._conn.row_factory = sqlite3.Row
            return self._conn
        except sqlite3.DatabaseError as e:
            # Surface a clear error that higher-level code can catch and
            # fall back to an in-memory database if desired.
            raise DatabaseCorruptError(f"Failed to open database: {e}")

    def init_schema(self):
        """Initialize the database schema from bundled SQL."""
        if self._conn is None:
            self.connect()
        cur = self._conn.cursor()
        sql = Path(__file__).parent / "schema.sql"
        cur.executescript(sql.read_text())
        self._conn.commit()

    def get_cached_hash(self, path: Path, size: int, mtime: float) -> Optional[str]:
        """Return cached hash if present and matching size+mtime, else None."""
        if self._conn is None:
            self.connect()
        # Look up directory_id for the parent directory to normalize paths
        cur = self._conn.cursor()
        parent = str(Path(path).parent)
        cur.execute("SELECT id FROM directories WHERE path = ? LIMIT 1", (parent,))
        row = cur.fetchone()
        if not row:
            return None
        directory_id = row[0]
        cur.execute(
            "SELECT hash FROM file_hashes WHERE directory_id = ? AND path = ? AND size = ? AND mtime = ? LIMIT 1",
            (directory_id, str(path), int(size), float(mtime)),
        )
        row = cur.fetchone()
        return row["hash"] if row else None

    def set_cached_hash(
        self, path: Path, size: int, mtime: float, hash_value: str
    ) -> None:
        if self._conn is None:
            self.connect()
        cur = self._conn.cursor()
        parent = str(Path(path).parent)
        # Ensure directory record exists
        cur.execute("INSERT OR IGNORE INTO directories (path, canonical_path) VALUES (?, ?)", (parent, None))
        cur.execute("SELECT id FROM directories WHERE path = ?", (parent,))
        directory_id = cur.fetchone()[0]
        cur.execute(
            """
            INSERT INTO file_hashes (directory_id, path, size, mtime, hash)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(directory_id, path) DO UPDATE SET size=excluded.size, mtime=excluded.mtime, hash=excluded.hash
            """,
            (directory_id, str(path), int(size), float(mtime), hash_value),
        )
        self._conn.commit()


class InMemoryFileDatabase(FileDatabase):
    """Simple in-memory fallback implementing the same interface.

    Stores entries in a dict keyed by path. Intended for use when the
    on-disk SQLite DB is unavailable or corrupted.
    """

    def __init__(self):
        super().__init__(db_path=None)
        self._store = {}

    def connect(self):
        # No sqlite connection required for in-memory store
        self._conn = None
        return None

    def init_schema(self):
        # No-op for in-memory store
        return

    def get_cached_hash(self, path: Path, size: int, mtime: float) -> Optional[str]:
        rec = self._store.get(str(path))
        if not rec:
            return None
        r_size, r_mtime, r_hash = rec
        if r_size == int(size) and float(r_mtime) == float(mtime):
            return r_hash
        return None

    def set_cached_hash(
        self, path: Path, size: int, mtime: float, hash_value: str
    ) -> None:
        self._store[str(path)] = (int(size), float(mtime), hash_value)


def get_database(db_path: Optional[Path] = None):
    """Factory that attempts to open an on-disk DB and falls back to in-memory."""
    if db_path is None:
        return InMemoryFileDatabase()
    # If the DB file already exists, attempt to open it and assume the
    # schema is present; do not force schema initialization which can fail
    # when upgrading or when indexes reference older column names. If the
    # file does not exist, create it and initialize the schema.
    import logging

    logger = logging.getLogger("video_duplicate_scanner")

    try:
        if db_path.exists():
            # If a directory was supplied where a file is expected,
            # do not attempt to open it as SQLite; fall back to in-memory.
            if db_path.is_dir():
                logger = logging.getLogger("video_duplicate_scanner")
                logger.warning(f"Database path {db_path} is a directory; using in-memory fallback")
                return InMemoryFileDatabase()
            # Try opening existing DB; if it's corrupt, attempt to backup
            # and recreate a fresh DB (regenerate).
            db = FileDatabase(db_path=db_path)
            try:
                # Connect and perform a quick sanity query to detect
                # malformed or non-sqlite files which sqlite3.connect
                # may not raise for on some platforms.
                db.connect()
                try:
                    cur = db._conn.cursor()
                    cur.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 1")
                    _ = cur.fetchone()
                except sqlite3.DatabaseError:
                    # Treat as corruption to trigger regeneration logic
                    raise DatabaseCorruptError("Database file appears corrupt or invalid")
                return db
            except DatabaseCorruptError:
                # Ensure any open connection is closed before manipulating the
                # on-disk file (important on Windows where open handles
                # prevent rename/unlink operations).
                try:
                    if getattr(db, "_conn", None):
                        try:
                            db._conn.close()
                        except Exception:
                            pass
                except Exception:
                    pass

                # Backup the corrupt file and recreate
                bad_path = Path(db_path)
                backup_path = bad_path.with_suffix(bad_path.suffix + ".corrupt")
                # Try an atomic replace first; fall back to shutil.move which
                # is more tolerant on Windows filesystems.
                try:
                    if bad_path.exists():
                        bad_path.replace(backup_path)
                except Exception:
                    try:
                        import shutil

                        if bad_path.exists():
                            shutil.move(str(bad_path), str(backup_path))
                    except Exception:
                        # If move fails try unlink; if that fails, re-raise
                        try:
                            bad_path.unlink()
                        except Exception:
                            raise

                # Create fresh DB and initialize schema
                newdb = FileDatabase(db_path=bad_path)
                newdb.connect()
                newdb.init_schema()
                logger.warning(f"Corrupt database regenerated at {bad_path}; backup saved as {backup_path}")
                return newdb

        # New DB file: create and initialize schema
        db = FileDatabase(db_path=db_path)
        db.connect()
        try:
            db.init_schema()
        except Exception:
            # If schema init fails on a newly created file, prefer the
            # in-memory fallback to avoid breaking callers.
            return InMemoryFileDatabase()
        return db
    except DatabaseCorruptError:
        # If creation fails due to corruption, fall back to in-memory
        return InMemoryFileDatabase()

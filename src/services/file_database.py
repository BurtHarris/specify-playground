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

    def get_cached_hash(
        self, path: Path, size: int, mtime: float
    ) -> Optional[str]:
        """Return cached hash if present and matching size+mtime, else None."""
        if self._conn is None:
            self.connect()
        cur = self._conn.cursor()
        cur.execute(
            """
            SELECT hash FROM file_hashes
            WHERE path = ? AND size = ? AND mtime = ?
            LIMIT 1
            """,
            (str(path), int(size), float(mtime)),
        )
        row = cur.fetchone()
        return row["hash"] if row else None

    def set_cached_hash(
        self, path: Path, size: int, mtime: float, hash_value: str
    ) -> None:
        if self._conn is None:
            self.connect()
        cur = self._conn.cursor()
        cur.execute(
            """
            INSERT INTO file_hashes (path, size, mtime, hash)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(path) DO UPDATE SET size=excluded.size, mtime=excluded.mtime, hash=excluded.hash
            """,
            (str(path), int(size), float(mtime), hash_value),
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

    def get_cached_hash(
        self, path: Path, size: int, mtime: float
    ) -> Optional[str]:
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
    try:
        db = FileDatabase(db_path=db_path)
        db.connect()
        return db
    except DatabaseCorruptError:
        return InMemoryFileDatabase()

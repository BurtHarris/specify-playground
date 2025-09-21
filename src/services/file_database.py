"""SQLite-backed cache for file hashes and scan metadata.

This is a minimal skeleton implementing the public surface required by
the current tests and the task plan (connect, init_schema, get_cached_hash,
set_cached_hash). Full implementation will follow in later tasks.
"""

import sqlite3
from pathlib import Path
from typing import Optional, Tuple


class FileDatabaseError(Exception):
    pass


class FileDatabase:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = Path(db_path) if db_path else None
        self._conn: Optional[sqlite3.Connection] = None

    def connect(self):
        if self.db_path is None:
            raise FileDatabaseError("Database path not set")
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.row_factory = sqlite3.Row
        return self._conn

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

    def set_cached_hash(self, path: Path, size: int, mtime: float, hash_value: str) -> None:
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

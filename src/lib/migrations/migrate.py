# Database Migration Script
# Purpose: Handle schema migrations for SQLite database

import sqlite3
from pathlib import Path

MIGRATIONS = [
    # Example: (version, SQL)
    (
        "001_initial",
        """
    CREATE TABLE IF NOT EXISTS files (
        id INTEGER PRIMARY KEY,
        path TEXT UNIQUE,
        size INTEGER,
        hash TEXT,
        file_extension TEXT,
        modified_time TEXT,
        first_seen TEXT,
        last_seen TEXT,
        scan_count INTEGER
    );
    CREATE INDEX IF NOT EXISTS idx_files_path ON files(path);
    CREATE INDEX IF NOT EXISTS idx_files_hash ON files(hash);
    """,
    ),
    # Add further migrations as needed
]


def apply_migrations(db_path: Path):
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    for version, sql in MIGRATIONS:
        cur.executescript(sql)
    conn.commit()
    conn.close()


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python migrate.py <db_path>")
        sys.exit(1)
    apply_migrations(Path(sys.argv[1]))

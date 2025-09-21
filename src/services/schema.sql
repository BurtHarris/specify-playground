-- Schema for file hash cache

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS file_hashes (
    path TEXT PRIMARY KEY,
    size INTEGER NOT NULL,
    mtime REAL NOT NULL,
    hash TEXT NOT NULL,
    first_seen_at TEXT DEFAULT (datetime('now'))
);

-- Index for lookup by hash (for cross-scan queries)
CREATE INDEX IF NOT EXISTS idx_file_hashes_hash ON file_hashes(hash);

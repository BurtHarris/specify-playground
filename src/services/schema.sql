-- Schema for file hash cache

PRAGMA foreign_keys = ON;

-- Directories table: normalize directory paths for faster per-directory queries
CREATE TABLE IF NOT EXISTS directories (
    id INTEGER PRIMARY KEY,
    path TEXT NOT NULL UNIQUE,
    canonical_path TEXT,
    first_seen_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS file_hashes (
    id INTEGER PRIMARY KEY,
    directory_id INTEGER REFERENCES directories(id) ON DELETE CASCADE,
    path TEXT NOT NULL,
    size INTEGER NOT NULL,
    mtime REAL NOT NULL,
    hash TEXT NOT NULL,
    first_seen_at TEXT DEFAULT (datetime('now')),
    UNIQUE(directory_id, path)
);

-- Index for lookup by hash (for cross-scan queries)
CREATE INDEX IF NOT EXISTS idx_file_hashes_hash ON file_hashes(hash);
CREATE INDEX IF NOT EXISTS idx_file_hashes_dir ON file_hashes(directory_id);

from pathlib import Path
from typing import Iterable, List, Optional
import fnmatch
import logging
import os

from src.services.file_hasher import stream_hash
from src.services.file_database import get_database


logger = logging.getLogger(__name__)


class FileScanner:
    """Scans directories for files, computes hashes (streaming) and uses a
    database-backed cache for previously computed file hashes.

    This is a lightweight, prototypical implementation intended for tests and
    early integration. It intentionally keeps the public surface minimal.
    """

    def __init__(self, db_path: Optional[Path] = None, patterns: Optional[List[str]] = None, recursive: bool = True, chunk_size: int = 1024 * 1024):
        self.db = get_database(db_path)
        self.patterns = patterns or ["*"]
        self.recursive = recursive
        self.chunk_size = chunk_size

    # Keep a small compatibility surface expected by existing tests
    VIDEO_EXTENSIONS = {'.mp4', '.mkv', '.mov'}

    def validate_file(self, file_path: Path) -> bool:
        """Validate a file for being a non-empty local video file.

        Returns False for missing files, unreadable files or unsupported extensions.
        """
        try:
            if hasattr(file_path, 'is_file') and hasattr(file_path, 'stat') and hasattr(file_path, 'suffix'):
                path = file_path
            else:
                path = Path(file_path)
        except Exception:
            try:
                path = Path(str(file_path))
            except Exception:
                return False

        try:
            if not path.exists() or not path.is_file():
                return False
        except Exception:
            return False

        try:
            if path.suffix.lower() not in self.VIDEO_EXTENSIONS:
                return False
        except Exception:
            return False

        try:
            if not os.access(path, os.R_OK):
                return False
        except Exception:
            return False

        try:
            stat_result = path.stat()
            size = int(getattr(stat_result, 'st_size', 0))
        except Exception:
            return False

        if size <= 0:
            return False

        return True

    def _should_include_file(self, user_file, cloud_status: str) -> bool:
        """Simple cloud-status based filter used by older tests."""
        if cloud_status == 'all':
            return True
        elif cloud_status == 'local':
            return getattr(user_file, 'is_local', False)
        elif cloud_status == 'cloud-only':
            return getattr(user_file, 'is_cloud_only', False)
        else:
            return True

    def _match_patterns(self, name: str) -> bool:
        for pat in self.patterns:
            if fnmatch.fnmatch(name, pat):
                return True
        return False

    def scan(self, paths: Iterable[Path]) -> List[dict]:
        """Scan the given paths and return a list of file metadata dicts with keys: path, size, mtime, hash."""
        results = []
        for p in paths:
            p = Path(p)
            if not p.exists():
                logger.debug("Path does not exist, skipping: %s", p)
                continue
            if p.is_file():
                files = [p]
            else:
                if self.recursive:
                    files = [f for f in p.rglob("*") if f.is_file()]
                else:
                    files = [f for f in p.iterdir() if f.is_file()]

            for f in files:
                if not self._match_patterns(f.name):
                    continue
                try:
                    st = f.stat()
                except (OSError, PermissionError) as e:
                    logger.warning("Could not stat file %s: %s", f, e)
                    continue

                size = int(st.st_size)
                mtime = float(st.st_mtime)

                # Check cache
                try:
                    cached = self.db.get_cached_hash(f, size, mtime)
                except Exception:
                    # On any DB error, fall back to no-cache behaviour
                    cached = None

                if cached:
                    hash_value = cached
                else:
                    try:
                        hash_value = stream_hash(f, chunk_size=self.chunk_size)
                        try:
                            self.db.set_cached_hash(f, size, mtime, hash_value)
                        except Exception:
                            logger.debug("Failed to write cache for %s", f)
                    except Exception as e:
                        logger.warning("Failed to hash file %s: %s", f, e)
                        continue

                results.append({
                    "path": str(f),
                    "size": size,
                    "mtime": mtime,
                    "hash": hash_value,
                })

        return results

    def get_supported_extensions(self):
        """
        Get the set of supported video file extensions.

        Returns: Set of supported extensions (e.g., {'.mp4', '.mkv', '.mov'})
        """
        return self.VIDEO_EXTENSIONS.copy()

    def is_supported_extension(self, extension: str) -> bool:
        """
        Check if a file extension is supported.

        Args:
            extension: File extension to check (e.g., '.mp4')

        Returns:
            True if extension is supported
        """
        return extension.lower() in self.VIDEO_EXTENSIONS
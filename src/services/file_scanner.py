from pathlib import Path
from typing import List, Optional, Iterator
import fnmatch
import os

from src.services.file_database import get_database
from src.models.user_file import UserFile
from src.models.cloud_file_status import CloudFileStatus
from src.services.onedrive_service import OneDriveService

from src.lib.interfaces import (
    FileDatabaseProtocol,
    HasherProtocol,
    ProgressReporterProtocol,
)


class DirectoryNotFoundError(Exception):
    """Raised when a provided directory path cannot be found or accessed."""

    pass


class FileScanner:
    """Scans directories for files and provides two interfaces:

    - Legacy directory-based API: scan_directory/scan/scan_recursive that yield
      `UserFile` instances (backwards compatible with existing code/tests).
    - New path-iterable API: calling `scan()` with an iterable of paths
      returns a list of dict metadata (used by the new prototype tests).
    """

    # By default, only accept common video extensions for the historical
    # VideoFileScanner behavior used by contract tests. Tests can override
    # this by setting SUPPORTED_EXTENSIONS to a different set.
    SUPPORTED_EXTENSIONS = {".mp4", ".mkv", ".mov"}  # type: Optional[set]

    def __init__(
        self,
        db_path: Optional[Path] = None,
        patterns: Optional[List[str]] = None,
        recursive: bool = True,
        chunk_size: int = 1024 * 1024,
        db=None,
        hasher=None,
        logger=None,
        onedrive_service=None,
    ):
        # Allow injection of database, hasher, and logger for testing and IoC.
        # If not provided, fall back to module-level factories for backward
        # compatibility.
        self.db: FileDatabaseProtocol = db if db is not None else get_database(db_path)
        self._hasher: HasherProtocol = hasher
        # logger may be injected (container.logger()) for IoC; if not
        # provided, attempt to obtain one from the Container so module-level
        # logging is centralized. Fall back to the stdlib logger if the
        # container is unavailable (preserves previous behavior).
        if logger is not None:
            self.logger = logger
        else:
            try:
                from src.lib.container import Container

                self.logger = Container().logger()
            except Exception:
                import logging as _logging

                self.logger = _logging.getLogger(__name__)
        self.patterns = patterns or ["*"]
        self.recursive = recursive
        self.chunk_size = chunk_size
        # Initialize or accept injected OneDrive service for cloud-status
        # detection; keep a single instance for the scanner lifetime to
        # allow caching. Accepting an injected service enables IoC for
        # tests and platforms where OneDrive API is unavailable.
        if onedrive_service is not None:
            self._onedrive = onedrive_service
        else:
            try:
                self._onedrive = OneDriveService()
            except Exception:
                self._onedrive = None

    # --- compatibility helpers (legacy API) ---------------------------------
    def scan_directory(
        self,
        directory: Path,
        recursive: bool = False,
        metadata=None,
        progress_reporter=None,
        cloud_status: str = "local",
    ) -> Iterator[UserFile]:
        """Legacy API: yield UserFile objects under `directory`.

        Preserves behavior expected by older tests and code that consumes
        `FileScanner` as a generator of `UserFile`.
        """
        directory = Path(directory)
        try:
            if not directory.exists() or not directory.is_dir():
                raise DirectoryNotFoundError(f"Directory not found: {directory}")
        except Exception:
            raise DirectoryNotFoundError(f"Directory not found: {directory}")

        # Build an iterator of candidate file entries according to recursion
        if recursive:
            candidates = list(directory.rglob("*"))
        else:
            try:
                candidates = list(directory.iterdir())
            except PermissionError:
                raise
            except Exception:
                candidates = []

        # Pre-filter candidates to count total items for progress reporting
        files = [
            entry
            for entry in candidates
            if getattr(entry, "is_file", lambda: False)()
            and self._match_patterns(entry.name)
        ]

        # If a progress_reporter was provided, initialize it with total files
        try:
            total_files = len(files)
            if progress_reporter and hasattr(progress_reporter, "start_progress"):
                try:
                    progress_reporter.start_progress(total_files, "Scanning")
                except Exception:
                    # Non-fatal if progress reporter fails
                    pass
        except Exception:
            total_files = 0

        for idx, entry in enumerate(files, start=1):
            try:
                # Validate via existing logic: size, readability, and optional
                # extension filter
                if not self._validate_path_like(entry):
                    # Optionally inform progress reporter about skipped items
                    if progress_reporter and hasattr(
                        progress_reporter, "update_progress"
                    ):
                        try:
                            progress_reporter.update_progress(idx, str(entry.name))
                        except Exception:
                            pass
                    continue

                # Emit progress before yielding
                if progress_reporter and hasattr(progress_reporter, "update_progress"):
                    try:
                        progress_reporter.update_progress(idx, str(entry.name))
                    except Exception:
                        pass

                # Build the UserFile and attach cloud-status information
                user_file = UserFile(entry)
                try:
                    if self._onedrive is not None:
                        status = self._onedrive.detect_cloud_status_safe(entry)
                    else:
                        status = CloudFileStatus.LOCAL
                    # Treat detection None as LOCAL fallback for graceful
                    # degradation and tests that expect a concrete status.
                    if status is None:
                        status = CloudFileStatus.LOCAL
                    # Attach status and convenience flags expected by tests
                    user_file.cloud_status = status
                    user_file.is_cloud_only = status == CloudFileStatus.CLOUD_ONLY
                    user_file.is_local = status != CloudFileStatus.CLOUD_ONLY
                except Exception:
                    # If detection fails, leave defaults (LOCAL)
                    pass
                yield user_file
            except PermissionError:
                raise
            except Exception:
                # Skip entries that cause unexpected errors
                continue
        # Finish progress reporting if present
        if progress_reporter and hasattr(progress_reporter, "finish_progress"):
            try:
                progress_reporter.finish_progress()
            except Exception:
                pass

    def scan_recursive(
        self,
        directory: Path,
        metadata=None,
        progress_reporter=None,
        cloud_status: str = "local",
    ) -> Iterator[UserFile]:
        yield from self.scan_directory(
            directory,
            recursive=True,
            metadata=metadata,
            progress_reporter=progress_reporter,
            cloud_status=cloud_status,
        )

    def scan(self, paths_or_directory) -> List[dict] or Iterator[UserFile]:
        """Dual-purpose entry point.

        If `paths_or_directory` is a Path or string, behave as legacy API and
        return an iterator of `UserFile` objects for that directory. If it is
        an iterable of Path-like objects, compute and return a list of dicts
        with metadata (path, size, mtime, hash).
        """
        # Directory-like usage -> legacy generator
        if isinstance(paths_or_directory, (str, Path)):
            return self.scan_directory(
                Path(paths_or_directory), recursive=self.recursive
            )

        # Otherwise assume iterable of paths -> new metadata list
        results = []
        for p in paths_or_directory:
            p = Path(p)
            if not p.exists():
                self.logger.debug("Path does not exist, skipping: %s", p)
                continue
            files = (
                [p]
                if p.is_file()
                else (
                    [f for f in p.rglob("*") if f.is_file()]
                    if self.recursive
                    else [f for f in p.iterdir() if f.is_file()]
                )
            )

            for f in files:
                if not self._match_patterns(f.name):
                    continue
                try:
                    st = f.stat()
                except (OSError, PermissionError) as e:
                    self.logger.warning("Could not stat file %s: %s", f, e)
                    continue

                size = int(st.st_size)
                mtime = float(st.st_mtime)

                # Check cache
                try:
                    cached = self.db.get_cached_hash(f, size, mtime)
                except Exception:
                    cached = None

                if cached:
                    hash_value = cached
                else:
                    try:
                        # Use injected hasher if provided, otherwise default
                        # to the stream_hash implementation.
                        hasher_fn = (
                            self._hasher
                            if self._hasher is not None
                            else __import__(
                                "src.services.file_hasher", fromlist=["stream_hash"]
                            ).stream_hash
                        )
                        hash_value = hasher_fn(f, chunk_size=self.chunk_size)
                        try:
                            self.db.set_cached_hash(f, size, mtime, hash_value)
                        except Exception:
                            self.logger.debug("Failed to write cache for %s", f)
                    except Exception as e:
                        self.logger.warning("Failed to hash file %s: %s", f, e)
                        continue

                results.append(
                    {
                        "path": str(f),
                        "size": size,
                        "mtime": mtime,
                        "hash": hash_value,
                    }
                )

        return results

    # --- small compatibility helpers --------------------------------------
    def _validate_path_like(self, file_path: Path) -> bool:
        try:
            if not file_path.exists() or not file_path.is_file():
                return False
        except Exception:
            return False
        try:
            # If SUPPORTED_EXTENSIONS is set, enforce it; otherwise accept any
            # extension.
            if self.SUPPORTED_EXTENSIONS:
                if file_path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
                    return False
        except Exception:
            return False
        try:
            if not os.access(file_path, os.R_OK):
                return False
        except Exception:
            return False
        try:
            stat_result = file_path.stat()
            size = int(getattr(stat_result, "st_size", 0))
        except Exception:
            return False
        if size <= 0:
            return False
        return True

    def validate_file(self, file_path) -> bool:
        """Public compatibility method used by older tests.

        Accepts a Path or path-like and returns True when the file exists,
        is readable, has a supported extension, and has positive size.
        """
        try:
            p = file_path if isinstance(file_path, Path) else Path(file_path)
        except Exception:
            return False
        return self._validate_path_like(p)

    def _should_include_file(self, user_file, cloud_status: str) -> bool:
        if cloud_status == "all":
            return True
        elif cloud_status == "local":
            return getattr(user_file, "is_local", False)
        elif cloud_status == "cloud-only":
            return getattr(user_file, "is_cloud_only", False)
        else:
            return True

    def _match_patterns(self, name: str) -> bool:
        for pat in self.patterns:
            if fnmatch.fnmatch(name, pat):
                return True
        return False

    def get_supported_extensions(self):
        return set(self.SUPPORTED_EXTENSIONS) if self.SUPPORTED_EXTENSIONS else set()

    def is_supported_extension(self, extension: str) -> bool:
        if not self.SUPPORTED_EXTENSIONS:
            return True
        return extension.lower() in self.SUPPORTED_EXTENSIONS

#!/usr/bin/env python3
"""Clean FileScanner - single canonical implementation."""

import os
from pathlib import Path
from typing import Iterator, Optional, Set
from src.models.file import UserFile


class DirectoryNotFoundError(Exception):
    pass


class FileScanner:
    def __init__(self, extensions: Optional[Set[str]] = None):
        self.extensions = (
            {e.lower() for e in extensions} if extensions else None
        )

    def scan_directory(
        self,
        directory: Path,
        recursive: bool = True,
        metadata=None,
        progress_reporter=None,
    ) -> Iterator[UserFile]:
        try:
            directory = Path(directory).resolve()
        except Exception:
            directory = Path(directory)

        if not directory.exists():
            raise DirectoryNotFoundError(f"Directory not found: {directory}")
        if not directory.is_dir():
            raise DirectoryNotFoundError(
                f"Path is not a directory: {directory}"
            )
        if not os.access(directory, os.R_OK):
            raise PermissionError(
                f"Permission denied accessing directory: {directory}"
            )

        iterator = (
            self._scan_recursive(directory)
            if recursive
            else self._scan_non_recursive(directory)
        )

        files = list(iterator)

        def _safe_key(p):
            try:
                return str(p)
            except Exception:
                return getattr(p, "name", repr(p))

        files = sorted(files, key=_safe_key)

        if progress_reporter:
            try:
                progress_reporter.start_progress(len(files), "Scanning files")
            except Exception:
                pass

        processed = 0
        for p in files:
            if not self.validate_file(p):
                processed += 1
                continue
            try:
                try:
                    size = p.stat().st_size
                except Exception:
                    size = 0

                file_obj = UserFile(p)
                try:
                    file_obj._size = size
                except Exception:
                    pass
                try:
                    file_obj.is_local = True
                except Exception:
                    pass

                if progress_reporter:
                    try:
                        label = p.name
                    except Exception:
                        label = str(p)
                    try:
                        progress_reporter.update_progress(
                            processed, f"Processing: {label}"
                        )
                    except Exception:
                        pass

                yield file_obj
            except (FileNotFoundError, PermissionError, ValueError):
                if metadata is not None:
                    try:
                        metadata.errors.append(
                            {"file": str(p), "error": "access"}
                        )
                    except Exception:
                        pass
            finally:
                processed += 1

        if progress_reporter:
            try:
                progress_reporter.finish_progress()
            except Exception:
                pass

    def _scan_recursive(self, directory: Path):
        found = []
        try:
            if self.extensions:
                for ext in self.extensions:
                    pattern = f"*{ext}"
                    for p in directory.rglob(pattern):
                        if p.is_file():
                            found.append(p)
            else:
                for p in directory.rglob("*"):
                    if p.is_file():
                        found.append(p)
        except Exception:
            pass
        return found

    def _scan_non_recursive(self, directory: Path):
        found = []
        try:
            if self.extensions:
                for ext in self.extensions:
                    pattern = f"*{ext}"
                    for p in directory.glob(pattern):
                        if p.is_file():
                            found.append(p)
            else:
                for p in directory.iterdir():
                    if p.is_file():
                        found.append(p)
        except Exception:
            pass
        return found

    def _is_supported_file(self, file_path: Path) -> bool:
        if self.extensions:
            return file_path.suffix.lower() in self.extensions
        return True

    def validate_file(self, file_path: Path) -> bool:
        try:
            p = file_path if isinstance(file_path, Path) else Path(file_path)
            try:
                if hasattr(p, "_flavour"):
                    p = p.resolve()
            except Exception:
                pass
            if not p.exists():
                return False
            if not p.is_file():
                return False
            if not self._is_supported_file(p):
                return False
            try:
                if not os.access(p, os.R_OK):
                    return False
            except Exception:
                pass
            try:
                size = p.stat().st_size
                if size == 0:
                    return False
            except Exception:
                return False
            return True
        except Exception:
            return False

    def get_supported_extensions(self) -> Optional[Set[str]]:
        return self.extensions.copy() if self.extensions else None

    def is_supported_extension(self, extension: str) -> bool:
        if self.extensions:
            return extension.lower() in self.extensions
        return True

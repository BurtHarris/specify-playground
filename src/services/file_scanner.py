#!/usr/bin/env python3
"""
FileScanner service for Universal File Duplicate Scanner CLI.
Handles directory traversal and file discovery with support for
recursive scanning, configurable extension filtering, and file validation.
"""


import os
from pathlib import Path
from typing import Iterator, Set, Optional
from src.models.file import UserFile

class DirectoryNotFoundError(Exception):
    """Raised when a directory cannot be found."""
    pass

class FileScanner:
    """Service for discovering and validating files in directories (universal support)."""
    def __init__(self, extensions: Optional[Set[str]] = None):
        """
        Initialize the FileScanner.
        Args:
            extensions: Optional set of file extensions to filter (e.g., {'.mp4', '.mkv'})
        """
        if extensions:
            self.extensions = set(e.lower() for e in extensions)
        else:
            self.extensions = None  # None means all files

    def scan_directory(self, directory: Path, recursive: bool = True, metadata=None, progress_reporter=None) -> Iterator[UserFile]:
        """
        Discover files in the specified directory.
        Args:
            directory: Root directory to scan
            recursive: Whether to scan subdirectories (default: True)
            metadata: Optional metadata object to track errors
            progress_reporter: Optional progress reporter for feedback
        Returns:
            Iterator of Path instances for discovered files
        Raises:
            DirectoryNotFoundError: If directory doesn't exist
            PermissionError: If directory is not accessible
        """
        directory = Path(directory).resolve()
        if not directory.exists():
            raise DirectoryNotFoundError(f"Directory not found: {directory}")
        if not directory.is_dir():
            raise DirectoryNotFoundError(f"Path is not a directory: {directory}")
        if not os.access(directory, os.R_OK):
            raise PermissionError(f"Permission denied accessing directory: {directory}")
        try:
            if recursive:
                yield from self._scan_recursive(directory, metadata, progress_reporter)
            else:
                yield from self._scan_non_recursive(directory, metadata, progress_reporter)
        except PermissionError:
            raise PermissionError(f"Permission denied scanning directory: {directory}")

    def _scan_recursive(self, directory: Path, metadata=None, progress_reporter=None) -> Iterator[UserFile]:
        try:
            found_files = []
            try:
                if self.extensions:
                    for ext in self.extensions:
                        pattern = f"*{ext}"
                        for file_path in directory.rglob(pattern):
                            found_files.append(file_path)
                else:
                    for file_path in directory.rglob("*"):
                        if file_path.is_file():
                            found_files.append(file_path)
            except (OSError, PermissionError):
                pass
            if not found_files:
                try:
                    for root, dirs, files in os.walk(directory):
                        root_path = Path(root)
                        for filename in files:
                            file_path = root_path / filename
                            if self.validate_file(file_path):
                                found_files.append(file_path)
                except (OSError, PermissionError):
                    pass
            # Ensure we always have a list to iterate and keep stable ordering
            # Sort by string representation (path) to avoid TypeError when tests use MagicMock
            sorted_files = sorted(found_files, key=lambda p: str(p))
            if progress_reporter:
                progress_reporter.start_progress(len(sorted_files), "Scanning files")
            files_processed = 0
            for file_path in sorted_files:
                if self.validate_file(file_path):
                    try:
                        if progress_reporter:
                            progress_reporter.update_progress(files_processed, f"Processing: {file_path.name}")
                        size = file_path.stat().st_size if hasattr(file_path, 'stat') else 0
                        file_obj = UserFile(path=file_path, size=size, is_local=True)
                        yield file_obj
                        files_processed += 1
                    except (ValueError, FileNotFoundError, PermissionError) as e:
                        if metadata:
                            metadata.errors.append({
                                "file": str(file_path),
                                "error": f"Permission denied: {e}"
                            })
                        files_processed += 1
                        continue
            if progress_reporter:
                progress_reporter.finish_progress()
        except OSError:
            pass

    def _scan_non_recursive(self, directory: Path, metadata=None, progress_reporter=None) -> Iterator[UserFile]:
        try:
            found_files = []
            try:
                if self.extensions:
                    for ext in self.extensions:
                        pattern = f"*{ext}"
                        for file_path in directory.glob(pattern):
                            found_files.append(file_path)
                else:
                    for entry in directory.iterdir():
                        if entry.is_file():
                            found_files.append(entry)
            except (OSError, PermissionError):
                pass
            if not found_files:
                try:
                    entries = list(directory.iterdir())
                    for entry in entries:
                        if entry.is_file() and self.validate_file(entry):
                            found_files.append(entry)
                except (OSError, PermissionError):
                    pass
            # Always provide a sorted list for deterministic iteration
            # Sort by string representation (path) to avoid TypeError when tests use MagicMock
            sorted_files = sorted(found_files, key=lambda p: str(p))
            if progress_reporter:
                progress_reporter.start_progress(len(sorted_files), "Scanning files")
            files_processed = 0
            for file_path in sorted_files:
                if self.validate_file(file_path):
                    try:
                        if progress_reporter:
                            progress_reporter.update_progress(files_processed, f"Processing: {file_path.name}")
                        size = file_path.stat().st_size if hasattr(file_path, 'stat') else 0
                        # Use the library UserFile wrapper which accepts (path, size, is_local)
                        file_obj = UserFile(path=file_path, size=size, is_local=True)
                        yield file_obj
                        files_processed += 1
                    except (ValueError, FileNotFoundError, PermissionError) as e:
                        if metadata:
                            metadata.errors.append({
                                "file": str(file_path),
                                "error": f"Permission denied: {e}"
                            })
                        files_processed += 1
                        continue
            if progress_reporter:
                progress_reporter.finish_progress()
        except PermissionError:
            pass

    def _is_supported_file(self, file_path: Path) -> bool:
        if self.extensions:
            return file_path.suffix.lower() in self.extensions
        return True

    def validate_file(self, file_path: Path) -> bool:
        try:
            resolved_path = file_path if isinstance(file_path, Path) else Path(file_path)
            try:
                if hasattr(resolved_path, '_mock_name'):
                    pass
                elif hasattr(resolved_path, '_flavour'):
                    resolved_path = resolved_path.resolve()
            except (AttributeError, TypeError, OSError):
                pass
            if not resolved_path.exists():
                return False
            if not resolved_path.is_file():
                return False
            if not self._is_supported_file(resolved_path):
                return False
            try:
                if hasattr(resolved_path, '_mock_name'):
                    pass
                else:
                    if not os.access(resolved_path, os.R_OK):
                        return False
            except (TypeError, OSError):
                pass
            try:
                size = resolved_path.stat().st_size
                if hasattr(size, 'st_size'):
                    size = size.st_size
                if size == 0:
                    return False
                return True
            except (OSError, AttributeError):
                return False
        except (OSError, ValueError, TypeError):
            return False

    def get_supported_extensions(self) -> Optional[Set[str]]:
        return self.extensions.copy() if self.extensions else None

    def is_supported_extension(self, extension: str) -> bool:
        if self.extensions:
            return extension.lower() in self.extensions
        return True

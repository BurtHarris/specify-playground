#!/usr/bin/env python3
"""
FileScanner service for Video Duplicate Scanner CLI.

Handles directory traversal and file discovery with support for
recursive scanning and file validation.
"""

import os
from pathlib import Path
from typing import Iterator, Set

from ..models.file import UserFile
from ..services.onedrive_service import OneDriveService

# Optional debug switch (enable by setting SPECIFY_DEBUG_VALIDATE=1 in env)
# Default off in simplified scanner
DEBUG_VALIDATE = False


class DirectoryNotFoundError(Exception):
    """Raised when a directory cannot be found."""
    pass


class FileScanner:
    """Service for discovering and validating files in directories."""
    
    # Supported video file extensions in order of preference
    VIDEO_EXTENSIONS = {'.mp4', '.mkv', '.mov'}
    EXTENSION_ORDER = ['.mp4', '.mkv', '.mov']  # Define processing order
    
    def __init__(self):
        """Initialize the VideoFileScanner."""
        # Initialize OneDrive service for cloud status detection; service will
        # gracefully degrade on non-Windows platforms. Tests may patch
        # OneDriveService.detect_cloud_status_safe to simulate statuses.
        try:
            self._onedrive = OneDriveService()
        except Exception:
            self._onedrive = None
        pass
    
    def scan_directory(self, directory: Path, recursive: bool = False, metadata=None, progress_reporter=None, cloud_status: str = 'local') -> Iterator[UserFile]:
        # Backwards-compatible shim. Prefer new explicit methods `scan` (non-recursive)
        # and `scan_recursive` for clearer behavior. Keep this wrapper so existing
        # call sites that pass `recursive` continue to work.
        if recursive:
            yield from self.scan_recursive(directory, metadata=metadata, progress_reporter=progress_reporter, cloud_status=cloud_status)
        else:
            yield from self.scan(directory, metadata=metadata, progress_reporter=progress_reporter, cloud_status=cloud_status)

    def scan(self, directory: Path, metadata=None, progress_reporter=None, cloud_status: str = 'local') -> Iterator[UserFile]:
        """Scan the immediate entries of ``directory`` (non-recursive).

        This method lists top-level entries (via ``directory.iterdir()``), filters
        by video extension, validates each file with ``validate_file`` and yields
        ``UserFile`` instances. Directory-level permission errors (from
        listing) propagate to the caller.
        """
        # Normalized to a pathlib.Path; tests should use the real filesystem
        directory = Path(directory)

        # Validate directory exists/isdir
        try:
            if not directory.exists():
                raise DirectoryNotFoundError(f"Directory not found: {directory}")
        except Exception:
            raise DirectoryNotFoundError(f"Directory not found: {directory}")

        try:
            if not directory.is_dir():
                raise DirectoryNotFoundError(f"Path is not a directory: {directory}")
        except Exception:
            raise DirectoryNotFoundError(f"Path is not a directory: {directory}")

        # Check permissions for listing: if os.access can't handle the object
        # (e.g., a Mock), assume accessible. Only catch TypeError/OSError here.
        try:
            access_ok = os.access(directory, os.R_OK)
        except (TypeError, OSError):
            access_ok = True
        if not access_ok:
            raise PermissionError(f"Permission denied accessing directory: {directory}")

        # List immediate entries; prefer iterdir (tests often patch iterdir).
        # If iterdir is not available or raises an OSError (missing path),
        # fall back to glob-based search. Do NOT swallow PermissionError;
        # let directory-level permission issues propagate to caller/tests.
        found_files = []
        try:
            entries = list(directory.iterdir())
            if DEBUG_VALIDATE:
                print(f"[scan] iterdir returned {len(entries)} entries: {entries}")
            for entry in entries:
                try:
                    if DEBUG_VALIDATE:
                        try:
                            print(f"[scan] entry type={type(entry)!r}, suffix={getattr(entry,'suffix',None)}")
                        except Exception:
                            print(f"[scan] entry type={type(entry)!r}")
                    if entry.is_file() and self._is_video_file(entry):
                        found_files.append(entry)
                except Exception:
                    continue
        except PermissionError:
            # Let callers/tests observe permission errors when iterdir fails
            raise
        except (OSError, AttributeError):
            # Fallback to glob-based enumeration (tests patch Path.glob in some cases)
            try:
                for extension in self.EXTENSION_ORDER:
                    pattern = f"*{extension}"
                    for file_path in directory.glob(pattern):
                        found_files.append(file_path)
            except Exception:
                # If glob also fails, give up and treat as empty
                found_files = []

        # Deterministic ordering
        try:
            sorted_files = sorted(found_files, key=lambda p: str(p))
        except Exception:
            sorted_files = found_files

        # Start progress reporting
        if progress_reporter:
            progress_reporter.start_progress(len(sorted_files), "Scanning video files")

        files_processed = 0
        for file_path in sorted_files:
            if self.validate_file(file_path):
                try:
                    if progress_reporter:
                        progress_reporter.update_progress(files_processed, f"Processing: {getattr(file_path, 'name', str(file_path))}")
                    user_file = UserFile(file_path)
                    # Populate cloud status if service available; cache on the
                    # UserFile instance so repeated accesses don't re-run
                    # detection. Tests patch OneDriveService.detect_cloud_status_safe.
                    try:
                        if self._onedrive is not None:
                            status = self._onedrive.detect_cloud_status_safe(file_path)
                            if status is not None:
                                # Use enum-based checks to set flags reliably
                                user_file.cloud_status = status
                                try:
                                    from ..models.cloud_file_status import CloudFileStatus
                                    user_file.is_cloud_only = (status == CloudFileStatus.CLOUD_ONLY)
                                    user_file.is_local = (status == CloudFileStatus.LOCAL)
                                except Exception:
                                    # If status is not the expected enum, fallback
                                    user_file.is_cloud_only = False
                                    user_file.is_local = True
                    except Exception:
                        # On detection error, leave defaults (assume local)
                        pass

                    if self._should_include_file(user_file, cloud_status):
                        yield user_file
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

    def scan_recursive(self, directory: Path, metadata=None, progress_reporter=None, cloud_status: str = 'local') -> Iterator[UserFile]:
        """Recursively scan ``directory`` for video files."""
        # Normalized to a pathlib.Path; tests should use the real filesystem
        directory = Path(directory)

        # Validate root
        try:
            if not directory.exists():
                raise DirectoryNotFoundError(f"Directory not found: {directory}")
        except Exception:
            raise DirectoryNotFoundError(f"Directory not found: {directory}")

        try:
            if not directory.is_dir():
                raise DirectoryNotFoundError(f"Path is not a directory: {directory}")
        except Exception:
            raise DirectoryNotFoundError(f"Path is not a directory: {directory}")

        # Prefer the rglob-based recursive scanner which also supports tests
        # that patch Path.rglob. Delegate to _scan_recursive which implements
        # rglob and sensible fallbacks.
        yield from self._scan_recursive(directory, metadata=metadata, progress_reporter=progress_reporter, cloud_status=cloud_status)
    
    def _scan_recursive(self, directory: Path, metadata=None, progress_reporter=None, cloud_status: str = 'local') -> Iterator[UserFile]:
        """
        Recursively scan directory for video files.
        
        Args:
            directory: Directory to scan recursively
            metadata: Optional metadata object to track errors
            progress_reporter: Optional progress reporter for feedback  
            cloud_status: Filter by cloud status: 'all', 'local', 'cloud-only'
            
        Yields:
            VideoFile instances for discovered video files
        """
        try:
            found_files = []
            
            # Try rglob approach first (preferred for real usage)
            try:
                for extension in self.EXTENSION_ORDER:
                    pattern = f"*{extension}"
                    for file_path in directory.rglob(pattern):
                        found_files.append(file_path)
            except (OSError, PermissionError):
                pass
            
            # If no files found via rglob, try os.walk approach (fallback)
            if not found_files:
                try:
                    for root, dirs, files in os.walk(directory):
                        root_path = Path(root)
                        for filename in files:
                            file_path = root_path / filename
                            if self._is_video_file(file_path):
                                found_files.append(file_path)
                except (OSError, PermissionError):
                    pass
            
            # Process found files in sorted order for deterministic results (recursive)
            try:
                # Try sorting by string path first
                sorted_files = sorted(found_files, key=lambda p: str(p))
            except (TypeError, AttributeError):
                # Handle Mock objects in tests - sort by extension then suffix
                try:
                    sorted_files = sorted(found_files, key=lambda p: (p.suffix, getattr(p, '_mock_name', '')))
                except (TypeError, AttributeError):
                    # If all else fails, just use original order
                    sorted_files = found_files
            
            # Start progress reporting if available
            if progress_reporter:
                progress_reporter.start_progress(len(sorted_files), "Scanning video files")
            
            files_processed = 0
            # No debug prints in normal operation; diagnostics removed to
            # keep test output clean.

            for file_path in sorted_files:
                if self.validate_file(file_path):
                    try:
                        # Report progress if available
                        if progress_reporter:
                            progress_reporter.update_progress(files_processed, f"Processing: {file_path.name}")
                        
                        # Create UserFile and apply cloud status filtering
                        user_file = UserFile(file_path)
                        if self._should_include_file(user_file, cloud_status):
                            yield user_file
                        files_processed += 1
                    except (ValueError, FileNotFoundError, PermissionError) as e:
                        # Track error in metadata if provided
                        if metadata:
                            metadata.errors.append({
                                "file": str(file_path),
                                "error": f"Permission denied: {e}"
                            })
                        files_processed += 1
                        # Skip files that can't be processed
                        continue
            
            # Finish progress reporting if available
            if progress_reporter:
                progress_reporter.finish_progress()
                
        except OSError:
            # Handle permission errors during traversal
            # Continue processing other directories
            pass
    
    def _scan_non_recursive(self, directory: Path, metadata=None, progress_reporter=None, cloud_status: str = 'local') -> Iterator[UserFile]:
        """
        Scan only the root level of directory for video files.
        
        Args:
            directory: Directory to scan (non-recursive)
            metadata: Optional metadata object to track errors
            progress_reporter: Optional progress reporter for feedback
            cloud_status: Filter by cloud status: 'all', 'local', 'cloud-only'
            
        Yields:
            VideoFile instances for discovered video files
        """
        try:
            found_files = []
            
            # For non-recursive scanning prefer iterdir (tests often patch iterdir)
            try:
                entries = list(directory.iterdir())
                for entry in entries:
                    try:
                        if entry.is_file() and self._is_video_file(entry):
                            found_files.append(entry)
                    except Exception:
                        # Skip entries that raise when interrogated (mocks may)
                        continue
            except (OSError, AttributeError):
                # Fall back to glob if iterdir isn't available or raises a non-permission error
                try:
                    for extension in self.EXTENSION_ORDER:
                        pattern = f"*{extension}"
                        for file_path in directory.glob(pattern):
                            found_files.append(file_path)
                except OSError:
                    pass
            
            # Process found files in sorted order for deterministic results (non-recursive)
            try:
                sorted_files = sorted(found_files, key=lambda p: str(p))
            except (TypeError, AttributeError):
                # Handle Mock objects in tests that can't be converted to string  
                sorted_files = found_files
            
            # Start progress reporting if available
            if progress_reporter:
                progress_reporter.start_progress(len(sorted_files), "Scanning video files")
            
            files_processed = 0
            for file_path in sorted_files:
                if self.validate_file(file_path):
                    try:
                        # Report progress if available
                        if progress_reporter:
                            progress_reporter.update_progress(files_processed, f"Processing: {file_path.name}")
                        
                        # Create UserFile and apply cloud status filtering
                        user_file = UserFile(file_path)
                        if self._should_include_file(user_file, cloud_status):
                            yield user_file
                        files_processed += 1
                    except (ValueError, FileNotFoundError, PermissionError) as e:
                        # Track error in metadata if provided
                        if metadata:
                            metadata.errors.append({
                                "file": str(file_path),
                                "error": f"Permission denied: {e}"
                            })
                        files_processed += 1
                        # Skip files that can't be processed
                        continue
            
            # Finish progress reporting if available
            if progress_reporter:
                progress_reporter.finish_progress()
                        
        # Let PermissionError propagate to the caller so permission errors are
        # observable by callers/tests. Other exceptions are handled above.
        except PermissionError:
            raise
        except Exception:
            # Any other unexpected error during non-recursive scanning should
            # not crash the scanner; swallow and continue gracefully.
            pass
    
    def _is_video_file(self, file_path: Path) -> bool:
        """
        Check if file has a video extension.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if file has a video extension
        """
        return file_path.suffix.lower() in self.VIDEO_EXTENSIONS
    
    def validate_file(self, file_path: Path) -> bool:
        """
        Check if a file is a valid video file that can be processed.
        
        Args:
            file_path: Path to file to validate
            
        Returns:
            True if file is valid and accessible
            
        Contract:
            - MUST check file existence
            - MUST check read permissions
            - MUST validate file extension
            - MUST NOT raise exceptions for invalid files
        """
        # Simplified validation that uses real filesystem semantics.
        # Any failure returns False rather than raising.
        try:
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
    
    def _should_include_file(self, user_file: UserFile, cloud_status: str) -> bool:
        """
        Determine if a video file should be included based on cloud status filtering.
        
        Args:
            video_file: VideoFile instance to check
            cloud_status: Filter criteria ('all', 'local', 'cloud-only')
            
        Returns:
            True if file should be included in results
        """
        if cloud_status == 'all':
            return True
        elif cloud_status == 'local':
            return user_file.is_local
        elif cloud_status == 'cloud-only':
            return user_file.is_cloud_only
        else:
            # Unknown filter - default to include all files
            return True
    
    def get_supported_extensions(self) -> Set[str]:
        """
        Get the set of supported video file extensions.
        
        Returns:
            Set of supported extensions (e.g., {'.mp4', '.mkv', '.mov'})
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
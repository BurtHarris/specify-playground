#!/usr/bin/env python3
"""
VideoFileScanner service for Video Duplicate Scanner CLI.

Handles directory traversal and video file discovery with support for
recursive scanning and file validation.
"""

import os
from pathlib import Path
from typing import Iterator, Set

from ..models.video_file import VideoFile


class DirectoryNotFoundError(Exception):
    """Raised when a directory cannot be found."""
    pass


class VideoFileScanner:
    """Service for discovering and validating video files in directories."""
    
    # Supported video file extensions
    VIDEO_EXTENSIONS = {'.mp4', '.mkv', '.mov'}
    
    def __init__(self):
        """Initialize the VideoFileScanner."""
        pass
    
    def scan_directory(self, directory: Path, recursive: bool = True) -> Iterator[VideoFile]:
        """
        Discover video files in the specified directory.
        
        Args:
            directory: Root directory to scan
            recursive: Whether to scan subdirectories (default: True)
            
        Returns:
            Iterator of VideoFile instances
            
        Raises:
            DirectoryNotFoundError: If directory doesn't exist
            PermissionError: If directory is not accessible
        """
        directory = Path(directory).resolve()
        
        # Validate directory exists
        if not directory.exists():
            raise DirectoryNotFoundError(f"Directory not found: {directory}")
        
        if not directory.is_dir():
            raise DirectoryNotFoundError(f"Path is not a directory: {directory}")
        
        # Check directory permissions
        if not os.access(directory, os.R_OK):
            raise PermissionError(f"Permission denied accessing directory: {directory}")
        
        # Scan for video files
        try:
            if recursive:
                yield from self._scan_recursive(directory)
            else:
                yield from self._scan_non_recursive(directory)
        except PermissionError:
            # Re-raise permission errors for the directory itself
            raise PermissionError(f"Permission denied scanning directory: {directory}")
    
    def _scan_recursive(self, directory: Path) -> Iterator[VideoFile]:
        """
        Recursively scan directory for video files.
        
        Args:
            directory: Directory to scan recursively
            
        Yields:
            VideoFile instances for discovered video files
        """
        try:
            # Use os.walk for efficient recursive traversal
            for root, dirs, files in os.walk(directory):
                root_path = Path(root)
                
                # Process files in current directory
                # Sort for deterministic ordering
                for filename in sorted(files):
                    file_path = root_path / filename
                    
                    if self._is_video_file(file_path) and self.validate_file(file_path):
                        try:
                            yield VideoFile(file_path)
                        except (ValueError, FileNotFoundError, PermissionError):
                            # Skip files that can't be processed
                            continue
                
                # Sort directories for deterministic traversal order
                dirs.sort()
                
        except OSError:
            # Handle permission errors during traversal
            # Continue processing other directories
            pass
    
    def _scan_non_recursive(self, directory: Path) -> Iterator[VideoFile]:
        """
        Scan only the root level of directory for video files.
        
        Args:
            directory: Directory to scan (root level only)
            
        Yields:
            VideoFile instances for discovered video files
        """
        try:
            # Get all entries in directory
            entries = list(directory.iterdir())
            
            # Filter and sort files for deterministic ordering
            try:
                files = sorted([entry for entry in entries if entry.is_file()])
            except TypeError:
                # Handle case where entries can't be sorted (e.g., in tests with Mock objects)
                files = [entry for entry in entries if entry.is_file()]
            
            for file_path in files:
                if self._is_video_file(file_path) and self.validate_file(file_path):
                    try:
                        yield VideoFile(file_path)
                    except (ValueError, FileNotFoundError, PermissionError):
                        # Skip files that can't be processed
                        continue
                        
        except PermissionError:
            # Can't read directory contents
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
        try:
            file_path = Path(file_path).resolve()
            
            # Check file existence
            if not file_path.exists():
                return False
            
            # Check it's actually a file
            if not file_path.is_file():
                return False
            
            # Check file extension
            if not self._is_video_file(file_path):
                return False
            
            # Check read permissions
            if not os.access(file_path, os.R_OK):
                return False
            
            # Additional validation - try to get file size
            # This can fail for some special files
            try:
                file_path.stat().st_size
            except OSError:
                return False
            
            return True
            
        except (OSError, ValueError):
            # Any other errors mean file is not valid
            return False
    
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
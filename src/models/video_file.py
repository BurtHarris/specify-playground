#!/usr/bin/env python3
"""
VideoFile model for Video Duplicate Scanner CLI.

Represents a single video file in the filesystem with lazy hash computation
and validation capabilities.
"""

import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional


class VideoFile:
    """Represents a single video file in the filesystem."""
    
    # Supported video extensions
    SUPPORTED_EXTENSIONS = {'.mp4', '.mkv', '.mov'}
    
    def __init__(self, path: Path):
        """
        Initialize a VideoFile instance.
        
        Args:
            path: Path to the video file
            
        Raises:
            ValueError: If path is invalid or file is not a supported video format
            FileNotFoundError: If file does not exist
            PermissionError: If file is not readable
        """
        self._path = Path(path).resolve()  # Store as absolute path
        self._size: Optional[int] = None
        self._hash: Optional[str] = None
        self._last_modified: Optional[datetime] = None
        
        # Validate file immediately
        self._validate_file()
    
    @property
    def path(self) -> Path:
        """Absolute path to the video file."""
        return self._path
    
    @property
    def size(self) -> int:
        """File size in bytes (computed lazily)."""
        if self._size is None:
            self._size = self._path.stat().st_size
        return self._size
    
    @property
    def hash(self) -> Optional[str]:
        """Blake2b hash of the file (computed lazily when needed)."""
        return self._hash
    
    @property
    def extension(self) -> str:
        """File extension in lowercase."""
        return self._path.suffix.lower()
    
    @property
    def last_modified(self) -> datetime:
        """File modification timestamp (computed lazily)."""
        if self._last_modified is None:
            timestamp = self._path.stat().st_mtime
            self._last_modified = datetime.fromtimestamp(timestamp)
        return self._last_modified
    
    def _validate_file(self) -> None:
        """
        Validate that the file exists, is readable, and is a supported video format.
        
        Raises:
            FileNotFoundError: If file does not exist
            PermissionError: If file is not readable
            ValueError: If file is not a supported video format
        """
        if not self._path.exists():
            raise FileNotFoundError(f"Video file not found: {self._path}")
        
        if not self._path.is_file():
            raise ValueError(f"Path is not a file: {self._path}")
        
        if not self.is_accessible():
            raise PermissionError(f"Cannot read video file: {self._path}")
        
        if self.extension not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported video format: {self.extension}. "
                f"Supported formats: {', '.join(sorted(self.SUPPORTED_EXTENSIONS))}"
            )
    
    def compute_hash(self) -> str:
        """
        Compute and cache the Blake2b hash of the file.
        
        Uses streaming to handle large files efficiently.
        
        Returns:
            Blake2b hash as hexadecimal string
            
        Raises:
            PermissionError: If file cannot be read
            OSError: If file reading fails
        """
        if self._hash is not None:
            return self._hash
        
        hasher = hashlib.blake2b()
        
        try:
            with open(self._path, 'rb') as f:
                # Read in chunks to handle large files efficiently
                chunk_size = 65536  # 64KB chunks
                while chunk := f.read(chunk_size):
                    hasher.update(chunk)
        except PermissionError:
            raise PermissionError(f"Permission denied reading file: {self._path}")
        except OSError as e:
            raise OSError(f"Error reading file {self._path}: {e}")
        
        self._hash = hasher.hexdigest()
        return self._hash
    
    def is_accessible(self) -> bool:
        """
        Check if the file can be read.
        
        Returns:
            True if file is readable, False otherwise
        """
        try:
            with open(self._path, 'rb') as f:
                # Try to read first byte
                f.read(1)
            return True
        except (PermissionError, OSError):
            return False
    
    def get_filename_without_extension(self) -> str:
        """
        Get filename without extension for fuzzy matching.
        
        Returns:
            Filename without extension
        """
        return self._path.stem
    
    def refresh_metadata(self) -> None:
        """
        Refresh cached file metadata (size, modification time).
        
        Useful if the file may have changed on disk.
        """
        self._size = None
        self._last_modified = None
        # Don't refresh hash as file content shouldn't change
    
    def __str__(self) -> str:
        """String representation showing file path."""
        return str(self._path)
    
    def __repr__(self) -> str:
        """Detailed string representation for debugging."""
        return f"VideoFile(path={self._path!r}, size={self.size}, extension='{self.extension}')"
    
    def __eq__(self, other) -> bool:
        """
        Equality based on file path.
        
        Args:
            other: Another VideoFile instance
            
        Returns:
            True if both represent the same file path
        """
        if not isinstance(other, VideoFile):
            return False
        return self._path == other._path
    
    def __hash__(self) -> int:
        """Hash based on file path for use in sets and dicts."""
        return hash(self._path)
    
    def __lt__(self, other) -> bool:
        """Ordering based on file path for sorting."""
        if not isinstance(other, VideoFile):
            return NotImplemented
        return str(self._path) < str(other._path)
    
    def to_dict(self) -> dict:
        """
        Convert to dictionary representation for JSON export.
        
        Returns:
            Dictionary with file information
        """
        return {
            'path': str(self._path),
            'size': self.size,
            'extension': self.extension,
            'last_modified': self.last_modified.isoformat() + 'Z',
            'hash': self._hash  # May be None if not computed
        }
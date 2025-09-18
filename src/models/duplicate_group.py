#!/usr/bin/env python3
"""
DuplicateGroup model for Video Duplicate Scanner CLI.

Represents a group of video files that have identical content (same hash).
"""

from typing import Iterator, List, Optional, Set
from pathlib import Path

from .video_file import VideoFile


class DuplicateGroup:
    """Represents a group of video files with identical content."""
    
    def __init__(self, hash_value: str, files: Optional[List[VideoFile]] = None):
        """
        Initialize a DuplicateGroup.
        
        Args:
            hash_value: The common hash shared by all files in this group
            files: Optional initial list of VideoFile objects
            
        Raises:
            ValueError: If hash_value is empty or files have different hashes
        """
        if not hash_value or not hash_value.strip():
            raise ValueError("Hash value cannot be empty")
        
        self._hash_value = hash_value.strip()
        self._files: Set[VideoFile] = set()
        
        if files:
            for file in files:
                self.add_file(file)
    
    @property
    def hash_value(self) -> str:
        """The hash value shared by all files in this group."""
        return self._hash_value
    
    @property
    def files(self) -> List[VideoFile]:
        """List of video files in this group, sorted by path."""
        return sorted(self._files)
    
    @property
    def file_count(self) -> int:
        """Number of files in this group."""
        return len(self._files)
    
    @property
    def is_empty(self) -> bool:
        """True if this group contains no files."""
        return len(self._files) == 0
    
    @property
    def is_duplicate_group(self) -> bool:
        """True if this group contains 2 or more files (actual duplicates)."""
        return len(self._files) >= 2
    
    @property
    def total_size(self) -> int:
        """Total size of all files in this group."""
        return sum(file.size for file in self._files)
    
    @property
    def file_size(self) -> int:
        """Size of each individual file in this group (all files are identical)."""
        return next(iter(self._files)).size if self._files else 0
    
    @property
    def wasted_space(self) -> int:
        """
        Amount of disk space wasted by duplicates.
        
        This is the total size minus the size of one copy.
        Returns 0 if there are fewer than 2 files.
        """
        if not self.is_duplicate_group:
            return 0
        
        # All files have the same size (same content), so use any file's size
        single_file_size = self.file_size
        return single_file_size * (len(self._files) - 1)
    
    @property
    def paths(self) -> List[Path]:
        """List of file paths in this group, sorted."""
        return [file.path for file in sorted(self._files)]
    
    def add_file(self, file: VideoFile) -> None:
        """
        Add a file to this group.
        
        Args:
            file: VideoFile to add
            
        Raises:
            ValueError: If file's hash doesn't match group hash
            TypeError: If file is not a VideoFile instance
        """
        if not isinstance(file, VideoFile):
            raise TypeError("Can only add VideoFile instances")
        
        # Compute hash if needed and verify it matches
        file_hash = file.compute_hash()
        if file_hash != self._hash_value:
            raise ValueError(
                f"File hash '{file_hash}' doesn't match group hash '{self._hash_value}'"
            )
        
        self._files.add(file)
    
    def remove_file(self, file: VideoFile) -> bool:
        """
        Remove a file from this group.
        
        Args:
            file: VideoFile to remove
            
        Returns:
            True if file was removed, False if file wasn't in group
        """
        try:
            self._files.remove(file)
            return True
        except KeyError:
            return False
    
    def remove_file_by_path(self, path: Path) -> bool:
        """
        Remove a file from this group by its path.
        
        Args:
            path: Path of file to remove
            
        Returns:
            True if file was removed, False if no matching file found
        """
        path = Path(path).resolve()
        
        for file in self._files:
            if file.path == path:
                self._files.remove(file)
                return True
        
        return False
    
    def contains_file(self, file: VideoFile) -> bool:
        """
        Check if a file is in this group.
        
        Args:
            file: VideoFile to check
            
        Returns:
            True if file is in this group
        """
        return file in self._files
    
    def contains_path(self, path: Path) -> bool:
        """
        Check if a file path is in this group.
        
        Args:
            path: Path to check
            
        Returns:
            True if path is in this group
        """
        path = Path(path).resolve()
        return any(file.path == path for file in self._files)
    
    def get_file_by_path(self, path: Path) -> Optional[VideoFile]:
        """
        Get a file from this group by its path.
        
        Args:
            path: Path to find
            
        Returns:
            VideoFile if found, None otherwise
        """
        path = Path(path).resolve()
        
        for file in self._files:
            if file.path == path:
                return file
        
        return None
    
    def merge_group(self, other: 'DuplicateGroup') -> None:
        """
        Merge another duplicate group into this one.
        
        Args:
            other: Another DuplicateGroup to merge
            
        Raises:
            ValueError: If groups have different hash values
            TypeError: If other is not a DuplicateGroup
        """
        if not isinstance(other, DuplicateGroup):
            raise TypeError("Can only merge with another DuplicateGroup")
        
        if other._hash_value != self._hash_value:
            raise ValueError(
                f"Cannot merge groups with different hashes: "
                f"'{self._hash_value}' vs '{other._hash_value}'"
            )
        
        # Add all files from other group
        self._files.update(other._files)
    
    def get_oldest_file(self) -> Optional[VideoFile]:
        """
        Get the file with the oldest modification time.
        
        Returns:
            VideoFile with oldest modification time, or None if group is empty
        """
        if not self._files:
            return None
        
        return min(self._files, key=lambda f: f.last_modified)
    
    def get_newest_file(self) -> Optional[VideoFile]:
        """
        Get the file with the newest modification time.
        
        Returns:
            VideoFile with newest modification time, or None if group is empty
        """
        if not self._files:
            return None
        
        return max(self._files, key=lambda f: f.last_modified)
    
    def get_smallest_path(self) -> Optional[VideoFile]:
        """
        Get the file with the shortest path (useful for finding the "original").
        
        Returns:
            VideoFile with shortest path, or None if group is empty
        """
        if not self._files:
            return None
        
        return min(self._files, key=lambda f: len(str(f.path)))
    
    def __len__(self) -> int:
        """Number of files in this group."""
        return len(self._files)
    
    def __iter__(self) -> Iterator[VideoFile]:
        """Iterate over files in this group."""
        return iter(sorted(self._files))
    
    def __contains__(self, file: VideoFile) -> bool:
        """Check if file is in this group."""
        return file in self._files
    
    def __str__(self) -> str:
        """String representation showing hash and file count."""
        return f"DuplicateGroup(hash={self._hash_value[:12]}..., files={len(self._files)})"
    
    def __repr__(self) -> str:
        """Detailed string representation for debugging."""
        return (
            f"DuplicateGroup(hash_value='{self._hash_value}', "
            f"file_count={len(self._files)}, "
            f"total_size={self.total_size}, "
            f"wasted_space={self.wasted_space})"
        )
    
    def __eq__(self, other) -> bool:
        """
        Equality based on hash value and file set.
        
        Args:
            other: Another DuplicateGroup
            
        Returns:
            True if both groups have same hash and same files
        """
        if not isinstance(other, DuplicateGroup):
            return False
        
        return (
            self._hash_value == other._hash_value and
            self._files == other._files
        )
    
    def __hash__(self) -> int:
        """Hash based on group hash value for use in sets and dicts."""
        return hash(self._hash_value)
    
    def to_dict(self) -> dict:
        """
        Convert to dictionary representation for JSON/YAML export.
        
        Returns:
            Dictionary with group information
        """
        return {
            'hash': self._hash_value,
            'file_count': self.file_count,
            'total_size': self.total_size,
            'wasted_space': self.wasted_space,
            'files': [file.to_dict() for file in sorted(self._files)]
        }
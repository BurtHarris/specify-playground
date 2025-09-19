#!/usr/bin/env python3
"""
PotentialMatchGroup model for Video Duplicate Scanner CLI.

Represents a group of video files that have similar names but different content.
These may be the same video in different formats/qualities.
"""

from typing import Dict, Iterator, List, Optional, Set, Tuple
from pathlib import Path

from .file import UserFile
try:
    from .user_file import UserFile as _ConcreteUserFile
except Exception:
    _ConcreteUserFile = None


class PotentialMatchGroup:
    """Represents a group of files with similar names but different content."""
    
    def __init__(self, base_name: str, similarity_threshold: float = 0.8, files: Optional[List[UserFile]] = None):
        """
        Initialize a PotentialMatchGroup.

        Args:
            base_name: The common base name that files in this group share similarity with
            similarity_threshold: Minimum similarity score for files to be in this group (0.0-1.0)
            files: Optional initial list of UserFile objects

        Raises:
            ValueError: If base_name is empty or similarity_threshold is invalid
        """
        if not base_name or not base_name.strip():
            raise ValueError("Base name cannot be empty")

        if not (0.0 <= similarity_threshold <= 1.0):
            raise ValueError("Similarity threshold must be between 0.0 and 1.0")

        self._base_name = base_name.strip()
        self._similarity_threshold = similarity_threshold
        self._files = set()
        self._similarity_scores = {}

        if files:
            for file in files:
                self.add_file(file)
    
    @property
    def base_name(self) -> str:
        """The base name that files in this group are similar to."""
        return self._base_name
    
    @property
    def similarity_threshold(self) -> float:
        """Minimum similarity score required for files in this group."""
        return self._similarity_threshold
    
    @property
    def files(self) -> List[UserFile]:
        """List of files in this group, sorted by similarity score (descending)."""
        return sorted(
            self._files, 
            key=lambda f: self._similarity_scores.get(f, 0.0), 
            reverse=True
        )
    
    @property
    def file_count(self) -> int:
        """Number of files in this group."""
        return len(self._files)
    
    @property
    def is_empty(self) -> bool:
        """True if this group contains no files."""
        return len(self._files) == 0
    
    @property
    def is_potential_match_group(self) -> bool:
        """True if this group contains 2 or more files (potential matches)."""
        return len(self._files) >= 2
    
    @property
    def extensions(self) -> Set[str]:
        """Set of file extensions present in this group."""
        return {file.extension for file in self._files}
    
    @property
    def has_multiple_extensions(self) -> bool:
        """True if files in this group have different extensions."""
        return len(self.extensions) > 1
    
    @property
    def total_size(self) -> int:
        """Total size of all files in this group."""
        return sum(file.size for file in self._files)
    
    @property
    def average_similarity(self) -> float:
        """Average similarity score of all files in this group."""
        if not self._files:
            return 0.0
        
        return sum(self._similarity_scores.values()) / len(self._files)
    
    @property
    def similarity_score(self) -> float:
        """Alias for average_similarity for backward compatibility."""
        return self.average_similarity
    
    @property
    def paths(self) -> List[Path]:
        """List of file paths in this group, sorted by similarity score."""
        return [file.path for file in self.files]
    
    def add_file(self, file: UserFile, similarity_score: Optional[float] = None) -> None:
        """
        Add a file to this group.
        
        Args:
            file: UserFile to add
            similarity_score: Similarity score between file and base_name.
                            If None, it will be computed using fuzzy matching.
            
        Raises:
            ValueError: If similarity score is below threshold
            TypeError: If file is not a UserFile instance
        """
        # Accept either the compatibility wrapper UserFile or the concrete implementation
        if not (isinstance(file, UserFile) or (_ConcreteUserFile is not None and isinstance(file, _ConcreteUserFile))):
            raise TypeError("Can only add UserFile instances")
        
        # Compute similarity score if not provided
        if similarity_score is None:
            similarity_score = self._compute_similarity(file)
        
        if similarity_score < self._similarity_threshold:
            raise ValueError(
                f"Similarity score {similarity_score:.3f} is below threshold "
                f"{self._similarity_threshold:.3f} for file: {file.path}"
            )
        
        self._files.add(file)
        self._similarity_scores[file] = similarity_score
    
    def remove_file(self, file: UserFile) -> bool:
        """
        Remove a file from this group.
        
        Args:
            file: UserFile to remove
            
        Returns:
            True if file was removed, False if file wasn't in group
        """
        try:
            self._files.remove(file)
            del self._similarity_scores[file]
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
                del self._similarity_scores[file]
                return True
        
        return False
    
    def contains_file(self, file: UserFile) -> bool:
        """
        Check if a file is in this group.
        
        Args:
            file: UserFile to check
            
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
    
    def get_file_by_path(self, path: Path) -> Optional[UserFile]:
        """
        Get a file from this group by its path.
        
        Args:
            path: Path to find
            
        Returns:
            UserFile if found, None otherwise
        """
        path = Path(path).resolve()
        
        for file in self._files:
            if file.path == path:
                return file
        
        return None
    
    def get_similarity_score(self, file: UserFile) -> Optional[float]:
        """
        Get the similarity score for a file in this group.
        
        Args:
            file: UserFile to get score for
            
        Returns:
            Similarity score if file is in group, None otherwise
        """
        return self._similarity_scores.get(file)
    
    def get_files_by_extension(self, extension: str) -> List[UserFile]:
        """
        Get all files with a specific extension.
        
        Args:
            extension: File extension to filter by (e.g., '.mp4')
            
        Returns:
            List of UserFile objects with the specified extension
        """
        extension = extension.lower()
        return [file for file in self._files if file.extension == extension]
    
    def get_best_match(self) -> Optional[UserFile]:
        """
        Get the file with the highest similarity score.
        
        Returns:
            UserFile with highest similarity score, or None if group is empty
        """
        if not self._files:
            return None
        
        return max(self._files, key=lambda f: self._similarity_scores[f])
    
    def get_files_with_scores(self) -> List[Tuple[UserFile, float]]:
        """
        Get all files with their similarity scores.
        
        Returns:
            List of (UserFile, similarity_score) tuples, sorted by score (descending)
        """
        return sorted(
            [(file, self._similarity_scores[file]) for file in self._files],
            key=lambda x: x[1],
            reverse=True
        )
    
    def merge_group(self, other: 'PotentialMatchGroup') -> None:
        """
        Merge another potential match group into this one.
        
        The base name and threshold from this group are preserved.
        Files from the other group are re-evaluated against this group's criteria.
        
        Args:
            other: Another PotentialMatchGroup to merge
            
        Raises:
            TypeError: If other is not a PotentialMatchGroup
        """
        if not isinstance(other, PotentialMatchGroup):
            raise TypeError("Can only merge with another PotentialMatchGroup")
        
        # Add files from other group, re-computing similarity scores
        for file in other._files:
            try:
                similarity_score = self._compute_similarity(file)
                if similarity_score >= self._similarity_threshold:
                    self._files.add(file)
                    self._similarity_scores[file] = similarity_score
            except ValueError:
                # File doesn't meet similarity threshold for this group
                continue
    
    def update_threshold(self, new_threshold: float) -> List[UserFile]:
        """
        Update the similarity threshold and remove files that no longer qualify.
        
        Args:
            new_threshold: New similarity threshold (0.0-1.0)
            
        Returns:
            List of files that were removed due to the new threshold
            
        Raises:
            ValueError: If new_threshold is invalid
        """
        if not (0.0 <= new_threshold <= 1.0):
            raise ValueError("Similarity threshold must be between 0.0 and 1.0")
        
        self._similarity_threshold = new_threshold
        
        # Find files that no longer meet the threshold
        removed_files = []
        for file in list(self._files):
            if self._similarity_scores[file] < new_threshold:
                self._files.remove(file)
                del self._similarity_scores[file]
                removed_files.append(file)
        
        return removed_files
    
    def _compute_similarity(self, file: UserFile) -> float:
        """
        Compute similarity score between file and base name using fuzzy matching.
        
        Args:
            file: UserFile to compute similarity for
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        try:
            from fuzzywuzzy import fuzz
        except ImportError:
            # Fallback to simple string comparison if fuzzywuzzy not available
            filename = file.get_filename_without_extension().lower()
            base_name_lower = self._base_name.lower()
            
            if filename == base_name_lower:
                return 1.0
            elif base_name_lower in filename or filename in base_name_lower:
                return 0.8
            else:
                return 0.0
        
        filename = file.get_filename_without_extension()
        return fuzz.ratio(filename, self._base_name) / 100.0
    
    def __len__(self) -> int:
        """Number of files in this group."""
        return len(self._files)
    
    def __iter__(self) -> Iterator[UserFile]:
        """Iterate over files in this group, sorted by similarity score."""
        return iter(self.files)
    
    def __contains__(self, file: UserFile) -> bool:
        """Check if file is in this group."""
        return file in self._files
    
    def __str__(self) -> str:
        """String representation showing base name and file count."""
        return f"PotentialMatchGroup(base_name='{self._base_name}', files={len(self._files)})"
    
    def __repr__(self) -> str:
        """Detailed string representation for debugging."""
        return (
            f"PotentialMatchGroup(base_name='{self._base_name}', "
            f"threshold={self._similarity_threshold:.3f}, "
            f"file_count={len(self._files)}, "
            f"avg_similarity={self.average_similarity:.3f})"
        )
    
    def __eq__(self, other) -> bool:
        """
        Equality based on base name, threshold, and file set.
        
        Args:
            other: Another PotentialMatchGroup
            
        Returns:
            True if both groups have same base name, threshold, and files
        """
        if not isinstance(other, PotentialMatchGroup):
            return False
        
        return (
            self._base_name == other._base_name and
            self._similarity_threshold == other._similarity_threshold and
            self._files == other._files
        )
    
    def __hash__(self) -> int:
        """Hash based on base name and threshold for use in sets and dicts."""
        return hash((self._base_name, self._similarity_threshold))
    
    def to_dict(self) -> dict:
        """
        Convert to dictionary representation for JSON/YAML export.
        
        Returns:
            Dictionary with group information
        """
        return {
            'base_name': self._base_name,
            'similarity_threshold': self._similarity_threshold,
            'file_count': self.file_count,
            'average_similarity': self.average_similarity,
            'extensions': sorted(self.extensions),
            'total_size': self.total_size,
            'files': [
                {
                    **file.to_dict(),
                    'similarity_score': self._similarity_scores[file]
                }
                for file in self.files
            ]
        }
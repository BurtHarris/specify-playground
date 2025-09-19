#!/usr/bin/env python3
"""
ScanResult model for Video Duplicate Scanner CLI.

Contains the complete results of a video duplicate scanning operation,
including metadata, duplicate groups, and potential matches.
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Union

from .duplicate_group import DuplicateGroup
from .potential_match_group import PotentialMatchGroup
from .scan_metadata import ScanMetadata
from .file import UserFile


class ScanResult:
    """Contains complete results of a video duplicate scanning operation."""
    
    def __init__(self, metadata: ScanMetadata):
        """
        Initialize a ScanResult with metadata.

        Args:
            metadata: ScanMetadata object containing scan configuration and statistics
        """
        self.metadata = metadata
        self.duplicate_groups: List[DuplicateGroup] = []
        self.potential_match_groups: List[PotentialMatchGroup] = []
        self._all_files = None  # Cached set of all files
    
    @property
    def has_duplicates(self) -> bool:
        """True if any duplicate groups were found."""
        return len(self.duplicate_groups) > 0
    
    @property
    def has_potential_matches(self) -> bool:
        """True if any potential match groups were found."""
        return len(self.potential_match_groups) > 0
    
    @property
    def duplicate_count(self) -> int:
        """Number of duplicate groups found."""
        return len(self.duplicate_groups)
    
    @property
    def potential_match_count(self) -> int:
        """Number of potential match groups found."""
        return len(self.potential_match_groups)
    
    @property
    def total_duplicate_files(self) -> int:
        """Total number of files in all duplicate groups."""
        return sum(group.file_count for group in self.duplicate_groups)
    
    @property
    def total_potential_match_files(self) -> int:
        """Total number of files in all potential match groups."""
        return sum(group.file_count for group in self.potential_match_groups)
    
    @property
    def total_wasted_space(self) -> int:
        """Total amount of wasted disk space from duplicates."""
        return sum(group.wasted_space for group in self.duplicate_groups)
    
    @property
    def total_duplicate_space(self) -> int:
        """Total size of all duplicate files."""
        return sum(group.total_size for group in self.duplicate_groups)
    
    @property
    def all_files(self) -> Set[UserFile]:
        """Set of all unique files found in the scan."""
        if self._all_files is None:
            self._all_files = set()
            
            # Add files from duplicate groups
            for group in self.duplicate_groups:
                self._all_files.update(group.files)
            
            # Add files from potential match groups
            for group in self.potential_match_groups:
                self._all_files.update(group.files)
        
        return self._all_files
    
    @property
    def unique_files_count(self) -> int:
        """Number of unique files found in the scan."""
        return len(self.all_files)
    
    def add_duplicate_group(self, group: DuplicateGroup) -> None:
        """
        Add a duplicate group to the results.
        
        Args:
            group: DuplicateGroup to add
            
        Raises:
            TypeError: If group is not a DuplicateGroup instance
            ValueError: If group is empty or contains only one file
        """
        if not isinstance(group, DuplicateGroup):
            raise TypeError("Must be a DuplicateGroup instance")
        
        if not group.is_duplicate_group:
            raise ValueError("Duplicate group must contain at least 2 files")
        
        self.duplicate_groups.append(group)
        self.metadata.duplicate_groups_found = len(self.duplicate_groups)
        
        # Update metadata statistics
        self.metadata.update_duplicate_stats(group.total_size, group.wasted_space)
        
        # Clear cached all_files set
        self._all_files = None
    
    def add_potential_match_group(self, group: PotentialMatchGroup) -> None:
        """
        Add a potential match group to the results.
        
        Args:
            group: PotentialMatchGroup to add
            
        Raises:
            TypeError: If group is not a PotentialMatchGroup instance
            ValueError: If group is empty or contains only one file
        """
        if not isinstance(group, PotentialMatchGroup):
            raise TypeError("Must be a PotentialMatchGroup instance")
        
        if not group.is_potential_match_group:
            raise ValueError("Potential match group must contain at least 2 files")
        
        self.potential_match_groups.append(group)
        self.metadata.potential_match_groups_found = len(self.potential_match_groups)
        
        # Clear cached all_files set
        self._all_files = None
    
    def remove_duplicate_group(self, group: DuplicateGroup) -> bool:
        """
        Remove a duplicate group from the results.
        
        Args:
            group: DuplicateGroup to remove
            
        Returns:
            True if group was removed, False if not found
        """
        try:
            self.duplicate_groups.remove(group)
            self.metadata.duplicate_groups_found = len(self.duplicate_groups)
            
            # Update metadata statistics (subtract the group's contribution)
            self.metadata.update_duplicate_stats(-group.total_size, -group.wasted_space)
            
            # Clear cached all_files set
            self._all_files = None
            return True
        except ValueError:
            return False
    
    def remove_potential_match_group(self, group: PotentialMatchGroup) -> bool:
        """
        Remove a potential match group from the results.
        
        Args:
            group: PotentialMatchGroup to remove
            
        Returns:
            True if group was removed, False if not found
        """
        try:
            self.potential_match_groups.remove(group)
            self.metadata.potential_match_groups_found = len(self.potential_match_groups)
            
            # Clear cached all_files set
            self._all_files = None
            return True
        except ValueError:
            return False
    
    def get_duplicate_groups_by_size(self, min_size: Optional[int] = None, 
                                   max_size: Optional[int] = None) -> List[DuplicateGroup]:
        """
        Get duplicate groups filtered by file size.
        
        Args:
            min_size: Minimum file size in bytes
            max_size: Maximum file size in bytes
            
        Returns:
            List of DuplicateGroup objects matching size criteria
        """
        filtered_groups = []
        
        for group in self.duplicate_groups:
            # All files in a duplicate group have the same size
            if group.files:
                file_size = group.files[0].size
                
                if min_size is not None and file_size < min_size:
                    continue
                if max_size is not None and file_size > max_size:
                    continue
                    
                filtered_groups.append(group)
        
        return filtered_groups
    
    def get_duplicate_groups_by_extension(self, extension: str) -> List[DuplicateGroup]:
        """
        Get duplicate groups containing files with a specific extension.
        
        Args:
            extension: File extension to filter by (e.g., '.mp4')
            
        Returns:
            List of DuplicateGroup objects containing files with the extension
        """
        extension = extension.lower()
        filtered_groups = []
        
        for group in self.duplicate_groups:
            if any(file.extension == extension for file in group.files):
                filtered_groups.append(group)
        
        return filtered_groups
    
    def get_potential_matches_by_extension(self, extension: str) -> List[PotentialMatchGroup]:
        """
        Get potential match groups containing files with a specific extension.
        
        Args:
            extension: File extension to filter by (e.g., '.mp4')
            
        Returns:
            List of PotentialMatchGroup objects containing files with the extension
        """
        extension = extension.lower()
        filtered_groups = []
        
        for group in self.potential_match_groups:
            if extension in group.extensions:
                filtered_groups.append(group)
        
        return filtered_groups
    
    def get_files_by_path_prefix(self, path_prefix: Union[str, Path]) -> Set[UserFile]:
        """
        Get all files whose paths start with the given prefix.
        
        Args:
            path_prefix: Path prefix to match against
            
        Returns:
            Set of UserFile objects with matching path prefix
        """
        path_prefix = str(Path(path_prefix).resolve())
        matching_files = set()
        
        for file in self.all_files:
            if str(file.path).startswith(path_prefix):
                matching_files.add(file)
        
        return matching_files
    
    def find_file_by_path(self, path: Union[str, Path]) -> Optional[UserFile]:
        """
        Find a specific file by its path.
        
        Args:
            path: Path to search for
            
        Returns:
            UserFile if found, None otherwise
        """
        target_path = Path(path).resolve()
        
        for file in self.all_files:
            if file.path == target_path:
                return file
        
        return None
    
    def get_summary(self) -> Dict[str, any]:
        """
        Get a summary of the scan results.
        
        Returns:
            Dictionary with summary information
        """
        summary = {
            'scan_completed': self.metadata.is_completed,
            'scan_duration_seconds': self.metadata.duration_seconds,
            'total_files_scanned': self.metadata.total_files_processed,
            'unique_files_found': self.unique_files_count,
            'duplicate_groups_found': self.duplicate_count,
            'potential_match_groups_found': self.potential_match_count,
            'total_duplicate_files': self.total_duplicate_files,
            'total_potential_match_files': self.total_potential_match_files,
            'total_wasted_space_bytes': self.total_wasted_space,
            'total_wasted_space_mb': round(self.total_wasted_space / (1024 * 1024), 2),
            'space_savings_potential_percent': round(self.metadata.space_savings_potential, 1)
        }
        
        # Add performance metrics
        summary.update(self.metadata.get_summary_stats())
        
        return summary
    
    def sort_duplicate_groups_by_size(self, reverse: bool = True) -> None:
        """
        Sort duplicate groups by file size.
        
        Args:
            reverse: If True, sort largest to smallest (default)
        """
        self.duplicate_groups.sort(
            key=lambda group: group.files[0].size if group.files else 0,
            reverse=reverse
        )
    
    def sort_duplicate_groups_by_count(self, reverse: bool = True) -> None:
        """
        Sort duplicate groups by number of files.
        
        Args:
            reverse: If True, sort most files to least (default)
        """
        self.duplicate_groups.sort(
            key=lambda group: group.file_count,
            reverse=reverse
        )
    
    def sort_duplicate_groups_by_wasted_space(self, reverse: bool = True) -> None:
        """
        Sort duplicate groups by wasted space.
        
        Args:
            reverse: If True, sort most wasted to least (default)
        """
        self.duplicate_groups.sort(
            key=lambda group: group.wasted_space,
            reverse=reverse
        )
    
    def sort_potential_matches_by_similarity(self, reverse: bool = True) -> None:
        """
        Sort potential match groups by average similarity score.
        
        Args:
            reverse: If True, sort highest similarity to lowest (default)
        """
        self.potential_match_groups.sort(
            key=lambda group: group.average_similarity,
            reverse=reverse
        )
    
    def __str__(self) -> str:
        """String representation with key statistics."""
        return (
            f"ScanResult(duplicates={self.duplicate_count}, "
            f"potential_matches={self.potential_match_count}, "
            f"files={self.unique_files_count})"
        )
    
    def __repr__(self) -> str:
        """Detailed string representation for debugging."""
        return (
            f"ScanResult(duplicate_groups={self.duplicate_count}, "
            f"potential_match_groups={self.potential_match_count}, "
            f"total_files={self.unique_files_count}, "
            f"wasted_space={self.total_wasted_space})"
        )
    
    def to_dict(self) -> dict:
        """
        Convert to dictionary representation for JSON/YAML export.
        
        Returns:
            Dictionary with complete scan results
        """
        return {
            'metadata': self.metadata.to_dict(),
            'summary': self.get_summary(),
            'duplicate_groups': [group.to_dict() for group in self.duplicate_groups],
            'potential_match_groups': [group.to_dict() for group in self.potential_match_groups]
        }
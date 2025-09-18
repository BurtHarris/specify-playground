"""
DuplicateDetector service for identifying duplicate and similar video files.

This service implements a two-stage detection approach:
1. Group files by size for performance optimization
2. Compute and compare hashes only for files with matching sizes
"""

from collections import defaultdict
from typing import List
from pathlib import Path
from fuzzywuzzy import fuzz
import re

from ..models.video_file import VideoFile
from ..models.duplicate_group import DuplicateGroup
from ..models.potential_match_group import PotentialMatchGroup


class DuplicateDetector:
    """Service for detecting duplicate and potentially similar video files."""
    
    def find_duplicates(self, files: List[VideoFile]) -> List[DuplicateGroup]:
        """
        Identifies duplicate files using size and hash comparison.
        
        Uses a two-stage approach:
        1. Group files by size (fast comparison)
        2. Compute hashes only for files with matching sizes
        
        Args:
            files: List of video files to analyze
            
        Returns:
            List of duplicate groups (groups with at least 2 files)
            
        Contract:
            - MUST group files by size first (performance optimization)
            - MUST compute hashes only for files with matching sizes
            - MUST group files with identical hashes
            - MUST return groups with at least 2 files
            - MUST preserve file order within groups
        """
        if not files:
            return []
        
        # Stage 1: Group files by size for performance optimization
        size_groups = defaultdict(list)
        for video_file in files:
            size_groups[video_file.size].append(video_file)
        
        # Stage 2: For size groups with multiple files, compute hashes
        duplicate_groups = []
        for file_list in size_groups.values():
            if len(file_list) < 2:
                # Skip groups with only one file
                continue
                
            # Compute hashes for all files in this size group
            hash_groups = defaultdict(list)
            for video_file in file_list:
                try:
                    # Compute hash if not already done
                    file_hash = video_file.compute_hash()
                    hash_groups[file_hash].append(video_file)
                except (OSError, PermissionError):
                    # Skip files that can't be read
                    continue
            
            # Create duplicate groups for hash groups with multiple files
            for file_hash, files_with_same_hash in hash_groups.items():
                if len(files_with_same_hash) >= 2:
                    # Preserve file order within groups
                    duplicate_group = DuplicateGroup(file_hash, files_with_same_hash)
                    duplicate_groups.append(duplicate_group)
        
        return duplicate_groups
    
    def find_potential_matches(self, files: List[VideoFile], threshold: float = 0.8) -> List[PotentialMatchGroup]:
        """
        Identifies files with similar names that might be duplicates.
        
        Uses fuzzy string matching on filenames, ignoring extensions.
        
        Args:
            files: List of video files to analyze
            threshold: Similarity threshold (0.0-1.0)
            
        Returns:
            List of potential match groups
            
        Contract:
            - MUST use fuzzy string matching on filenames
            - MUST ignore file extensions in comparison
            - MUST only group files above threshold similarity
            - MUST calculate accurate similarity scores
            - MUST handle Unicode filenames correctly
        """
        if not files or threshold < 0.0 or threshold > 1.0:
            return []
        
        potential_groups = []
        processed_files = set()
        
        for i, file1 in enumerate(files):
            if file1 in processed_files:
                continue
                
            # Extract filename without extension for comparison
            name1 = self._extract_filename_for_comparison(file1.path)
            
            # Find all files similar to this one
            similar_files = [file1]
            similarity_scores = {}
            
            for j, file2 in enumerate(files[i+1:], start=i+1):
                if file2 in processed_files:
                    continue
                    
                name2 = self._extract_filename_for_comparison(file2.path)
                
                # Calculate similarity score using fuzzy matching
                similarity = fuzz.ratio(name1, name2) / 100.0
                
                if similarity >= threshold:
                    similar_files.append(file2)
                    similarity_scores[file2] = similarity
            
            # Create potential match group if we found similar files
            if len(similar_files) >= 2:
                # Set similarity score for the base file
                similarity_scores[file1] = 1.0
                
                # Use the base filename as the group name
                base_name = self._extract_filename_for_comparison(file1.path)
                potential_group = PotentialMatchGroup(base_name, threshold)
                
                # Add all similar files to the group
                for file in similar_files:
                    potential_group.add_file(file, similarity_scores[file])
                    
                potential_groups.append(potential_group)
                
                # Mark all files in this group as processed
                for file in similar_files:
                    processed_files.add(file)
        
        return potential_groups
    
    def _extract_filename_for_comparison(self, file_path: Path) -> str:
        """
        Extract filename without extension for fuzzy comparison.
        
        Handles Unicode filenames correctly and normalizes for comparison.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Filename without extension, suitable for comparison
        """
        # Get filename without extension
        filename = file_path.stem
        
        # Normalize whitespace and handle Unicode correctly
        filename = re.sub(r'\s+', ' ', filename.strip())
        
        return filename
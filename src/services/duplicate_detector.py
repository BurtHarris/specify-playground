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
    
    def find_duplicates(self, files: List[VideoFile], progress_reporter=None, verbose: bool = False) -> List[DuplicateGroup]:
        """
        Identifies duplicate files using size and hash comparison.
        
        Uses a two-stage approach:
        1. Group files by size (fast comparison)
        2. Compute hashes only for files with matching sizes
        
        Args:
            files: List of video files to analyze
            progress_reporter: Optional progress reporter for feedback
            verbose: Enable detailed logging of actions taken
            
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
        
        if verbose:
            print(f"Analyzing {len(files)} files for duplicates...")
            # Show cloud status breakdown
            cloud_only_count = sum(1 for f in files if f.is_cloud_only)
            local_count = len(files) - cloud_only_count
            print(f"  Cloud-only files: {cloud_only_count}")
            print(f"  Local files: {local_count}")
            print()
            
            # Show detailed analysis of each file
            print("File analysis:")
            for video_file in files:
                cloud_status = "CLOUD-ONLY" if video_file.is_cloud_only else "LOCAL"
                size_mb = video_file.size / (1024 * 1024)
                print(f"  {cloud_status:10} | {size_mb:8.1f} MB | {video_file.path.name}")
            print()
        
        # Stage 1: Group files by size for performance optimization
        size_groups = defaultdict(list)
        for video_file in files:
            size_groups[video_file.size].append(video_file)
        
        if verbose:
            groups_with_multiple = sum(1 for file_list in size_groups.values() if len(file_list) >= 2)
            print(f"Found {groups_with_multiple} size groups with potential duplicates")
        
        # Stage 2: For size groups with multiple files, compute hashes
        duplicate_groups = []
        total_files_to_hash = sum(len(file_list) for file_list in size_groups.values() if len(file_list) >= 2)
        hashed_files = 0
        skipped_cloud_files = 0
        skipped_error_files = 0
        
        for file_list in size_groups.values():
            if len(file_list) < 2:
                # Skip groups with only one file
                continue
                
            # Compute hashes for all files in this size group
            hash_groups = defaultdict(list)
            for video_file in file_list:
                try:
                    # Report progress if reporter available
                    if progress_reporter:
                        progress_reporter.update_progress(hashed_files, f"Computing hash: {video_file.path.name}")
                    
                    # Skip hash computation for cloud-only files to avoid triggering downloads
                    if video_file.is_cloud_only:
                        if verbose:
                            print(f"  SKIPPED (cloud-only): {video_file.path.name}")
                        hashed_files += 1
                        skipped_cloud_files += 1
                        continue
                    
                    if verbose:
                        print(f"  HASHING: {video_file.path.name}")
                    
                    # Compute hash if not already done
                    file_hash = video_file.compute_hash()
                    hash_groups[file_hash].append(video_file)
                    hashed_files += 1
                except (OSError, PermissionError) as e:
                    if verbose:
                        print(f"  SKIPPED (error): {video_file.path.name} - {e}")
                    # Skip files that can't be read
                    hashed_files += 1
                    skipped_error_files += 1
                    continue
            
            # Create duplicate groups for hash groups with multiple files
            for file_hash, files_with_same_hash in hash_groups.items():
                if len(files_with_same_hash) >= 2:
                    # Preserve file order within groups
                    duplicate_group = DuplicateGroup(file_hash, files_with_same_hash)
                    duplicate_groups.append(duplicate_group)
                    if verbose:
                        print(f"  DUPLICATE GROUP: {len(files_with_same_hash)} files with hash {file_hash[:8]}...")
        
        if verbose:
            print(f"Hash computation summary:")
            print(f"  Files hashed: {hashed_files - skipped_cloud_files - skipped_error_files}")
            print(f"  Cloud-only files skipped: {skipped_cloud_files}")
            print(f"  Error files skipped: {skipped_error_files}")
            print(f"  Duplicate groups found: {len(duplicate_groups)}")
        
        return duplicate_groups
    
    def find_potential_matches(self, files: List[VideoFile], threshold: float = 0.8, verbose: bool = False) -> List[PotentialMatchGroup]:
        """
        Identifies files with similar names that might be duplicates.
        
        Uses fuzzy string matching on filenames combined with size analysis
        to identify potential duplicates that require manual review.
        
        Args:
            files: List of video files to analyze
            threshold: Name similarity threshold (0.0-1.0)
            verbose: Enable detailed logging of actions taken
            
        Returns:
            List of potential match groups
            
        Contract:
            - MUST use fuzzy string matching on filenames (name similarity)
            - MUST validate with size comparison (file similarity indicators)
            - MUST ignore file extensions in name comparison
            - MUST only group files above threshold name similarity
            - MUST calculate accurate similarity scores
            - MUST handle Unicode filenames correctly
        """
        if not files or threshold < 0.0 or threshold > 1.0:
            return []
        
        if verbose:
            print(f"Analyzing {len(files)} files for potential matches (name similarity threshold: {threshold})...")
        
        potential_groups = []
        processed_files = set()
        excluded_pairs = 0
        
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
                
                # Check if files should be excluded from similarity matching
                if self._should_exclude_from_similarity(name1, name2):
                    if verbose:
                        print(f"  EXCLUDED (name patterns): '{file1.path.name}' vs '{file2.path.name}' (obvious non-duplicates)")
                    excluded_pairs += 1
                    continue
                
                # Calculate name similarity score using fuzzy matching
                name_similarity = fuzz.ratio(name1, name2) / 100.0
                
                if name_similarity >= threshold:
                    # Check if file sizes are reasonably similar (within 3x of each other)
                    # Different quality encodings of same content shouldn't differ by more than 3x
                    size_ratio = max(file1.size, file2.size) / max(min(file1.size, file2.size), 1)
                    if size_ratio > 3.0:
                        if verbose:
                            print(f"  EXCLUDED (size diff): '{file1.path.name}' vs '{file2.path.name}' - name similarity: {name_similarity:.2f}, sizes: {file1.size/(1024*1024):.1f}MB vs {file2.size/(1024*1024):.1f}MB (ratio: {size_ratio:.1f}x)")
                        excluded_pairs += 1
                        continue
                    
                    if verbose:
                        print(f"  POTENTIAL MATCH: '{file1.path.name}' vs '{file2.path.name}' - name similarity: {name_similarity:.2f}, sizes: {file1.size/(1024*1024):.1f}MB vs {file2.size/(1024*1024):.1f}MB")
                    similar_files.append(file2)
                    similarity_scores[file2] = name_similarity
            
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
                
                if verbose:
                    print(f"  POTENTIAL GROUP: {len(similar_files)} files similar to '{file1.path.name}'")
                
                # Mark all files in this group as processed
                for file in similar_files:
                    processed_files.add(file)
        
        if verbose:
            print(f"Potential match analysis summary:")
            print(f"  Potential groups found: {len(potential_groups)}")
            print(f"  Excluded obvious non-duplicates: {excluded_pairs}")
        
        return potential_groups
    
    def _extract_filename_for_comparison(self, file_path: Path) -> str:
        """
        Extract filename without extension for fuzzy comparison.
        
        Handles Unicode filenames correctly and normalizes for comparison.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Filename without extension, suitable for comparison (lowercase)
        """
        # Get filename without extension
        filename = file_path.stem
        
        # Normalize whitespace and handle Unicode correctly
        filename = re.sub(r'\s+', ' ', filename.strip())
        
        # Convert to lowercase for case-insensitive comparison
        return filename.lower()
    
    def _should_exclude_from_similarity(self, name1: str, name2: str) -> bool:
        """
        Check if two filenames should be excluded from similarity matching.
        
        Only excludes very obvious non-duplicates with high confidence to avoid
        blocking legitimate potential matches.
        
        Args:
            name1: First filename (already lowercased)
            name2: Second filename (already lowercased)
            
        Returns:
            True if files should be excluded from similarity matching
        """
        # Only exclude if we have very high confidence they're different
        # Pattern 1: Clear sequential numbering with same base name
        # Only exclude if the base names are very similar AND numbers are clearly different
        sequential_patterns = [
            r'\bpart\s*(\d+)\b',
            r'\bepisode\s*(\d+)\b',
            r'\bvol(?:ume)?\s*(\d+)\b'
        ]
        
        for pattern in sequential_patterns:
            matches1 = re.findall(pattern, name1, re.IGNORECASE)
            matches2 = re.findall(pattern, name2, re.IGNORECASE)
            
            if matches1 and matches2 and matches1 != matches2:
                # Remove the sequential parts and check if base names are nearly identical
                base1 = re.sub(pattern, '', name1, flags=re.IGNORECASE).strip()
                base2 = re.sub(pattern, '', name2, flags=re.IGNORECASE).strip()
                
                # Only exclude if base names are very similar (>90% match)
                base_similarity = fuzz.ratio(base1, base2) / 100.0
                if base_similarity > 0.9:
                    return True  # High confidence these are sequential parts
        
        # Pattern 2: Identical timestamps with small time differences
        # Only exclude files with identical base names but different precise timestamps
        timestamp_pattern = r'(\d{4}-\d{2}-\d{2}\s+\d{2}[_:]\d{2})'
        times1 = re.findall(timestamp_pattern, name1)
        times2 = re.findall(timestamp_pattern, name2)
        
        if times1 and times2 and times1 != times2:
            # Remove timestamps and check if base names are identical
            base1 = re.sub(timestamp_pattern, '', name1).strip()
            base2 = re.sub(timestamp_pattern, '', name2).strip()
            if base1 == base2:  # Identical base names, different timestamps
                return True
        
        return False  # Don't exclude - let fuzzy matching decide
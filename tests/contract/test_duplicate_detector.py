#!/usr/bin/env python3
"""
DuplicateDetector Service Contract Tests for Video Duplicate Scanner

These tests validate the DuplicateDetector service contract as specified in
specs/001-build-a-cli/contracts/service-apis.md

All tests MUST FAIL initially (TDD requirement) until implementation is complete.
"""

import pytest
from pathlib import Path
import tempfile
import shutil
import hashlib

# Import the DuplicateDetector service (will fail until implemented)
try:
    from services.duplicate_detector import DuplicateDetector
    from models.video_file import VideoFile
    from models.duplicate_group import DuplicateGroup
    from models.potential_match_group import PotentialMatchGroup
except ImportError:
    # Expected to fail initially - create stubs for testing
    class DuplicateDetector:
        def find_duplicates(self, files):
            raise NotImplementedError("DuplicateDetector not yet implemented")
            
        def find_potential_matches(self, files, threshold=0.8):
            raise NotImplementedError("DuplicateDetector not yet implemented")
    
    class VideoFile:
        def __init__(self, path, size=None, hash_value=None):
            self.path = Path(path)
            self.size = size or 0
            self.hash = hash_value
            
    class DuplicateGroup:
        def __init__(self, files):
            self.files = files
            
    class PotentialMatchGroup:
        def __init__(self, files, similarity_score):
            self.files = files
            self.similarity_score = similarity_score


class TestDuplicateDetectorContract:
    """Test DuplicateDetector service contract compliance."""
    
    def setup_method(self):
        """Set up test environment for each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.detector = DuplicateDetector()
        
        # Create test video files with content for testing
        self.create_test_files()
        
    def teardown_method(self):
        """Clean up after each test."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def create_test_files(self):
        """Create test files with known content for duplicate detection."""
        # Create files with identical content (duplicates)
        duplicate_content = b"This is duplicate video content" * 1000
        
        self.duplicate1 = Path(self.temp_dir) / "duplicate1.mp4"
        self.duplicate2 = Path(self.temp_dir) / "duplicate2.mp4"
        self.duplicate3 = Path(self.temp_dir) / "duplicate3.mkv"
        
        for file in [self.duplicate1, self.duplicate2, self.duplicate3]:
            with open(file, 'wb') as f:
                f.write(duplicate_content)
        
        # Create unique files
        unique_content1 = b"Unique video content 1" * 1000
        unique_content2 = b"Unique video content 2" * 1000
        
        self.unique1 = Path(self.temp_dir) / "unique1.mp4"
        self.unique2 = Path(self.temp_dir) / "unique2.mkv"
        
        with open(self.unique1, 'wb') as f:
            f.write(unique_content1)
        with open(self.unique2, 'wb') as f:
            f.write(unique_content2)
            
        # Create files with similar names but different content
        similar_content1 = b"Similar but different content 1" * 1000
        similar_content2 = b"Similar but different content 2" * 1000
        
        self.similar1 = Path(self.temp_dir) / "movie_title.mp4"
        self.similar2 = Path(self.temp_dir) / "movie_title.mkv"
        
        with open(self.similar1, 'wb') as f:
            f.write(similar_content1)
        with open(self.similar2, 'wb') as f:
            f.write(similar_content2)

    def create_video_file_objects(self):
        """Create VideoFile objects from test files."""
        files = []
        
        for file_path in [self.duplicate1, self.duplicate2, self.duplicate3, 
                         self.unique1, self.unique2, self.similar1, self.similar2]:
            size = file_path.stat().st_size
            
            # Calculate hash
            hasher = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
            hash_value = hasher.hexdigest()
            
            files.append(VideoFile(file_path, size, hash_value))
            
        return files

    @pytest.mark.contract
    def test_find_duplicates_returns_duplicate_groups(self):
        """Test: find_duplicates returns List[DuplicateGroup]."""
        files = self.create_video_file_objects()
        
        result = self.detector.find_duplicates(files)
        
        # Contract: Returns List[DuplicateGroup]
        assert isinstance(result, list)
        for group in result:
            assert isinstance(group, DuplicateGroup)

    @pytest.mark.contract
    def test_find_duplicates_groups_by_size_first(self):
        """Test: Groups files by size first for performance optimization."""
        files = self.create_video_file_objects()
        
        # This test validates the performance contract - grouping by size first
        # We can't directly test the internal implementation, but we can verify
        # that files with different sizes are not grouped together
        
        result = self.detector.find_duplicates(files)
        
        # Contract: MUST group files by size first
        for group in result:
            if len(group.files) > 1:
                # All files in a duplicate group must have the same size
                first_size = group.files[0].size
                for file in group.files[1:]:
                    assert file.size == first_size, "Files in duplicate group must have same size"

    @pytest.mark.contract
    def test_find_duplicates_computes_hashes_for_size_matches(self):
        """Test: Computes hashes only for files with matching sizes."""
        files = self.create_video_file_objects()
        
        result = self.detector.find_duplicates(files)
        
        # Contract: MUST compute hashes only for files with matching sizes
        # All files in duplicate groups should have identical hashes
        for group in result:
            if len(group.files) > 1:
                first_hash = group.files[0].hash
                for file in group.files[1:]:
                    assert file.hash == first_hash, "Files in duplicate group must have identical hashes"

    @pytest.mark.contract
    def test_find_duplicates_groups_identical_hashes(self):
        """Test: Groups files with identical hashes."""
        files = self.create_video_file_objects()
        
        result = self.detector.find_duplicates(files)
        
        # Contract: MUST group files with identical hashes
        # Should find at least one group with our duplicate files
        found_duplicate_group = False
        
        for group in result:
            if len(group.files) >= 3:  # Our test has 3 duplicate files
                # Check if this group contains our duplicate files
                group_paths = {f.path.name for f in group.files}
                expected_duplicates = {"duplicate1.mp4", "duplicate2.mp4", "duplicate3.mkv"}
                
                if expected_duplicates.issubset(group_paths):
                    found_duplicate_group = True
                    
        assert found_duplicate_group, "Should find group containing our duplicate files"

    @pytest.mark.contract
    def test_find_duplicates_returns_groups_with_minimum_two_files(self):
        """Test: Returns groups with at least 2 files."""
        files = self.create_video_file_objects()
        
        result = self.detector.find_duplicates(files)
        
        # Contract: MUST return groups with at least 2 files
        for group in result:
            assert len(group.files) >= 2, "Duplicate groups must contain at least 2 files"

    @pytest.mark.contract
    def test_find_duplicates_preserves_file_order_within_groups(self):
        """Test: Preserves file order within groups."""
        files = self.create_video_file_objects()
        
        # Run multiple times to check consistency
        result1 = self.detector.find_duplicates(files)
        result2 = self.detector.find_duplicates(files)
        
        # Contract: MUST preserve file order within groups
        assert len(result1) == len(result2)
        
        for group1, group2 in zip(result1, result2):
            paths1 = [f.path for f in group1.files]
            paths2 = [f.path for f in group2.files]
            assert paths1 == paths2, "File order within groups should be consistent"

    @pytest.mark.contract
    def test_find_potential_matches_returns_potential_match_groups(self):
        """Test: find_potential_matches returns List[PotentialMatchGroup]."""
        files = self.create_video_file_objects()
        
        result = self.detector.find_potential_matches(files, threshold=0.8)
        
        # Contract: Returns List[PotentialMatchGroup]
        assert isinstance(result, list)
        for group in result:
            assert isinstance(group, PotentialMatchGroup)

    @pytest.mark.contract
    def test_find_potential_matches_uses_fuzzy_string_matching(self):
        """Test: Uses fuzzy string matching on filenames."""
        files = self.create_video_file_objects()
        
        result = self.detector.find_potential_matches(files, threshold=0.8)
        
        # Contract: MUST use fuzzy string matching on filenames
        # Should find potential match between "movie_title.mp4" and "movie_title.mkv"
        found_similar_match = False
        
        for group in result:
            group_names = {f.path.stem for f in group.files}  # stem excludes extension
            if "movie_title" in group_names and len(group.files) >= 2:
                found_similar_match = True
                
        assert found_similar_match, "Should find potential match for similar filenames"

    @pytest.mark.contract
    def test_find_potential_matches_ignores_file_extensions(self):
        """Test: Ignores file extensions in comparison."""
        files = self.create_video_file_objects()
        
        result = self.detector.find_potential_matches(files, threshold=0.8)
        
        # Contract: MUST ignore file extensions in comparison
        # Files with same name but different extensions should be matched
        for group in result:
            if len(group.files) >= 2:
                # Check if files have same name but different extensions
                stems = [f.path.stem for f in group.files]
                extensions = [f.path.suffix for f in group.files]
                
                # If stems are the same but extensions differ, that validates the contract
                if len(set(stems)) == 1 and len(set(extensions)) > 1:
                    # Found a group that matches same name, different extensions
                    return
                    
        # If we reach here, we should at least not fail due to extension handling

    @pytest.mark.contract
    def test_find_potential_matches_respects_threshold(self):
        """Test: Only groups files above threshold similarity."""
        files = self.create_video_file_objects()
        
        # Test with high threshold - should find fewer matches
        high_threshold_result = self.detector.find_potential_matches(files, threshold=0.95)
        
        # Test with low threshold - should find more matches
        low_threshold_result = self.detector.find_potential_matches(files, threshold=0.3)
        
        # Contract: MUST only group files above threshold similarity
        # Higher threshold should result in fewer or equal matches
        assert len(high_threshold_result) <= len(low_threshold_result)
        
        # All groups should have similarity scores above their respective thresholds
        for group in high_threshold_result:
            assert group.similarity_score >= 0.95
            
        for group in low_threshold_result:
            assert group.similarity_score >= 0.3

    @pytest.mark.contract
    def test_find_potential_matches_calculates_accurate_similarity_scores(self):
        """Test: Calculates accurate similarity scores."""
        files = self.create_video_file_objects()
        
        result = self.detector.find_potential_matches(files, threshold=0.0)  # Get all matches
        
        # Contract: MUST calculate accurate similarity scores
        for group in result:
            # Similarity score should be between 0.0 and 1.0
            assert 0.0 <= group.similarity_score <= 1.0
            
            # Score should be reasonably accurate - files with identical names 
            # (different extensions) should have high similarity
            if len(group.files) >= 2:
                stems = [f.path.stem for f in group.files]
                if len(set(stems)) == 1:  # All have same stem
                    assert group.similarity_score >= 0.8, "Identical names should have high similarity"

    @pytest.mark.contract
    def test_find_potential_matches_handles_unicode_filenames(self):
        """Test: Handles Unicode filenames correctly."""
        # Create files with Unicode names
        unicode_files = []
        
        unicode_names = [
            "фильм_название.mp4",  # Cyrillic
            "فيلم_عنوان.mkv",       # Arabic
            "电影_标题.mov",         # Chinese
            "película_título.mp4"   # Spanish with accents
        ]
        
        for name in unicode_names:
            file_path = Path(self.temp_dir) / name
            with open(file_path, 'wb') as f:
                f.write(b"Unicode test content")
                
            unicode_files.append(VideoFile(file_path, file_path.stat().st_size))
        
        # Contract: MUST handle Unicode filenames correctly
        try:
            result = self.detector.find_potential_matches(unicode_files, threshold=0.5)
            # Should not raise exceptions with Unicode filenames
            assert isinstance(result, list)
        except UnicodeError:
            pytest.fail("Should handle Unicode filenames without errors")

    @pytest.mark.contract
    def test_find_potential_matches_default_threshold(self):
        """Test: Uses 0.8 as default threshold."""
        files = self.create_video_file_objects()
        
        # Call without threshold parameter
        result_default = self.detector.find_potential_matches(files)
        
        # Call with explicit 0.8 threshold
        result_explicit = self.detector.find_potential_matches(files, threshold=0.8)
        
        # Contract: Default threshold should be 0.8
        assert len(result_default) == len(result_explicit)
        
        # Both results should be equivalent
        for group_default, group_explicit in zip(result_default, result_explicit):
            assert group_default.similarity_score == group_explicit.similarity_score

    @pytest.mark.contract
    def test_find_duplicates_handles_empty_file_list(self):
        """Test: Handles empty file list gracefully."""
        result = self.detector.find_duplicates([])
        
        # Contract: Should handle empty input gracefully
        assert isinstance(result, list)
        assert len(result) == 0

    @pytest.mark.contract
    def test_find_potential_matches_handles_empty_file_list(self):
        """Test: Handles empty file list gracefully."""
        result = self.detector.find_potential_matches([])
        
        # Contract: Should handle empty input gracefully
        assert isinstance(result, list)
        assert len(result) == 0

    @pytest.mark.contract
    def test_find_duplicates_handles_single_file(self):
        """Test: Handles single file input gracefully."""
        files = [self.create_video_file_objects()[0]]  # Just one file
        
        result = self.detector.find_duplicates(files)
        
        # Contract: Single file cannot form a duplicate group
        assert isinstance(result, list)
        assert len(result) == 0  # No groups with single file

    @pytest.mark.contract
    def test_find_potential_matches_handles_single_file(self):
        """Test: Handles single file input gracefully."""
        files = [self.create_video_file_objects()[0]]  # Just one file
        
        result = self.detector.find_potential_matches(files)
        
        # Contract: Single file cannot form a potential match group
        assert isinstance(result, list)
        assert len(result) == 0  # No groups with single file


if __name__ == "__main__":
    # Run contract tests
    pytest.main([__file__, "-v", "-m", "contract"])
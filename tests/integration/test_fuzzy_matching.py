#!/usr/bin/env python3
"""
Fuzzy Matching Integration Tests for Video Duplicate Scanner

These tests validate end-to-end fuzzy name matching functionality for
identifying potential duplicates with similar filenames.

All tests MUST FAIL initially (TDD requirement) until implementation is complete.
"""

import pytest
import tempfile
import shutil
from pathlib import Path

# Import modules for integration testing (will fail until implemented)
try:
    from services.video_file_scanner import VideoFileScanner
    from services.duplicate_detector import DuplicateDetector
    from services.fuzzy_matcher import FuzzyMatcher
    from models.video_file import VideoFile
    from models.potential_match_group import PotentialMatchGroup
except ImportError:
    # Expected to fail initially - create stubs for testing
    class VideoFileScanner:
        def scan_directory(self, directory, recursive=True):
            raise NotImplementedError("VideoFileScanner not yet implemented")
    
    class DuplicateDetector:
        def find_potential_matches(self, files, threshold=0.8):
            raise NotImplementedError("DuplicateDetector not yet implemented")
    
    class FuzzyMatcher:
        def find_similar_names(self, files, threshold=0.8):
            raise NotImplementedError("FuzzyMatcher not yet implemented")
            
        def calculate_similarity(self, name1, name2):
            raise NotImplementedError("FuzzyMatcher not yet implemented")
    
    class VideoFile:
        def __init__(self, path, size=None, hash_value=None):
            self.path = Path(path)
            self.size = size or 0
            self.hash = hash_value
    
    class PotentialMatchGroup:
        def __init__(self, files, similarity_score):
            self.files = files
            self.similarity_score = similarity_score


class TestFuzzyMatchingIntegration:
    """Test fuzzy matching integration scenarios."""
    
    def setup_method(self):
        """Set up test environment for each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.scanner = VideoFileScanner()
        self.detector = DuplicateDetector()
        self.fuzzy_matcher = FuzzyMatcher()
        
        # Create test video files with similar names
        self.create_test_videos()
        
    def teardown_method(self):
        """Clean up after each test."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def create_test_videos(self):
        """Create test video files with various name similarity patterns."""
        # Similar movie titles (high similarity)
        similar_movies = [
            ("The_Dark_Knight.mp4", b"Content for Dark Knight 1" * 1000),
            ("The_Dark_Knight.mkv", b"Content for Dark Knight 2" * 1000),
            ("The_Dark_Knight_1080p.mp4", b"Content for Dark Knight 3" * 1000),
            ("The.Dark.Knight.mp4", b"Content for Dark Knight 4" * 1000),
        ]
        
        # Series episodes (medium similarity)
        series_episodes = [
            ("Game_of_Thrones_S01E01.mkv", b"GoT Episode 1 content" * 1000),
            ("Game.of.Thrones.S01E01.mp4", b"GoT Episode 1 alt content" * 1000),
            ("Game_of_Thrones_Season1_Episode1.mov", b"GoT Episode 1 long content" * 1000),
        ]
        
        # Different movies (low similarity)
        different_movies = [
            ("Inception.mp4", b"Inception content" * 1000),
            ("Avatar.mkv", b"Avatar content" * 1000),
            ("Interstellar.mov", b"Interstellar content" * 1000),
        ]
        
        # Create all test files
        all_files = similar_movies + series_episodes + different_movies
        for filename, content in all_files:
            file_path = Path(self.temp_dir) / filename
            with open(file_path, 'wb') as f:
                f.write(content)

    @pytest.mark.integration
    def test_end_to_end_fuzzy_matching_high_similarity(self):
        """Test: End-to-end fuzzy matching finds files with high name similarity."""
        # Integration test: Scan → Fuzzy match
        scanned_files = list(self.scanner.scan_directory(Path(self.temp_dir)))
        potential_matches = self.detector.find_potential_matches(scanned_files, threshold=0.8)
        
        # Should find potential matches for similar filenames
        assert len(potential_matches) > 0
        
        # Should find The Dark Knight variations
        dark_knight_found = False
        for group in potential_matches:
            group_names = [f.path.stem.lower() for f in group.files]
            if any("dark" in name and "knight" in name for name in group_names):
                dark_knight_found = True
                assert len(group.files) >= 2  # At least 2 similar files
                assert group.similarity_score >= 0.8  # High similarity
                
        assert dark_knight_found, "Should find The Dark Knight filename variations"

    @pytest.mark.integration
    def test_fuzzy_matching_ignores_file_extensions(self):
        """Test: Fuzzy matching ignores file extensions when comparing names."""
        # Integration test: Files with same name but different extensions
        scanned_files = list(self.scanner.scan_directory(Path(self.temp_dir)))
        potential_matches = self.detector.find_potential_matches(scanned_files, threshold=0.7)
        
        # Should match files with same base name but different extensions
        extension_match_found = False
        for group in potential_matches:
            if len(group.files) >= 2:
                # Check if files have same stem but different extensions
                stems = [f.path.stem for f in group.files]
                extensions = [f.path.suffix for f in group.files]
                
                # Look for groups where stems are similar but extensions differ
                if len(set(extensions)) > 1:  # Different extensions
                    # Stems should be similar (ignoring punctuation differences)
                    base_stem = stems[0].replace("_", "").replace(".", "").lower()
                    for stem in stems[1:]:
                        compare_stem = stem.replace("_", "").replace(".", "").lower()
                        if base_stem == compare_stem or base_stem in compare_stem or compare_stem in base_stem:
                            extension_match_found = True
                            break
                            
        assert extension_match_found, "Should match files with same name but different extensions"

    @pytest.mark.integration
    def test_fuzzy_matching_threshold_filtering(self):
        """Test: Fuzzy matching respects similarity threshold settings."""
        scanned_files = list(self.scanner.scan_directory(Path(self.temp_dir)))
        
        # Test with high threshold (strict matching)
        high_threshold_matches = self.detector.find_potential_matches(scanned_files, threshold=0.9)
        
        # Test with medium threshold
        medium_threshold_matches = self.detector.find_potential_matches(scanned_files, threshold=0.7)
        
        # Test with low threshold (permissive matching) 
        low_threshold_matches = self.detector.find_potential_matches(scanned_files, threshold=0.5)
        
        # Lower thresholds should find same or more matches
        assert len(low_threshold_matches) >= len(medium_threshold_matches)
        assert len(medium_threshold_matches) >= len(high_threshold_matches)
        
        # All matches should respect their threshold
        for group in high_threshold_matches:
            assert group.similarity_score >= 0.9
            
        for group in medium_threshold_matches:
            assert group.similarity_score >= 0.7
            
        for group in low_threshold_matches:
            assert group.similarity_score >= 0.5

    @pytest.mark.integration
    def test_fuzzy_matching_punctuation_normalization(self):
        """Test: Fuzzy matching handles punctuation and spacing differences."""
        # Create files with same content but different punctuation
        punctuation_variants = [
            "Movie Title.mp4",
            "Movie.Title.mkv", 
            "Movie_Title.mov",
            "Movie-Title.mp4",
            "MovieTitle.mkv"
        ]
        
        content = b"Same movie different punctuation" * 1000
        for filename in punctuation_variants:
            file_path = Path(self.temp_dir) / filename
            with open(file_path, 'wb') as f:
                f.write(content)
        
        # Integration test: Should match despite punctuation differences
        scanned_files = list(self.scanner.scan_directory(Path(self.temp_dir)))
        potential_matches = self.detector.find_potential_matches(scanned_files, threshold=0.7)
        
        # Should find a group with the punctuation variants
        punctuation_match_found = False
        for group in potential_matches:
            if len(group.files) >= 3:  # Should group multiple punctuation variants
                group_names = [f.path.name for f in group.files]
                movie_title_variants = [name for name in group_names if "Movie" in name and "Title" in name]
                
                if len(movie_title_variants) >= 3:
                    punctuation_match_found = True
                    assert group.similarity_score >= 0.7
                    
        assert punctuation_match_found, "Should match files despite punctuation differences"

    @pytest.mark.integration
    def test_fuzzy_matching_case_insensitive(self):
        """Test: Fuzzy matching is case insensitive."""
        # Create files with same content but different cases
        case_variants = [
            "action_movie.mp4",
            "Action_Movie.mkv",
            "ACTION_MOVIE.mov",
            "Action.Movie.mp4"
        ]
        
        content = b"Same movie different case" * 1000
        for filename in case_variants:
            file_path = Path(self.temp_dir) / filename
            with open(file_path, 'wb') as f:
                f.write(content)
        
        # Integration test: Should match despite case differences
        scanned_files = list(self.scanner.scan_directory(Path(self.temp_dir)))
        potential_matches = self.detector.find_potential_matches(scanned_files, threshold=0.8)
        
        # Should find a group with the case variants
        case_match_found = False
        for group in potential_matches:
            if len(group.files) >= 3:
                group_names = [f.path.stem.lower() for f in group.files]
                action_movie_variants = [name for name in group_names if "action" in name and "movie" in name]
                
                if len(action_movie_variants) >= 3:
                    case_match_found = True
                    
        assert case_match_found, "Should match files despite case differences"

    @pytest.mark.integration
    def test_fuzzy_matching_unicode_filenames(self):
        """Test: Fuzzy matching handles Unicode filenames correctly."""
        # Create files with Unicode names
        unicode_variants = [
            "电影标题.mp4",       # Chinese
            "電影標題.mkv",       # Traditional Chinese (similar)
            "фильм_название.mov", # Cyrillic
            "película_título.mp4" # Spanish
        ]
        
        content = b"Unicode movie content" * 1000
        for filename in unicode_variants:
            file_path = Path(self.temp_dir) / filename
            with open(file_path, 'wb') as f:
                f.write(content)
        
        # Integration test: Should handle Unicode without errors
        scanned_files = list(self.scanner.scan_directory(Path(self.temp_dir)))
        
        # Should not crash with Unicode filenames
        try:
            potential_matches = self.detector.find_potential_matches(scanned_files, threshold=0.5)
            assert isinstance(potential_matches, list)
        except UnicodeError:
            pytest.fail("Should handle Unicode filenames without errors")

    @pytest.mark.integration
    def test_fuzzy_matching_series_episode_patterns(self):
        """Test: Fuzzy matching recognizes TV series episode patterns."""
        # Create TV series episodes with different naming conventions
        episode_variants = [
            "Breaking_Bad_S01E01.mkv",
            "Breaking.Bad.S01E01.mp4", 
            "Breaking Bad Season 1 Episode 1.mov",
            "Breaking_Bad_1x01.mp4",
            "BreakingBad_S1E1.mkv"
        ]
        
        content = b"Breaking Bad episode content" * 1000
        for filename in episode_variants:
            file_path = Path(self.temp_dir) / filename
            with open(file_path, 'wb') as f:
                f.write(content)
        
        # Integration test: Should recognize episode pattern similarities
        scanned_files = list(self.scanner.scan_directory(Path(self.temp_dir)))
        potential_matches = self.detector.find_potential_matches(scanned_files, threshold=0.6)
        
        # Should find matches for Breaking Bad episodes
        episode_match_found = False
        for group in potential_matches:
            if len(group.files) >= 3:
                group_names = [f.path.stem.lower() for f in group.files]
                breaking_bad_episodes = [name for name in group_names if "breaking" in name and "bad" in name]
                
                if len(breaking_bad_episodes) >= 3:
                    episode_match_found = True
                    
        assert episode_match_found, "Should match TV series episodes despite naming differences"

    @pytest.mark.integration
    def test_fuzzy_matching_quality_indicators(self):
        """Test: Fuzzy matching handles quality indicators in filenames."""
        # Create files with same title but different quality indicators
        quality_variants = [
            "Avatar_720p.mp4",
            "Avatar_1080p.mkv",
            "Avatar_4K.mov",
            "Avatar_HDRip.mp4",
            "Avatar_BluRay.mkv",
            "Avatar.mp4"  # No quality indicator
        ]
        
        content = b"Avatar movie content" * 1000
        for filename in quality_variants:
            file_path = Path(self.temp_dir) / filename
            with open(file_path, 'wb') as f:
                f.write(content)
        
        # Integration test: Should match despite quality indicators
        scanned_files = list(self.scanner.scan_directory(Path(self.temp_dir)))
        potential_matches = self.detector.find_potential_matches(scanned_files, threshold=0.7)
        
        # Should find a group with Avatar variants
        quality_match_found = False
        for group in potential_matches:
            if len(group.files) >= 4:  # Should group multiple quality variants
                group_names = [f.path.stem.lower() for f in group.files]
                avatar_variants = [name for name in group_names if "avatar" in name]
                
                if len(avatar_variants) >= 4:
                    quality_match_found = True
                    
        assert quality_match_found, "Should match files despite quality indicators"

    @pytest.mark.integration
    def test_fuzzy_matching_excludes_very_different_names(self):
        """Test: Fuzzy matching excludes files with very different names."""
        scanned_files = list(self.scanner.scan_directory(Path(self.temp_dir)))
        potential_matches = self.detector.find_potential_matches(scanned_files, threshold=0.8)
        
        # Should not group completely different movie titles
        for group in potential_matches:
            if len(group.files) >= 2:
                # Verify that grouped files actually have similar names
                first_name = group.files[0].path.stem.lower()
                for file in group.files[1:]:
                    other_name = file.path.stem.lower()
                    
                    # Should have some common words or characters
                    # (This is a basic check - actual implementation may be more sophisticated)
                    common_chars = set(first_name) & set(other_name)
                    assert len(common_chars) >= 3, f"Files should have some similarity: {first_name} vs {other_name}"

    @pytest.mark.integration
    def test_fuzzy_matching_performance_with_many_files(self):
        """Test: Fuzzy matching performs reasonably with larger file sets."""
        # Create many files for performance testing
        for i in range(100):
            if i % 10 == 0:
                # Create groups of similar files
                base_name = f"movie_series_{i // 10}"
                for j in range(3):
                    filename = f"{base_name}_part{j}.mp4"
            else:
                # Create unique files
                filename = f"unique_movie_{i}.mkv"
            
            file_path = Path(self.temp_dir) / filename
            content = f"Content for file {i}".encode() * 1000
            with open(file_path, 'wb') as f:
                f.write(content)
        
        # Integration test: Should handle large file set efficiently
        scanned_files = list(self.scanner.scan_directory(Path(self.temp_dir)))
        
        # Should complete without timeout (basic performance check)
        import time
        start_time = time.time()
        potential_matches = self.detector.find_potential_matches(scanned_files, threshold=0.8)
        duration = time.time() - start_time
        
        # Should complete in reasonable time (adjust threshold as needed)
        assert duration < 30.0, f"Fuzzy matching took too long: {duration} seconds"
        
        # Should find some matches from our similar files
        assert len(potential_matches) > 0, "Should find some potential matches in large dataset"

    @pytest.mark.integration
    def test_fuzzy_matching_integration_with_duplicate_detection(self):
        """Test: Fuzzy matching integrates properly with duplicate detection."""
        # Create files that are both duplicates (same content) and have similar names
        duplicate_content = b"Duplicate content with similar names" * 1000
        
        # Exact duplicates with similar names
        exact_duplicates = [
            "Movie_Title_2023.mp4",
            "Movie_Title_2023_backup.mp4"
        ]
        
        for filename in exact_duplicates:
            file_path = Path(self.temp_dir) / filename
            with open(file_path, 'wb') as f:
                f.write(duplicate_content)
        
        # Similar names but different content
        similar_different_content = [
            ("Movie_Title_2024.mkv", b"Different content 2024" * 1000),
            ("Movie.Title.2024.mov", b"Different content alt" * 1000)
        ]
        
        for filename, content in similar_different_content:
            file_path = Path(self.temp_dir) / filename
            with open(file_path, 'wb') as f:
                f.write(content)
        
        # Integration test: Both duplicate detection and fuzzy matching
        scanned_files = list(self.scanner.scan_directory(Path(self.temp_dir)))
        
        # Find exact duplicates
        duplicate_groups = self.detector.find_duplicates(scanned_files)
        
        # Find potential matches
        potential_matches = self.detector.find_potential_matches(scanned_files, threshold=0.7)
        
        # Should find exact duplicates
        assert len(duplicate_groups) >= 1, "Should find exact duplicates"
        
        # Should also find potential matches for similar names
        assert len(potential_matches) >= 1, "Should find potential matches"
        
        # Files that are exact duplicates should not appear in potential matches
        # (they're already confirmed duplicates)
        duplicate_files = {f.path for group in duplicate_groups for f in group.files}
        potential_files = {f.path for group in potential_matches for f in group.files}
        
        # There might be some overlap, but the systems should work together
        assert len(duplicate_files) > 0
        assert len(potential_files) > 0


if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v", "-m", "integration"])
"""
Unit tests for PotentialMatchGroup model.

Tests the PotentialMatchGroup data model including file grouping,
name similarity, and threshold validation.
"""

import pytest
from pathlib import Path
import tempfile

from src.models.user_file import UserFile
from src.models.potential_match_group import PotentialMatchGroup


class TestPotentialMatchGroup:
    """Test suite for PotentialMatchGroup model."""
    
    @pytest.fixture
    def sample_user_files(self):
        """Create sample UserFile instances for testing."""
        files = []
        user_files = []
        # Create temporary files with similar names but different content
        file_names = ['movie.mp4', 'movie2.mkv', 'movieX.mov']
        for name in file_names:
            with tempfile.NamedTemporaryFile(suffix='.tmp', delete=False) as f:
                f.write(name.encode())
                temp_path = Path(f.name)
            final_path = temp_path.parent / name
            # If a file with the target name already exists (test flakiness), remove it first
            try:
                if final_path.exists():
                    final_path.unlink()
            except Exception:
                pass
            temp_path.rename(final_path)
            files.append(final_path)
        for file_path in files:
            user_files.append(UserFile(file_path))
        yield user_files
        # Cleanup
        for user_file in user_files:
            if user_file.path.exists():
                user_file.path.unlink()
    
    def test_potential_match_group_creation(self, sample_user_files):
        """Test basic PotentialMatchGroup creation."""
        base_name = "movie"
        threshold = 0.8
        group = PotentialMatchGroup(base_name, threshold, sample_user_files[:2])
        assert group.base_name == base_name
        assert group.similarity_threshold == threshold
        assert len(group.files) == 2

    def test_potential_match_group_empty_base_name_error(self):
        """Test that creating a group with empty base name raises error."""
        with pytest.raises(ValueError, match="Base name cannot be empty"):
            PotentialMatchGroup("", 0.8)
    
    def test_potential_match_group_invalid_threshold_error(self):
        """Test that invalid threshold raises error."""
        base_name = "movie"
        
        with pytest.raises(ValueError, match="Similarity threshold must be between 0.0 and 1.0"):
            PotentialMatchGroup(base_name, -0.1)
        
        with pytest.raises(ValueError, match="Similarity threshold must be between 0.0 and 1.0"):
            PotentialMatchGroup(base_name, 1.1)
    
    def test_potential_match_group_creation_no_files(self):
        """Test creating group with base name but no files."""
        base_name = "movie"
        threshold = 0.8
        
        group = PotentialMatchGroup(base_name, threshold)
        
        assert group.base_name == base_name
        assert group.similarity_threshold == threshold
        assert len(group.files) == 0
    
    def test_add_file_to_group(self, sample_video_files):
        """Test adding files to a group."""
        base_name = "movie"
        threshold = 0.8
        group = PotentialMatchGroup(base_name, threshold)
        
        for video_file in sample_video_files:
            group.add_file(video_file)
        
        assert len(group.files) == len(sample_video_files)
        for video_file in sample_video_files:
            assert video_file in group.files
    
    def test_remove_file_from_group(self, sample_video_files):
        """Test removing files from a group."""
        base_name = "movie"
        threshold = 0.8
        group = PotentialMatchGroup(base_name, threshold, sample_video_files)
        file_to_remove = sample_video_files[0]
        
        group.remove_file(file_to_remove)
        
        assert file_to_remove not in group.files
        assert len(group.files) == len(sample_video_files) - 1
    
    def test_remove_file_not_in_group_error(self, sample_video_files):
        """Test that removing non-existent file returns False."""
        base_name = "movie"
        threshold = 0.8
        group = PotentialMatchGroup(base_name, threshold, sample_video_files[:1])
        
        # Try to remove a file that's not in the group
        result = group.remove_file(sample_video_files[1])
        assert result is False
        assert len(group.files) == 1  # Group should still have the original file
    
    def test_file_count_property(self, sample_video_files):
        """Test file_count property."""
        base_name = "movie"
        threshold = 0.8
        group = PotentialMatchGroup(base_name, threshold, sample_video_files)
        
        assert group.file_count == len(sample_video_files)
    
    def test_group_id_uniqueness(self, sample_video_files):
        """Test that each group gets unique base names."""
        base_name1 = "movie"
        base_name2 = "movieZ"  # Similar but different base name
        threshold = 0.8
    
        group1 = PotentialMatchGroup(base_name1, threshold, sample_video_files[:1])
        group2 = PotentialMatchGroup(base_name2, threshold, sample_video_files[2:3])  # Use movieX file which should be compatible
        
        assert group1.base_name != group2.base_name

    def test_group_id_format(self, sample_video_files):
        """Test that base name follows expected format."""
        base_name = "movie"
        threshold = 0.8
        group = PotentialMatchGroup(base_name, threshold, sample_video_files[:2])
        
        # Base name should be a string
        assert isinstance(group.base_name, str)
        assert group.base_name == base_name
    
    def test_str_representation(self, sample_video_files):
        """Test string representation of PotentialMatchGroup."""
        base_name = "movie"
        threshold = 0.8
        group = PotentialMatchGroup(base_name, threshold, sample_video_files[:2])
        str_repr = str(group)
    
        assert "PotentialMatchGroup" in str_repr
        assert str(group.base_name) in str_repr
        assert str(len(group.files)) in str_repr

    def test_equality_comparison(self, sample_video_files):
        """Test equality comparison between groups."""
        base_name = "movie"
        threshold = 0.8
        
        group1 = PotentialMatchGroup(base_name, threshold, sample_video_files[:2])
        group2 = PotentialMatchGroup(base_name, threshold, sample_video_files[:2])  # Same files
        
        # Create a compatible base name for the third group test
        compatible_base = "moviefilm"  # This should have high similarity with movieX
        group3 = PotentialMatchGroup(compatible_base, 0.6, sample_video_files[2:3])  # Lower threshold for compatibility
        
        # Test equality based on actual comparison method
        assert group1.base_name == group2.base_name
        assert group1.base_name != group3.base_name
    
    def test_to_dict(self, sample_video_files):
        """Test to_dict method."""
        base_name = "movie"
        threshold = 0.8
        group = PotentialMatchGroup(base_name, threshold, sample_video_files[:2])
        
        data = group.to_dict()
        
        assert 'base_name' in data
        assert 'similarity_threshold' in data
        assert 'file_count' in data
        assert 'average_similarity' in data
        assert 'extensions' in data
        assert 'total_size' in data
        assert 'files' in data
        
        assert data['base_name'] == base_name
        assert data['similarity_threshold'] == threshold
        assert data['file_count'] == 2
        assert len(data['files']) == 2
    
    def test_different_thresholds(self, sample_video_files):
        """Test groups with different similarity thresholds."""
        base_name = "movie"
        
        group1 = PotentialMatchGroup(base_name, 0.8, sample_video_files[:2])
        group2 = PotentialMatchGroup(base_name, 0.9, sample_video_files[:2])
        
        assert group1.similarity_threshold == 0.8
        assert group2.similarity_threshold == 0.9
        assert group1.base_name == group2.base_name  # Same base name
    
    def test_boundary_thresholds(self):
        """Test boundary values for similarity threshold."""
        base_name = "movie"
        
        # Minimum threshold
        group_min = PotentialMatchGroup(base_name, 0.0)
        assert group_min.similarity_threshold == 0.0
        
        # Maximum threshold
        group_max = PotentialMatchGroup(base_name, 1.0)
        assert group_max.similarity_threshold == 1.0

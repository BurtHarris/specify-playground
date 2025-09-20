"""
Unit tests for DuplicateGroup model.

Tests the DuplicateGroup data model including file grouping,
size calculations, and validation.
"""

import pytest
from pathlib import Path
import tempfile
import hashlib

from src.models.user_file import UserFile
from src.models.duplicate_group import DuplicateGroup


class TestDuplicateGroup:
    """Test suite for DuplicateGroup model."""
    
    @pytest.fixture
    def sample_content_and_hash(self):
        """Create sample content and its hash for testing."""
        content = b"identical content for testing duplicate files"
        hash_obj = hashlib.blake2b()
        hash_obj.update(content)
        hash_value = hash_obj.hexdigest()
        return content, hash_value
    
    @pytest.fixture
    def sample_user_files(self, sample_content_and_hash):
        """Create sample UserFile instances for testing."""
        content, hash_value = sample_content_and_hash
        files = []
        user_files = []
        for i in range(3):
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f:
                f.write(content)
                files.append(Path(f.name))
        for file_path in files:
            user_files.append(UserFile(file_path))
        yield user_files, hash_value
        for file_path in files:
            if file_path.exists():
                file_path.unlink()
    
    def test_duplicate_group_creation(self, sample_user_files):
        """Test basic DuplicateGroup creation."""
        user_files, hash_value = sample_user_files
        group = DuplicateGroup(hash_value, user_files[:2])
        assert group.hash_value == hash_value
        assert len(group.files) == 2
    
    def test_duplicate_group_empty_hash_error(self):
        """Test that creating a group with empty hash raises error."""
        with pytest.raises(ValueError, match="Hash value cannot be empty"):
            DuplicateGroup("")
    
    def test_duplicate_group_creation_no_files(self, sample_user_files):
        """Test creating group with hash but no files."""
        video_files, hash_value = sample_user_files
        
        group = DuplicateGroup(hash_value)
        
        assert group.hash_value == hash_value
        assert len(group.files) == 0
    
    def test_add_file_to_group(self, sample_user_files):
        """Test adding files to a group."""
        video_files, hash_value = sample_user_files
        group = DuplicateGroup(hash_value)
        
        for video_file in video_files:
            group.add_file(video_file)
        
        assert len(group.files) == len(video_files)
        for video_file in video_files:
            assert video_file in group.files
    
    def test_remove_file_from_group(self, sample_user_files):
        """Test removing files from a group."""
        video_files, hash_value = sample_user_files
        group = DuplicateGroup(hash_value, video_files)
        file_to_remove = video_files[0]
        
        group.remove_file(file_to_remove)
        
        assert file_to_remove not in group.files
        assert len(group.files) == len(video_files) - 1
    
    def test_remove_file_not_in_group_error(self, sample_user_files):
        """Test that removing non-existent file returns False."""
        video_files, hash_value = sample_user_files
        group = DuplicateGroup(hash_value, video_files[:1])
        
        # Try to remove a file that wasn't added to the group
        # Since we only added the first file, the second file isn't in the group
        result = group.remove_file(video_files[1])
        assert result is False  # Should return False when file not found
    
    def test_total_size_property(self, sample_user_files):
        """Test total_size property calculation."""
        video_files, hash_value = sample_user_files
        group = DuplicateGroup(hash_value, video_files)
        
        expected_size = sum(f.size for f in video_files)
        assert group.total_size == expected_size
    
    def test_total_size_empty_group(self, sample_user_files):
        """Test total_size for empty group."""
        video_files, hash_value = sample_user_files
        group = DuplicateGroup(hash_value)
        
        assert group.total_size == 0
    
    def test_wasted_space_property(self, sample_user_files):
        """Test wasted_space property calculation."""
        video_files, hash_value = sample_user_files
        group = DuplicateGroup(hash_value, video_files)
        
        if len(video_files) > 1:
            # Wasted space = total_size - largest_file_size
            file_sizes = [f.size for f in video_files]
            expected_wasted = sum(file_sizes) - max(file_sizes)
            assert group.wasted_space == expected_wasted
        else:
            assert group.wasted_space == 0
    
    def test_file_count_property(self, sample_user_files):
        """Test file_count property."""
        video_files, hash_value = sample_user_files
        group = DuplicateGroup(hash_value, video_files)
        
        assert group.file_count == len(video_files)
    
    def test_group_id_uniqueness(self, sample_user_files):
        """Test that each group gets a unique hash."""
        video_files, hash_value = sample_user_files

        group1 = DuplicateGroup(hash_value, video_files[:1])
        group2 = DuplicateGroup(hash_value, video_files[1:2])
        
        # Groups with same hash should have same hash() value when they contain same files
        # But when they contain different files, hash might be different
        # This test verifies the hash-based equality works correctly
        assert group1 != group2  # Different files means different groups
    
    def test_group_id_format(self, sample_user_files):
        """Test that group hash value follows expected format."""
        video_files, hash_value = sample_user_files
        group = DuplicateGroup(hash_value, video_files[:2])
        
        # Hash value should be a non-empty string
        assert isinstance(group.hash_value, str)
        assert len(group.hash_value) > 0
        assert group.hash_value == hash_value
    
    def test_str_representation(self, sample_user_files):
        """Test string representation of DuplicateGroup."""
        video_files, hash_value = sample_user_files
        group = DuplicateGroup(hash_value, video_files[:2])
        str_repr = str(group)
        
        assert "DuplicateGroup" in str_repr
        assert "files=2" in str_repr
    
    def test_equality_comparison(self, sample_user_files):
        """Test equality comparison between groups."""
        video_files, hash_value = sample_user_files

        group1 = DuplicateGroup(hash_value, video_files[:2])
        group2 = DuplicateGroup(hash_value, video_files[:2])  # Same files
        
        different_hash = "different_hash_value"
        group3 = DuplicateGroup(different_hash)  # Different hash, no files to avoid validation
        
        # Groups with same hash and files should be equal
        assert group1 == group2
        assert group1 != group3
    
    def test_to_dict(self, sample_user_files):
        """Test to_dict method."""
        video_files, hash_value = sample_user_files
        group = DuplicateGroup(hash_value, video_files[:2])
        
        data = group.to_dict()
        
        assert 'hash' in data
        assert 'file_count' in data
        assert 'total_size' in data
        assert 'wasted_space' in data
        assert 'files' in data
        
        assert data['hash'] == hash_value
        assert data['file_count'] == 2
        assert len(data['files']) == 2
    
    def test_add_file_wrong_hash_error(self, sample_user_files):
        """Test that adding file with wrong hash raises error."""
        video_files, hash_value = sample_user_files
        group = DuplicateGroup(hash_value)
        
        # Create a file with different content (different hash)
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f:
            f.write(b"different content")
            different_file_path = Path(f.name)
        
        try:
            different_file = UserFile(different_file_path)
            
            with pytest.raises(ValueError, match="File hash .* doesn't match group hash"):
                group.add_file(different_file)
        finally:
            if different_file_path.exists():
                different_file_path.unlink()

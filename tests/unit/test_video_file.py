"""
Unit tests for VideoFile model.

Tests the core VideoFile data model including file validation,
hash computation, and path handling.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, mock_open, Mock
import hashlib
import tempfile
import os

from src.models.video_file import VideoFile


class TestVideoFile:
    """Test suite for VideoFile model."""
    
    @pytest.fixture
    def temp_video_file(self):
        """Create a temporary video file for testing."""
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f:
            f.write(b"test video content")
            temp_path = Path(f.name)
        
        yield temp_path
        
        # Cleanup
        if temp_path.exists():
            temp_path.unlink()
    
    def test_video_file_creation(self, temp_video_file):
        """Test basic VideoFile creation."""
        video_file = VideoFile(temp_video_file)
        
        assert video_file.path == temp_video_file.resolve()
        assert video_file.extension == '.mp4'
        assert video_file.size > 0
    
    def test_video_file_creation_nonexistent_file(self):
        """Test VideoFile creation with non-existent file raises error."""
        path = Path("/nonexistent/video.mp4")
        
        with pytest.raises(FileNotFoundError):
            VideoFile(path)
    
    def test_video_file_creation_unsupported_extension(self):
        """Test VideoFile creation with unsupported extension raises error."""
        with tempfile.NamedTemporaryFile(suffix='.avi', delete=False) as f:
            f.write(b"test content")
            temp_path = Path(f.name)
        
        try:
            with pytest.raises(ValueError, match="Unsupported video format"):
                VideoFile(temp_path)
        finally:
            temp_path.unlink()
    
    def test_video_file_equality(self, temp_video_file):
        """Test VideoFile equality comparison."""
        video1 = VideoFile(temp_video_file)
        video2 = VideoFile(temp_video_file)
        
        with tempfile.NamedTemporaryFile(suffix='.mkv', delete=False) as f:
            f.write(b"different content")
            temp_path2 = Path(f.name)
        
        try:
            video3 = VideoFile(temp_path2)
            
            assert video1 == video2
            assert video1 != video3
        finally:
            temp_path2.unlink()
    
    def test_video_file_hash(self, temp_video_file):
        """Test VideoFile hash computation."""
        video1 = VideoFile(temp_video_file)
        video2 = VideoFile(temp_video_file)
        
        assert hash(video1) == hash(video2)
    
    def test_video_file_str(self, temp_video_file):
        """Test VideoFile string representation."""
        video_file = VideoFile(temp_video_file)
        
        assert str(video_file) == str(temp_video_file.resolve())
    
    def test_video_file_repr(self, temp_video_file):
        """Test VideoFile repr representation."""
        video_file = VideoFile(temp_video_file)
        repr_str = repr(video_file)
        
        assert "VideoFile" in repr_str
        # Normalize path separators for cross-platform compatibility
        expected_path = str(temp_video_file.resolve()).replace('\\', '/')
        assert expected_path in repr_str or str(temp_video_file.resolve()) in repr_str
        assert ".mp4" in repr_str
    
    def test_compute_hash_blake2b(self, temp_video_file):
        """Test blake2b hash computation."""
        video_file = VideoFile(temp_video_file)
        
        # Compute expected hash
        with open(temp_video_file, 'rb') as f:
            expected_hash = hashlib.blake2b(f.read()).hexdigest()
        
        computed_hash = video_file.compute_hash()
        
        assert computed_hash == expected_hash
        assert video_file._hash == expected_hash
    
    def test_compute_hash_cached(self, temp_video_file):
        """Test that hash computation is cached."""
        video_file = VideoFile(temp_video_file)
        
        # First call
        hash1 = video_file.compute_hash()
        # Second call
        hash2 = video_file.compute_hash()
        
        assert hash1 == hash2
        assert video_file.hash == hash1
    
    def test_size_property(self, temp_video_file):
        """Test size property."""
        video_file = VideoFile(temp_video_file)
        expected_size = temp_video_file.stat().st_size
        
        assert video_file.size == expected_size
    
    def test_extension_property(self, temp_video_file):
        """Test extension property."""
        video_file = VideoFile(temp_video_file)
        
        assert video_file.extension == '.mp4'
    
    def test_last_modified_property(self, temp_video_file):
        """Test last_modified property."""
        video_file = VideoFile(temp_video_file)
        
        # Should return a datetime object
        last_modified = video_file.last_modified
        assert last_modified is not None
    
    def test_is_accessible(self, temp_video_file):
        """Test is_accessible method."""
        video_file = VideoFile(temp_video_file)
        
        assert video_file.is_accessible() is True
    
    def test_get_filename_without_extension(self, temp_video_file):
        """Test get_filename_without_extension method."""
        video_file = VideoFile(temp_video_file)
        
        expected_stem = temp_video_file.stem
        assert video_file.get_filename_without_extension() == expected_stem
    
    def test_refresh_metadata(self, temp_video_file):
        """Test refresh_metadata method."""
        video_file = VideoFile(temp_video_file)
        
        # Access size to cache it
        original_size = video_file.size
        
        # Refresh metadata
        video_file.refresh_metadata()
        
        # Size should be recalculated
        assert video_file.size == original_size
    
    def test_to_dict(self, temp_video_file):
        """Test to_dict method."""
        video_file = VideoFile(temp_video_file)
        
        data = video_file.to_dict()
        
        assert 'path' in data
        assert 'size' in data
        assert 'extension' in data
        assert 'last_modified' in data
        assert 'hash' in data
        
        assert data['path'] == str(temp_video_file.resolve())
        assert data['extension'] == '.mp4'
        assert data['hash'] is None  # Not computed yet
    
    def test_to_dict_with_hash(self, temp_video_file):
        """Test to_dict method with computed hash."""
        video_file = VideoFile(temp_video_file)
        
        # Compute hash
        computed_hash = video_file.compute_hash()
        
        data = video_file.to_dict()
        assert data['hash'] == computed_hash
    
    def test_hash_property_lazy_computation(self, temp_video_file):
        """Test hash property returns cached value."""
        video_file = VideoFile(temp_video_file)
        
        # Initially no hash
        assert video_file._hash is None
        assert video_file.hash is None
        
        # Compute hash explicitly
        computed_hash = video_file.compute_hash()
        
        # Now hash property should return the computed hash
        assert video_file.hash == computed_hash
        assert video_file._hash == computed_hash
    
    @pytest.mark.parametrize("extension", [".mp4", ".mkv", ".mov"])
    def test_supported_extensions(self, extension):
        """Test VideoFile with supported extensions."""
        with tempfile.NamedTemporaryFile(suffix=extension, delete=False) as f:
            f.write(b"test content")
            temp_path = Path(f.name)
        
        try:
            video_file = VideoFile(temp_path)
            assert video_file.extension == extension.lower()
        finally:
            temp_path.unlink()
    
    @pytest.mark.parametrize("extension", [".txt", ".jpg", ".pdf", ".avi", ".wmv"])
    def test_unsupported_extensions(self, extension):
        """Test VideoFile rejects unsupported extensions."""
        with tempfile.NamedTemporaryFile(suffix=extension, delete=False) as f:
            f.write(b"test content")
            temp_path = Path(f.name)
        
        try:
            with pytest.raises(ValueError, match="Unsupported video format"):
                VideoFile(temp_path)
        finally:
            temp_path.unlink()
    
    def test_ordering(self, temp_video_file):
        """Test VideoFile ordering."""
        video1 = VideoFile(temp_video_file)
        
        with tempfile.NamedTemporaryFile(suffix='.mkv', delete=False) as f:
            f.write(b"test content")
            temp_path2 = Path(f.name)
        
        try:
            video2 = VideoFile(temp_path2)
            
            # Should be orderable
            videos = sorted([video2, video1])
            assert len(videos) == 2
        finally:
            temp_path2.unlink()
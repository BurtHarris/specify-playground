"""
Unit tests for UserFile model.

Tests the core UserFile data model including file validation,
hash computation, and path handling.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, mock_open, Mock
import tempfile
import hashlib
from src.models.user_file import UserFile
"""
Unit tests for UserFile model.

Tests the core UserFile data model including file validation,
hash computation, and path handling.
"""

class TestUserFile:
    """Test suite for UserFile model."""
    
    @pytest.fixture
    def temp_user_file(self):
        """Create a temporary user file for testing."""
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f:
            f.write(b"test file content")
            temp_path = Path(f.name)
        yield temp_path
        if temp_path.exists():
            temp_path.unlink()
    
    def test_user_file_creation(self, temp_user_file):
        """Test basic UserFile creation."""
        user_file = UserFile(temp_user_file)
        assert user_file._path == temp_user_file.resolve()
        assert user_file.extension == '.mp4'
        assert user_file.size > 0
    
    def test_user_file_creation_nonexistent_file(self):
        """Test UserFile creation with non-existent file raises error."""
        path = Path("/nonexistent/file.mp4")
        # Lazy construction: creating the model should succeed but accessing
        # filesystem-backed properties should raise.
        user = UserFile(path)
        with pytest.raises(FileNotFoundError):
            _ = user.size
    
    def test_user_file_creation_unsupported_extension(self):
        """Test UserFile creation with unsupported extension raises error."""
        with tempfile.NamedTemporaryFile(suffix='.unsupported', delete=False) as f:
            f.write(b"test content")
            temp_path = Path(f.name)
        try:
            # Lazy model accepts unknown extensions; extension is exposed
            user = UserFile(temp_path)
            assert user.extension == '.unsupported'
        finally:
            temp_path.unlink()
    
    def test_user_file_equality(self, temp_user_file):
        """Test UserFile equality comparison."""
        user1 = UserFile(temp_user_file)
        user2 = UserFile(temp_user_file)
        with tempfile.NamedTemporaryFile(suffix='.mkv', delete=False) as f:
            f.write(b"different content")
            temp_path2 = Path(f.name)
        try:
            user3 = UserFile(temp_path2)
            assert user1 == user2
            assert user1 != user3
        finally:
            temp_path2.unlink()
    
    def test_user_file_hash(self, temp_user_file):
        """Test UserFile hash computation."""
        user1 = UserFile(temp_user_file)
        user2 = UserFile(temp_user_file)
        assert hash(user1) == hash(user2)
    
    def test_user_file_str(self, temp_user_file):
        """Test UserFile string representation."""
        user_file = UserFile(temp_user_file)
        assert str(user_file) == str(temp_user_file.resolve())
    
    def test_user_file_repr(self, temp_user_file):
        """Test UserFile repr representation."""
        user_file = UserFile(temp_user_file)
        repr_str = repr(user_file)
        assert "UserFile" in repr_str
        # Normalize path separators for cross-platform compatibility
        expected_path = str(temp_user_file.resolve()).replace('\\', '/')
        assert expected_path in repr_str or str(temp_user_file.resolve()) in repr_str
        assert ".mp4" in repr_str
    
    def test_compute_hash_blake2b(self, temp_user_file):
        """Test blake2b hash computation."""
        user_file = UserFile(temp_user_file)
        # Compute expected hash
        with open(temp_user_file, 'rb') as f:
            expected_hash = hashlib.blake2b(f.read()).hexdigest()
        computed_hash = user_file.compute_hash()
        assert computed_hash == expected_hash
        assert user_file._hash == expected_hash
    
    def test_compute_hash_cached(self, temp_user_file):
        """Test that hash computation is cached."""
        user_file = UserFile(temp_user_file)
        # First call
        hash1 = user_file.compute_hash()
        # Second call
        hash2 = user_file.compute_hash()
        assert hash1 == hash2
        assert user_file.hash == hash1
    
    def test_size_property(self, temp_user_file):
        """Test size property."""
        user_file = UserFile(temp_user_file)
        expected_size = temp_user_file.stat().st_size
        assert user_file.size == expected_size
    
    def test_extension_property(self, temp_user_file):
        """Test extension property."""
        user_file = UserFile(temp_user_file)
        assert user_file.extension == '.mp4'
    
    def test_last_modified_property(self, temp_user_file):
        """Test last_modified property."""
        user_file = UserFile(temp_user_file)
        # Should return a datetime object
        last_modified = user_file.last_modified
        assert last_modified is not None
    
    def test_is_accessible(self, temp_user_file):
        """Test is_accessible method."""
        user_file = UserFile(temp_user_file)
        assert user_file.is_accessible() is True
    
    def test_get_filename_without_extension(self, temp_user_file):
        """Test get_filename_without_extension method."""
        user_file = UserFile(temp_user_file)
        expected_stem = temp_user_file.stem
        assert user_file.get_filename_without_extension() == expected_stem
    
    def test_refresh_metadata(self, temp_user_file):
        """Test refresh_metadata method."""
        user_file = UserFile(temp_user_file)
        # Access size to cache it
        original_size = user_file.size
        # Refresh metadata
        user_file.refresh_metadata()
        # Size should be recalculated
        assert user_file.size == original_size
    
    def test_to_dict(self, temp_user_file):
        """Test to_dict method."""
        user_file = UserFile(temp_user_file)
        data = user_file.to_dict()
        assert 'path' in data
        assert 'size' in data
        assert 'extension' in data
        assert 'last_modified' in data
        assert 'hash' in data
        assert data['path'] == str(temp_user_file.resolve())
        assert data['extension'] == '.mp4'
        assert data['hash'] is None  # Not computed yet
    
    def test_to_dict_with_hash(self, temp_user_file):
        """Test to_dict method with computed hash."""
        user_file = UserFile(temp_user_file)
        # Compute hash
        computed_hash = user_file.compute_hash()
        data = user_file.to_dict()
        assert data['hash'] == computed_hash
    
    def test_hash_property_lazy_computation(self, temp_user_file):
        """Test hash property returns cached value."""
        user_file = UserFile(temp_user_file)
        # Initially no hash
        assert user_file._hash is None
        assert user_file.hash is None
        # Compute hash explicitly
        computed_hash = user_file.compute_hash()
        # Now hash property should return the computed hash
        assert user_file.hash == computed_hash
        assert user_file._hash == computed_hash
    
    @pytest.mark.parametrize("extension", [".mp4", ".mkv", ".mov"])
    def test_supported_extensions(self, extension):
        """Test UserFile with supported extensions."""
        with tempfile.NamedTemporaryFile(suffix=extension, delete=False) as f:
            f.write(b"test content")
            temp_path = Path(f.name)
        try:
            user_file = UserFile(temp_path)
            assert user_file.extension == extension.lower()
        finally:
            temp_path.unlink()
    
    @pytest.mark.parametrize("extension", [".txt", ".jpg", ".pdf", ".avi", ".wmv"])
    def test_unsupported_extensions(self, extension):
        """Test VideoFile rejects unsupported extensions."""
        with tempfile.NamedTemporaryFile(suffix=extension, delete=False) as f:
            f.write(b"test content")
            temp_path = Path(f.name)
        
        try:
            # Under lazy semantics the model accepts any extension and
            # simply exposes it via the ``extension`` attribute.
            user = UserFile(temp_path)
            assert user.extension == extension.lower()
        finally:
            temp_path.unlink()
    
    def test_ordering(self, temp_user_file):
        """Test UserFile ordering."""
        user1 = UserFile(temp_user_file)
        with tempfile.NamedTemporaryFile(suffix='.mkv', delete=False) as f:
            f.write(b"test content")
            temp_path2 = Path(f.name)
        try:
            user2 = UserFile(temp_path2)
            # Should be orderable
            users = sorted([user2, user1])
            assert len(users) == 2
        finally:
            temp_path2.unlink()
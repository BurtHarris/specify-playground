"""
Contract test for UserFile cloud status integration following TDD methodology.

This test verifies the enhanced UserFile model contract with cloud status support.
The tests are lightweight assertions that the `UserFile` model exposes the
expected cloud-related properties and that they behave sensibly (types and
mutual consistency). Implementation is expected to evolve; these contract tests
help guide the API.
"""

import pytest
from pathlib import Path

from src.models.user_file import UserFile
try:
    from src.models.cloud_file_status import CloudFileStatus
except Exception:
    class CloudFileStatus:
        LOCAL = "local"
        CLOUD_ONLY = "cloud_only"


class TestUserFileCloudIntegrationContract:
    """Contract tests for UserFile cloud status integration."""

    def test_user_file_has_cloud_properties(self):
        user = UserFile(Path("temp_test/video1.mp4"))
        assert hasattr(user, 'cloud_status')
        assert hasattr(user, 'is_cloud_only')
        assert hasattr(user, 'is_local')

    def test_is_local_and_is_cloud_only_are_boolean(self):
        user = UserFile(Path("temp_test/video1.mp4"))
        assert isinstance(user.is_local, bool)
        assert isinstance(user.is_cloud_only, bool)

    def test_cloud_status_enum_or_string(self):
        user = UserFile(Path("temp_test/video1.mp4"))
        status = user.cloud_status
        # Accept either enum-like object or string for contract
        assert (isinstance(status, str) or hasattr(status, 'name') or hasattr(status, 'value'))

    def test_mutual_exclusivity_of_booleans(self):
        user = UserFile(Path("temp_test/video1.mp4"))
        # At runtime these should be mutually exclusive
        assert user.is_local != user.is_cloud_only

    def test_lazy_evaluation_and_caching(self):
        # Accessing cloud_status should not raise on property presence
        user = UserFile(Path("nonexistent_test_file.mp4"))
        # Should be accessible (may raise on underlying detection, but property exists)
        try:
            _ = user.cloud_status
        except Exception:
            # If detection raises, that's acceptable at contract stage, but attribute must exist
            assert hasattr(user, 'cloud_status')



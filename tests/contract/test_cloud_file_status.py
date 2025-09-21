#!/usr/bin/env python3
"""
CloudFileStatus Enum Contract Tests for OneDrive Integration MVP

These tests validate the CloudFileStatus enum contract as specified in
specs/003-onedrive-compat-the/data-model.md

All tests MUST FAIL initially (TDD requirement) until implementation is complete.
"""

import pytest
from enum import Enum

# Import the CloudFileStatus enum (will fail until implemented)
try:
    from src.models.cloud_file_status import CloudFileStatus
except ImportError:
    # Expected to fail initially - create stub for testing
    class CloudFileStatus(Enum):
        """Stub for testing - will be replaced with real implementation"""

        pass


class TestCloudFileStatusContract:
    """Test CloudFileStatus enum contract compliance."""

    @pytest.mark.contract
    def test_cloud_file_status_enum_exists(self):
        """Test: CloudFileStatus enum exists and is an Enum."""
        # Contract: CloudFileStatus must be an Enum
        assert issubclass(
            CloudFileStatus, Enum
        ), "CloudFileStatus must inherit from Enum"

    @pytest.mark.contract
    def test_cloud_file_status_has_local_value(self):
        """Test: CloudFileStatus.LOCAL exists with correct value."""
        # Contract: LOCAL = "local"
        assert hasattr(
            CloudFileStatus, "LOCAL"
        ), "CloudFileStatus must have LOCAL value"
        assert CloudFileStatus.LOCAL.value == "local", "LOCAL value must be 'local'"

    @pytest.mark.contract
    def test_cloud_file_status_has_cloud_only_value(self):
        """Test: CloudFileStatus.CLOUD_ONLY exists with correct value."""
        # Contract: CLOUD_ONLY = "cloud_only"
        assert hasattr(
            CloudFileStatus, "CLOUD_ONLY"
        ), "CloudFileStatus must have CLOUD_ONLY value"
        assert (
            CloudFileStatus.CLOUD_ONLY.value == "cloud_only"
        ), "CLOUD_ONLY value must be 'cloud_only'"

    @pytest.mark.contract
    def test_cloud_file_status_mvp_only_values(self):
        """Test: CloudFileStatus contains only MVP values (LOCAL, CLOUD_ONLY)."""
        # Contract: MVP scope includes only LOCAL and CLOUD_ONLY
        expected_values = {"local", "cloud_only"}
        actual_values = {status.value for status in CloudFileStatus}

        assert (
            actual_values == expected_values
        ), f"MVP CloudFileStatus must contain only {expected_values}, got {actual_values}"

    @pytest.mark.contract
    def test_cloud_file_status_enum_string_representation(self):
        """Test: CloudFileStatus enum values have correct string representation."""
        # Contract: String representation should be the enum value
        assert str(CloudFileStatus.LOCAL) == "CloudFileStatus.LOCAL"
        assert str(CloudFileStatus.CLOUD_ONLY) == "CloudFileStatus.CLOUD_ONLY"

    @pytest.mark.contract
    def test_cloud_file_status_enum_equality(self):
        """Test: CloudFileStatus enum values support equality comparison."""
        # Contract: Enum values must support equality
        assert CloudFileStatus.LOCAL == CloudFileStatus.LOCAL
        assert CloudFileStatus.CLOUD_ONLY == CloudFileStatus.CLOUD_ONLY
        assert CloudFileStatus.LOCAL != CloudFileStatus.CLOUD_ONLY

    @pytest.mark.contract
    def test_cloud_file_status_enum_hashable(self):
        """Test: CloudFileStatus enum values are hashable (can be used in sets/dicts)."""
        # Contract: Enum values must be hashable
        status_set = {CloudFileStatus.LOCAL, CloudFileStatus.CLOUD_ONLY}
        assert len(status_set) == 2, "CloudFileStatus values must be hashable"

        status_dict = {
            CloudFileStatus.LOCAL: "local_file",
            CloudFileStatus.CLOUD_ONLY: "cloud_file",
        }
        assert len(status_dict) == 2, "CloudFileStatus values must work as dict keys"

    @pytest.mark.contract
    def test_cloud_file_status_iteration(self):
        """Test: CloudFileStatus enum supports iteration."""
        # Contract: Enum must be iterable
        statuses = list(CloudFileStatus)
        assert len(statuses) == 2, "CloudFileStatus must have exactly 2 values for MVP"
        assert CloudFileStatus.LOCAL in statuses, "LOCAL must be in iteration"
        assert CloudFileStatus.CLOUD_ONLY in statuses, "CLOUD_ONLY must be in iteration"

    @pytest.mark.contract
    def test_cloud_file_status_value_access(self):
        """Test: CloudFileStatus enum values are accessible by value."""
        # Contract: Enum values must be accessible by their string value
        assert CloudFileStatus("local") == CloudFileStatus.LOCAL
        assert CloudFileStatus("cloud_only") == CloudFileStatus.CLOUD_ONLY

    @pytest.mark.contract
    def test_cloud_file_status_invalid_value_raises_error(self):
        """Test: CloudFileStatus raises ValueError for invalid values."""
        # Contract: Invalid enum values must raise ValueError
        with pytest.raises(ValueError):
            CloudFileStatus("invalid_status")

        with pytest.raises(ValueError):
            CloudFileStatus("pinned")  # Future enhancement value, not in MVP

    @pytest.mark.contract
    def test_cloud_file_status_type_annotation_support(self):
        """Test: CloudFileStatus can be used in type annotations."""

        # Contract: Enum must support type annotations
        def test_function(status: CloudFileStatus) -> str:
            return status.value

        # Should work without type errors
        result = test_function(CloudFileStatus.LOCAL)
        assert result == "local"

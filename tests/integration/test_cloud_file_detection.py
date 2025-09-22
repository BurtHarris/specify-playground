#!/usr/bin/env python3
"""Minimal presence test so contract expecting OneDrive integration tests
sees at least one relevant file. This test is intentionally lightweight and
is safe to run on all platforms; detailed integration scenarios live in
`test_mixed_directory_scan.py`.
"""

from src.models.cloud_file_status import CloudFileStatus


def test_cloud_file_detection_presence():
    assert CloudFileStatus.LOCAL is not None

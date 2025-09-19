"""Compatibility fixtures and aliases for tests.

This file provides small shims so existing tests that still refer to the
older `VideoFile` names or `sample_video_files` fixture continue to work
while the codebase has migrated to `UserFile` and `sample_user_files`.

These shims are intentionally lightweight and only used for tests; they do
not change the production API.
"""
from pathlib import Path
import pytest

from src.models.user_file import UserFile

# Backwards-compatible alias for tests that still import VideoFile
VideoFile = UserFile


@pytest.fixture
def sample_video_files(request, tmp_path):
    """Alias fixture that mirrors sample_user_files semantics.

    Many older tests expect a fixture named `sample_video_files`. Tests should
    be migrated to `sample_user_files` and `UserFile` over time; this shim
    keeps the test-suite runnable during the migration.
    """
    # Create a small set of temporary files and return UserFile instances.
    files = []
    for i, suffix in enumerate(['.mp4', '.mkv', '.mov']):
        p = tmp_path / f"movie{i}{suffix}"
        p.write_bytes(b"test")
        files.append(UserFile(p))
    # Some tests expect a tuple (files, hash_value) in specific places; the
    # contract tests usually just need files, so return the list.
    return files

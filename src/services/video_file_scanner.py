"""Compatibility shim for historical VideoFileScanner API.

Tests and older code import VideoFileScanner from this module. The real
implementation lives in `file_scanner.py` as `FileScanner`. Export a
compatibility alias so both old imports and new code work.
"""
from .file_scanner import FileScanner as VideoFileScanner
from ..models.file import UserFile as VideoFile

# Provide backward-compatible names. Some older tests import
# VideoFileScanner (or rely on a global name VideoFile/FileScanner)
# without importing FileScanner explicitly. To be compatible, export
# the historical names and also place them on builtins so unqualified
# name lookups in test modules fall back to these classes.
import builtins

# Module-level aliases
FileScanner = VideoFileScanner

# Put compatibility symbols on builtins for legacy tests that expect them
setattr(builtins, 'VideoFile', VideoFile)
setattr(builtins, 'FileScanner', FileScanner)

__all__ = ["VideoFileScanner", "VideoFile", "FileScanner"]

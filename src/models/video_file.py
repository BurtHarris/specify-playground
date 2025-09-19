"""
Compatibility shim: export `VideoFile` name for code/tests that still import the old class name.

This project migrated to `UserFile` for generic file support. Some tests and modules
still import `src.models.video_file.VideoFile`. To keep older imports working during the
refactor, expose `VideoFile` as an alias of `UserFile`.
"""
from .user_file import UserFile

# Backwards-compatible name
VideoFile = UserFile

__all__ = ["UserFile", "VideoFile"]

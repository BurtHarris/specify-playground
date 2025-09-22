"""Compatibility module exporting the canonical UserFile implementation.

Re-export the concrete implementation from `src.models.user_file` so that
imports from `src.models.file` and `src.models.user_file` refer to the same
class object. This keeps isinstance checks consistent across tests and
legacy compatibility shims.
"""

from .user_file import UserFile

__all__ = ["UserFile"]

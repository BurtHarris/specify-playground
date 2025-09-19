from pathlib import Path
from typing import Optional

# Thin compatibility wrapper to unify the UserFile API across the codebase.
# Historically the project had a refactor that introduced `src.models.user_file.UserFile`.
# Many modules import `UserFile` from `src.models.file`; to avoid large, duplicated
# implementations we delegate to the concrete implementation in `user_file.py`.

from .user_file import UserFile as _UserFileImpl
from src.models.cloud_file_status import CloudFileStatus


class UserFile:
    """Compatibility wrapper around the real UserFile implementation.

    This wrapper preserves the constructor signature used across the codebase
    (path, size, is_local, cloud_status) and delegates behavior to the
    implementation in `src.models.user_file.UserFile` while exposing the
    attributes and methods tests and services expect (path, size, compute_hash,
    get_filename_without_extension, last_modified, extension, to_dict, etc.).
    """

    def __init__(self, path: Path, size: Optional[int] = None, is_local: bool = True, cloud_status: Optional[str] = None):
        # Accept either Path or string path
        path_obj = Path(path) if not isinstance(path, Path) else path
        self._impl = _UserFileImpl(path_obj)
        # If caller supplied a pre-known size, seed the implementation's cache
        if size is not None:
            try:
                self._impl._size = int(size)
            except Exception:
                pass
        if cloud_status is not None:
            # support both enum and raw value
            try:
                # If passed as string, convert to CloudFileStatus
                if isinstance(cloud_status, str):
                    try:
                        self._impl.cloud_status = CloudFileStatus.from_string(cloud_status)
                    except ValueError:
                        self._impl.cloud_status = cloud_status
                else:
                    self._impl.cloud_status = cloud_status
            except Exception:
                self._impl.cloud_status = cloud_status

        # Mirror simple flags expected elsewhere
        self.is_local = is_local

    # Delegate common attributes and methods to the underlying implementation
    def __getattr__(self, name):
        return getattr(self._impl, name)

    def __repr__(self):
        return repr(self._impl)

    def __eq__(self, other):
        if isinstance(other, UserFile):
            return self._impl == other._impl
        return self._impl == other

    def __hash__(self):
        return hash(self._impl)

    # Provide ordering support by delegating to the underlying Path string
    def __lt__(self, other):
        if isinstance(other, UserFile):
            return str(self._impl._path) < str(other._impl._path)
        # allow comparison with underlying impls
        return str(self._impl._path) < str(other)


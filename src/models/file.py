from pathlib import Path
from typing import Optional

class UserFile:
    def __init__(self, path: Path, size: int, is_local: bool = True, cloud_status: Optional[str] = None):
        self.path = path
        self.size = size
        self.is_local = is_local
        self.cloud_status = cloud_status

    @property
    def name(self):
        return self.path.name

    @property
    def extension(self):
        return self.path.suffix.lower()

    def __repr__(self):
        return f"<UserFile path={self.path} size={self.size} local={self.is_local} cloud_status={self.cloud_status}>"

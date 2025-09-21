class DatabaseError(Exception):
    """Base class for database-related errors."""


class DatabaseCorruptError(DatabaseError):
    """Raised when the on-disk database is corrupt or unusable."""


class DatabaseNotConfiguredError(DatabaseError):
    """Raised when no database path was provided but DB operations were requested."""

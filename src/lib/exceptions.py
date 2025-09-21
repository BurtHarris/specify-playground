class DatabaseError(Exception):
    """Base exception for database related errors."""


class DatabaseCorruptError(DatabaseError):
    """Raised when the on-disk database is corrupt or cannot be opened."""


class DatabaseNotConfiguredError(DatabaseError):
    """Raised when callers attempt DB operations without configuring a path."""
class DatabaseError(Exception):
    """Base class for database-related errors."""


class DatabaseCorruptError(DatabaseError):
    """Raised when the on-disk database is corrupt or unusable."""


class DatabaseNotConfiguredError(DatabaseError):
    """Raised when no database path was provided but DB operations were requested."""

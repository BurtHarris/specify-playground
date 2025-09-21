from typing import Protocol, runtime_checkable, Any, List


@runtime_checkable
class LoggerProtocol(Protocol):
    """Structural protocol describing the minimal logger surface used by the app.

    This is intentionally small and mirrors the stdlib `logging.Logger` API
    used across the codebase. The Protocol allows tests to supply lightweight
    stubs that satisfy the interface (structural typing) and enables mypy
    to statically validate overrides.
    """

    handlers: List[Any]

    def debug(self, msg: str, *args: Any, **kwargs: Any) -> None:
        ...

    def info(self, msg: str, *args: Any, **kwargs: Any) -> None:
        ...

    def warning(self, msg: str, *args: Any, **kwargs: Any) -> None:
        ...

    def error(self, msg: str, *args: Any, **kwargs: Any) -> None:
        ...

    def exception(self, msg: str, *args: Any, **kwargs: Any) -> None:
        ...

    def setLevel(self, level: int) -> None:
        ...


@runtime_checkable
class ProgressReporterProtocol(Protocol):
    """Protocol for progress reporting components used by scanning/detection."""

    def start_progress(self, total: int, label: str) -> None:
        ...

    def update_progress(self, idx: int, name: str) -> None:
        ...

    def finish_progress(self) -> None:
        ...


@runtime_checkable
class HasherProtocol(Protocol):
    """Protocol for hasher callables used to compute file hashes.

    Expected to be a callable accepting a pathlib.Path and optional
    chunk_size (int) and returning a string hash value.
    """

    def __call__(self, path: "pathlib.Path", chunk_size: int = ...) -> str:
        ...


@runtime_checkable
class FileDatabaseProtocol(Protocol):
    """Protocol for lightweight file-hash cache/database providers."""

    def get_cached_hash(self, path: "pathlib.Path", size: int, mtime: float) -> Any:
        ...

    def set_cached_hash(
        self, path: "pathlib.Path", size: int, mtime: float, hashv: str
    ) -> None:
        ...


@runtime_checkable
class ConfigManagerProtocol(Protocol):
    """Protocol for configuration manager used by the CLI and services."""

    DEFAULT_CONFIG: Any

    def load_config(self) -> dict:
        ...

    def add_scan_history(
        self, directory: "pathlib.Path", file_count: int, duplicates_found: int
    ) -> None:
        ...


@runtime_checkable
class ResultExporterProtocol(Protocol):
    """Protocol for result exporters (YAML/JSON) used by the CLI."""

    def export_yaml(self, scan_result: Any, path: "pathlib.Path") -> None:
        ...

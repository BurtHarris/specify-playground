from dependency_injector import containers, providers
import logging

from src.services.progress_reporter import ProgressReporter
from src.services.file_hasher import stream_hash
from src.services.file_database import get_database
from src.lib.config_manager import ConfigManager
from src.lib.interfaces import LoggerProtocol
import sys
from typing import Optional


def _make_logger(name: str = "video_duplicate_scanner", level: Optional[str] = None):
    """Helper to create and configure a stdlib logger from container config.

    The function deliberately keeps configuration minimal: it sets level
    (if provided) and ensures at least one StreamHandler exists so logs
    are visible during CLI runs and tests. Tests can override the provider
    to inject a dummy/logger stub if needed.
    """
    logger = logging.getLogger(name)
    # Configure level from provided value (string) or default to INFO
    lvl = logging.INFO
    if level:
        try:
            lvl = getattr(logging, level.upper(), logging.INFO)
        except Exception:
            lvl = logging.INFO
    logger.setLevel(lvl)

    # Add a default StreamHandler if no handlers are configured. This keeps
    # output visible when run as a CLI but avoids double-handling in tests
    # that configure the root logger.
    if not logger.handlers:
        handler = logging.StreamHandler(stream=sys.stderr)
        formatter = logging.Formatter(
            "%(asctime)s %(levelname)s [%(name)s] %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


class Container(containers.DeclarativeContainer):
    """Application dependency container.

    Provides:
    - logger: configured stdlib logger
    - progress_reporter_factory: factory for ProgressReporter instances
    """

    config = providers.Configuration()

    # Logger provider: configured via container.config.logger.level (optional)
    # Example usage in tests:
    #   container.config.logger.level.from_value('DEBUG')
    #   container.logger()
    logger: providers.Singleton[LoggerProtocol] = providers.Singleton(
        _make_logger,
        name=providers.Callable(lambda: "video_duplicate_scanner"),
        level=config.logger.level,
    )

    # Factory that creates ProgressReporter instances; callers should pass
    # `enabled` boolean at call time (providers.Factory will forward args).
    progress_reporter_factory = providers.Factory(ProgressReporter)

    # Hasher provider: exposes the streaming hasher callable so tests can
    # inject alternate implementations. Use Object to return the callable
    # itself (consumers expect a callable that accepts (path, chunk_size,...)).
    hasher = providers.Object(stream_hash)

    # Database provider: factory that wraps get_database so callers can
    # request a DB instance bound to a specific path.
    database = providers.Factory(get_database)

    # ConfigManager provider: allows tests to replace config handling
    # or supply pre-populated config instances.
    config_manager = providers.Singleton(ConfigManager)

    # Progress reporter alias: keep a short name in addition to
    # `progress_reporter_factory` for readability. Tests may override this
    # provider using `container.progress_reporter.override(...)`.
    progress_reporter = progress_reporter_factory = providers.Factory(ProgressReporter)

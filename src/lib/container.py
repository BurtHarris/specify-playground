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

    # Ensure at least one handler exists and prefer writing to stdout so
    # test captures of STDOUT include informational logs. If Rich is
    # available, prefer RichHandler for nicer formatting; otherwise add a
    # StreamHandler to stdout. Avoid adding duplicate handlers on repeated
    # _make_logger calls.
    try:
        has_any_handler = any(isinstance(h, logging.Handler) for h in logger.handlers)
    except Exception:
        has_any_handler = False

    if not has_any_handler:
        try:
            # Try to use RichHandler (writes to console/stdout by default)
            from rich.logging import RichHandler  # type: ignore
            from rich.console import Console  # type: ignore

            console = Console()
            rich_handler = RichHandler(console=console, rich_tracebacks=True)
            logger.addHandler(rich_handler)
            # Also add a simple stderr StreamHandler so legacy tests and
            # environments that assert the presence of a StreamHandler
            # can continue to pass. Avoid duplicate handlers by checking
            # existing handler types.
            try:
                has_stream = any(isinstance(h, logging.StreamHandler) for h in logger.handlers)
            except Exception:
                has_stream = False
            if not has_stream:
                handler = logging.StreamHandler(stream=sys.stderr)
                formatter = logging.Formatter(
                    "%(asctime)s %(levelname)s [%(name)s] %(message)s"
                )
                handler.setFormatter(formatter)
                logger.addHandler(handler)
        except Exception:
            # Fall back to stdout StreamHandler
            handler = logging.StreamHandler(stream=sys.stdout)
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

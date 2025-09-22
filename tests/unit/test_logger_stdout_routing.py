import logging
import sys

from src.lib.container import Container
from src.cli.main import _reconfigure_logger_for_stdout


def test_reconfigure_logger_for_stdout_adds_stdout_handler(tmp_path):
    c = Container()
    logger = c.logger()

    # Ensure the logger initially has at least one StreamHandler (stderr by default)
    assert any(isinstance(h, logging.StreamHandler) for h in logger.handlers)

    # Reconfigure to redirect to stdout
    _reconfigure_logger_for_stdout(logger)

    # Now a StreamHandler with stream == sys.stdout should be present
    assert any(isinstance(h, logging.StreamHandler) and getattr(h, "stream", None) is sys.stdout for h in logger.handlers)

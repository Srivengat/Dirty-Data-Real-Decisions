"""Production logging configuration for the analysis pipeline."""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logging(
    log_level: int = logging.INFO,
    log_file: Optional[Path] = None,
) -> None:
    """Configure root and package logging format and output streams.

    Args:
        log_level: Standard logging level (e.g. logging.INFO, logging.DEBUG).
        log_file: Optional path to write persistent application logs.
    """
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Configure root handler for console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Avoid duplicate handlers if setup is called multiple times
    if not root_logger.handlers:
        root_logger.addHandler(console_handler)

    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(str(log_file), encoding="utf-8")
        file_handler.setFormatter(formatter)
        file_handler.setLevel(log_level)
        root_logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """Retrieve a namespaced logger instance.

    Args:
        name: Name of the module requesting a logger (typically __name__).

    Returns:
        logging.Logger: Configured logger instance.
    """
    return logging.getLogger(name)

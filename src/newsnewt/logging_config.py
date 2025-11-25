"""Logging configuration for NewsNewt."""

import logging
import sys
from logging.handlers import RotatingFileHandler

from newsnewt.config import settings


def setup_logging() -> None:
    """Configure application logging."""
    # Create log directory if it doesn't exist
    settings.log_dir.mkdir(parents=True, exist_ok=True)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level.upper()))

    # Clear any existing handlers
    root_logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S UTC",
    )

    # File handler with rotation
    file_handler = RotatingFileHandler(
        filename=settings.log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(getattr(logging, settings.log_level.upper()))
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Console handler (for development/debugging)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, settings.log_level.upper()))
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Log initialization
    logger = logging.getLogger(__name__)
    logger.info(
        f"Logging configured: level={settings.log_level}, file={settings.log_file}"
    )


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a module.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance

    """
    return logging.getLogger(name)

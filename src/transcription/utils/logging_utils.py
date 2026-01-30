"""Logging utilities for the transcription system.

Provides centralized logging configuration with support for:
- Console output
- File logging
- Structured formatting
- Context-aware loggers
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional

from transcription.config import config


def setup_logging(
    name: str,
    level: Optional[str] = None,
    log_file: Optional[Path] = None,
    console: bool = True,
) -> logging.Logger:
    """Setup and configure a logger instance.

    Args:
        name: Logger name (typically __name__)
        level: Log level (DEBUG, INFO, WARNING, ERROR). Defaults to config.
        log_file: Optional specific log file path. Defaults to config.
        console: Whether to output to console. Defaults to True.

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Set level
    log_level = level or config.logging.level
    logger.setLevel(getattr(logging, log_level.upper()))

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(config.logging.format_string)

    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logger.level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # File handler
    if config.logging.file_logging:
        file_path = log_file or config.logging.log_file
        try:
            file_handler = logging.FileHandler(file_path, encoding="utf-8")
            file_handler.setLevel(logger.level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except (OSError, PermissionError) as e:
            # Log to console that file logging failed
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            console_handler.setLevel(logging.WARNING)
            logger.addHandler(console_handler)
            logger.warning(f"Could not setup file logging: {e}")

    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with default configuration.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


class LogContext:
    """Context manager for temporary log level changes."""

    def __init__(self, logger: logging.Logger, level: str):
        """Initialize context manager.

        Args:
            logger: Logger to modify
            level: Temporary level to set
        """
        self.logger = logger
        self.original_level = logger.level
        self.temporary_level = getattr(logging, level.upper())

    def __enter__(self) -> logging.Logger:
        """Enter context - set temporary level."""
        self.logger.setLevel(self.temporary_level)
        for handler in self.logger.handlers:
            handler.setLevel(self.temporary_level)
        return self.logger

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context - restore original level."""
        self.logger.setLevel(self.original_level)
        for handler in self.logger.handlers:
            handler.setLevel(self.original_level)

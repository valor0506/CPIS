"""Logging configuration for CPIS.

This module initializes standard library logging with clean formatting
and outputs to both console and rotation files.
"""

import logging
import os
from pathlib import Path

from src.core.config.config import get_settings


def setup_logger(name: str = "cpis") -> logging.Logger:
    """Configure and return a logger instance with console and file handlers.

    Args:
        name: Name of the logger.

    Returns:
        logging.Logger: Configured logger.
    """
    logger = logging.getLogger(name)

    # If the logger is already configured, return it
    if logger.handlers:
        return logger

    settings = get_settings()
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(log_level)

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] [%(filename)s:%(lineno)d] - %(message)s"
    )

    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File Handler
    if settings.LOG_FILE_PATH:
        try:
            log_path = Path(settings.LOG_FILE_PATH)
            # Create logging folder if it doesn't exist
            log_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = logging.FileHandler(log_path, encoding="utf-8")
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            # Fall back to console only if file creation fails
            logger.warning(
                f"Failed to initialize file logger at {settings.LOG_FILE_PATH}: {str(e)}. "
                "Defaulting to console-only logging."
            )

    return logger

"""
Logging utilities
"""

import logging
import sys
from pathlib import Path
from loguru import logger


def setup_logging(log_level: str = "INFO", log_file: str = "logs/agents.log"):
    """
    Setup logging configuration

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Path to log file
    """
    # Create logs directory
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)

    # Remove default logger
    logger.remove()

    # Add console handler
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level=log_level,
        colorize=True
    )

    # Add file handler
    logger.add(
        log_file,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} - {message}",
        level=log_level,
        rotation="10 MB",
        retention="1 week",
        compression="zip"
    )

    return logger

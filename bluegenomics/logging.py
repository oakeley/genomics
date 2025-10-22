"""
Logging utilities for BlueGenomics
"""

import logging
import sys

__all__ = ['configure_log_level', 'get_logger', 'LOG']


def configure_log_level(logger_name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Configure logging level for a specific logger.

    Args:
        logger_name: Name of the logger
        level: Logging level (default INFO)

    Returns:
        Configured logger
    """
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def get_logger(logger_name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Get a configured logger instance.

    Args:
        logger_name: Name of the logger
        level: Logging level (default INFO)

    Returns:
        Configured logger instance
    """
    return configure_log_level(logger_name, level)


# Create default logger
LOG = configure_log_level("bluegenomics")

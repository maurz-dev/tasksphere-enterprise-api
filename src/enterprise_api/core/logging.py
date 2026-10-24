"""Structured application logging configuration."""

import logging
import sys


def setup_logging() -> logging.Logger:
    """Configure enterprise-level logger formatting."""
    log_format = (
        "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s"
    )
    date_format = "%Y-%m-%d %H:%M:%S"

    logger = logging.getLogger("enterprise_api")
    logger.setLevel(logging.DEBUG)

    # Avoid duplicate handlers if re-initialized
    if not logger.handlers:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter(fmt=log_format, datefmt=date_format)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger


logger = setup_logging()

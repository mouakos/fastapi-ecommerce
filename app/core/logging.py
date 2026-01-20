"""Logging configuration."""

import sys
from datetime import datetime
from pathlib import Path

from loguru import logger

# Logs directory inside app/
log_dir = Path("logs")
log_dir.mkdir(parents=True, exist_ok=True)

LOG_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level>"
)

# Remove default handler to avoid duplicate logs
logger.remove()

# Configure console logging
logger.add(
    sys.stdout,
    format=LOG_FORMAT,
    level="INFO",
    enqueue=True,
    colorize=True,
    backtrace=True,
    diagnose=True,
)

# Configure file logging
logger.add(
    log_dir / f"{datetime.now().strftime('%Y-%m-%d')}.json",
    serialize=True,
    rotation="10 MB",
    retention="10 days",
    compression="zip",
    level="INFO",
    enqueue=True,
    format=LOG_FORMAT,
)

# Export the logger instance
__all__ = ["logger"]

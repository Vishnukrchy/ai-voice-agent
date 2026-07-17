"""Centralized structured logger. Every API call, LLM request, Twilio event,
error, and conversation turn should be logged through this module."""
import sys
from pathlib import Path

from loguru import logger

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

logger.remove()
logger.add(sys.stdout, level="INFO", colorize=True,
           format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | {message}")
logger.add(LOG_DIR / "app.log", rotation="10 MB", retention="14 days", level="DEBUG",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}")
logger.add(LOG_DIR / "errors.log", rotation="10 MB", retention="30 days", level="ERROR")

__all__ = ["logger"]

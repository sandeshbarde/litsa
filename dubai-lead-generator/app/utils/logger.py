"""
Centralized logger using loguru.
Never logs API keys, passwords, or private credentials.
"""

import sys
import re
from pathlib import Path
from loguru import logger

from app.config import yaml_config

_SECRET_PATTERN = re.compile(
    r"(key|password|secret|token|credential|auth)\s*[=:]\s*\S+",
    re.IGNORECASE,
)


class SecretFilter:
    """Loguru sink filter that redacts secrets from log records."""

    def __call__(self, message: str) -> str:
        return _SECRET_PATTERN.sub(r"\1=[REDACTED]", message)


def setup_logger() -> None:
    """Configure loguru with file sinks and console output."""
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    log_cfg = yaml_config.logging_config
    level = log_cfg.get("level", "INFO")
    rotation = log_cfg.get("rotation", "10 MB")
    retention = log_cfg.get("retention", "30 days")

    # Remove default handler
    logger.remove()

    # Console handler
    logger.add(
        sys.stderr,
        level=level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        filter=lambda record: True,
    )

    # Main log file
    logger.add(
        logs_dir / "app.log",
        level=level,
        rotation=rotation,
        retention=retention,
        encoding="utf-8",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{line} - {message}",
    )

    # Error-only log file
    logger.add(
        logs_dir / "errors.log",
        level="ERROR",
        rotation=rotation,
        retention=retention,
        encoding="utf-8",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{line} - {message}\n{exception}",
    )


# Initialize on import
setup_logger()

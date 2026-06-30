"""Logging helpers for WonderCubs Studio."""
from __future__ import annotations

import logging
from pathlib import Path

LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"


def configure_logging(log_file: Path) -> None:
    """Configure application-wide logging."""
    log_file.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format=LOG_FORMAT,
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def get_logger(name: str) -> logging.Logger:
    """Return a configured logger."""
    return logging.getLogger(name)

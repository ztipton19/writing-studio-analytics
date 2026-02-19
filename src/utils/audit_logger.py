"""Structured audit logging for desktop operations."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

_LOGGER_NAME = "writing_studio_audit"


def _log_path() -> Path:
    base = os.getenv("LOCALAPPDATA")
    if base:
        root = Path(base) / "WritingStudioAnalytics"
    else:
        root = Path.home() / ".writing-studio-analytics"
    root.mkdir(parents=True, exist_ok=True)
    return root / "audit.log"


def get_audit_logger() -> logging.Logger:
    logger = logging.getLogger(_LOGGER_NAME)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(_log_path(), encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
    logger.propagate = False
    return logger


def audit_event(event: str, **fields: Any) -> None:
    payload: Dict[str, Any] = {
        "ts": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "event": event,
    }
    payload.update(fields)
    get_audit_logger().info(json.dumps(payload, default=str))

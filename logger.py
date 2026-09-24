"""
Simple logger used by DeskFlow.
Stores logs in memory so they can be viewed from /trace.
"""

import logging
from datetime import datetime, timezone
from collections import deque

_BUFFER_SIZE = 500
_log_buffer: deque = deque(maxlen=_BUFFER_SIZE)

# setup logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
_logger = logging.getLogger("DeskFlow")


def log(message: str, level: str = "info") -> None:
    """Add log entry."""
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "level": level.upper(),
        "msg": message,
    }
    _log_buffer.append(entry)
    getattr(_logger, level, _logger.info)(message)


def get_logs() -> list[dict]:
    """Get logs."""
    return list(_log_buffer)


def clear_logs() -> None:
    _log_buffer.clear()

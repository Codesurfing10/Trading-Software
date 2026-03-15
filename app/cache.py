"""Simple in-memory TTL cache shared across providers."""

from __future__ import annotations

import time
from typing import Any, Optional, Tuple

_store: dict[str, Tuple[float, Any]] = {}


def get(key: str) -> Optional[Any]:
    entry = _store.get(key)
    if entry is None:
        return None
    expires_at, value = entry
    if time.monotonic() > expires_at:
        del _store[key]
        return None
    return value


def set(key: str, value: Any, ttl: int = 60) -> None:  # noqa: A001
    _store[key] = (time.monotonic() + ttl, value)


def invalidate(key: str) -> None:
    _store.pop(key, None)

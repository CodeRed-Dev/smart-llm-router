"""
Cache Module

Provides in-memory TTL caching for LLM responses to improve performance
and reduce costs for repeated queries.
"""

import time
from typing import Any, Optional
from threading import Lock
from app.config import settings

class Cache:
    def __init__(self):
        self._cache = {}
        self._lock = Lock()
        self._ttl_seconds = settings.CACHE_TTL_SECONDS

    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from cache if it exists and hasn't expired.
        """
        with self._lock:
            if key in self._cache:
                value, timestamp = self._cache[key]
                if time.time() - timestamp < self._ttl_seconds:
                    return value
                else:
                    # Expired, remove it
                    del self._cache[key]
        return None

    def set(self, key: str, value: Any) -> None:
        """
        Set a value in cache with current timestamp.
        """
        with self._lock:
            self._cache[key] = (value, time.time())

    def clear(self) -> None:
        """
        Clear all cached values.
        """
        with self._lock:
            self._cache.clear()

    def size(self) -> int:
        """
        Get the current number of cached items.
        """
        with self._lock:
            # Clean expired entries
            current_time = time.time()
            expired_keys = [
                k for k, (_, ts) in self._cache.items()
                if current_time - ts >= self._ttl_seconds
            ]
            for k in expired_keys:
                del self._cache[k]
            return len(self._cache)
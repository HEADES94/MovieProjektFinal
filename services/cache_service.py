"""Cache service for better performance."""
from functools import wraps
import time
from typing import Any, Dict, Optional


class SimpleCache:
    """Simple in-memory cache implementation."""

    def __init__(self, default_timeout: int = 300):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.default_timeout = default_timeout

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if key in self._cache:
            data = self._cache[key]
            if time.time() < data['expires']:
                return data['value']
            else:
                del self._cache[key]
        return None

    def set(self, key: str, value: Any, timeout: Optional[int] = None) -> None:
        """Set value in cache."""
        timeout = timeout or self.default_timeout
        self._cache[key] = {
            'value': value,
            'expires': time.time() + timeout
        }

    def delete(self, key: str) -> None:
        """Delete value from cache."""
        self._cache.pop(key, None)

    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()


cache = SimpleCache()


def cached(timeout: int = 300, key_prefix: str = ""):
    """Decorator for caching function results."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(kwargs))}"

            result = cache.get(cache_key)
            if result is not None:
                return result

            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout)
            return result
        return wrapper
    return decorator

"""API Rate Limiting and Monitoring."""
from functools import wraps
from time import time
from typing import Dict, Optional
from flask import request, jsonify, g
import logging


class RateLimiter:
    """Rate limiter implementation for API endpoints."""

    def __init__(self):
        self.requests: Dict[str, list] = {}

    def is_allowed(self, key: str, limit: int, window: int) -> bool:
        """Check if request is allowed based on rate limit."""
        now = time()

        if key not in self.requests:
            self.requests[key] = []

        # Remove old requests outside the time window
        self.requests[key] = [req_time for req_time in self.requests[key]
                             if now - req_time < window]

        # Check if limit is reached
        if len(self.requests[key]) >= limit:
            return False

        # Add current request
        self.requests[key].append(now)
        return True

    def get_remaining_requests(self, key: str, limit: int, window: int) -> int:
        """Get remaining requests for a key."""
        now = time()

        if key not in self.requests:
            return limit

        valid_requests = [req_time for req_time in self.requests[key]
                         if now - req_time < window]

        return max(0, limit - len(valid_requests))

    def get_reset_time(self, key: str, window: int) -> Optional[float]:
        """Get time until rate limit resets."""
        if key not in self.requests or not self.requests[key]:
            return None

        oldest_request = min(self.requests[key])
        reset_time = oldest_request + window

        return max(0, reset_time - time())


rate_limiter = RateLimiter()


def rate_limit(limit: int = 100, window: int = 3600, per: str = 'ip'):
    """
    Rate limiting decorator.

    Args:
        limit: Number of allowed requests
        window: Time window in seconds
        per: 'ip' or 'user'
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if per == 'ip':
                key = request.remote_addr
            elif per == 'user':
                key = getattr(g, 'user_id', request.remote_addr)
            else:
                key = request.remote_addr

            if not rate_limiter.is_allowed(key, limit, window):
                remaining = rate_limiter.get_remaining_requests(key, limit, window)
                reset_time = rate_limiter.get_reset_time(key, window)

                logging.warning(f"Rate limit exceeded for {key}")

                return jsonify({
                    'error': 'Rate limit exceeded',
                    'limit': limit,
                    'window': window,
                    'remaining': remaining,
                    'reset_time': reset_time
                }), 429

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def api_rate_limit(limit: int = 60, window: int = 60):
    """Rate limit for API endpoints (60 requests per minute)."""
    return rate_limit(limit=limit, window=window, per='ip')


def user_rate_limit(limit: int = 30, window: int = 60):
    """Rate limit for user-specific actions (30 requests per minute)."""
    return rate_limit(limit=limit, window=window, per='user')


def strict_rate_limit(limit: int = 10, window: int = 60):
    """Strict rate limit for sensitive operations (10 requests per minute)."""
    return rate_limit(limit=limit, window=window, per='user')


class RequestMonitor:
    """Monitor and log API requests."""

    def __init__(self):
        self.request_stats: Dict[str, Dict] = {}

    def log_request(self, endpoint: str, method: str, response_time: float,
                   status_code: int, user_id: Optional[str] = None):
        """Log a request for monitoring."""
        key = f"{method} {endpoint}"

        if key not in self.request_stats:
            self.request_stats[key] = {
                'count': 0,
                'total_time': 0,
                'errors': 0,
                'last_accessed': time()
            }

        stats = self.request_stats[key]
        stats['count'] += 1
        stats['total_time'] += response_time
        stats['last_accessed'] = time()

        if status_code >= 400:
            stats['errors'] += 1

        # Log slow requests
        if response_time > 2.0:
            logging.warning(f"Slow request: {key} took {response_time:.2f}s")

        # Log errors
        if status_code >= 500:
            logging.error(f"Server error: {key} returned {status_code}")

    def get_stats(self) -> Dict:
        """Get request statistics."""
        return {
            endpoint: {
                'count': stats['count'],
                'avg_time': stats['total_time'] / stats['count'],
                'error_rate': stats['errors'] / stats['count'] * 100,
                'last_accessed': stats['last_accessed']
            }
            for endpoint, stats in self.request_stats.items()
        }


request_monitor = RequestMonitor()


def monitor_requests(f):
    """Decorator to monitor request performance."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time()

        try:
            result = f(*args, **kwargs)
            status_code = getattr(result, 'status_code', 200)
        except Exception as e:
            status_code = 500
            logging.error(f"Request failed: {str(e)}")
            raise
        finally:
            response_time = time() - start_time

            request_monitor.log_request(
                endpoint=request.endpoint or 'unknown',
                method=request.method,
                response_time=response_time,
                status_code=status_code,
                user_id=getattr(g, 'user_id', None)
            )

        return result
    return decorated_function

"""
Simple in-memory rate limiter using cachetools TTLCache.
"""
import time
import os
from functools import wraps
from flask import request, jsonify, current_app
from cachetools import TTLCache

# Cache stores { ip_address: {"count": int, "first": timestamp} }
_rate_cache = None

def _get_cache():
    global _rate_cache
    if _rate_cache is None:
        max_clients = int(os.getenv("RATE_LIMIT_CACHE_SIZE", 10000))
        window = int(os.getenv("RATE_LIMIT_WINDOW", 60))
        _rate_cache = TTLCache(maxsize=max_clients, ttl=window)
    return _rate_cache

def rate_limit(max_requests=None, window_seconds=None):
    """
    Decorator for rate limiting Flask endpoints.
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            cache = _get_cache()
            client_ip = request.remote_addr or "unknown"
            max_req = max_requests or current_app.config["RATE_LIMIT_MAX_REQUESTS"]
            window = window_seconds or current_app.config["RATE_LIMIT_WINDOW"]

            data = cache.get(client_ip)
            if not data:
                cache[client_ip] = {"count": 1, "first": time.time()}
            else:
                if data["count"] >= max_req:
                    retry_after = cache.ttl(client_ip)
                    return jsonify({
                        "error": "rate_limit_exceeded",
                        "retry_after": retry_after
                    }), 429
                data["count"] += 1
                cache[client_ip] = data

            return f(*args, **kwargs)
        return wrapper
    return decorator

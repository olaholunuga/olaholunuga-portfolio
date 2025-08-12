"""
Lightweight caching service.
Supports in-memory cache (fast) or optional file-backed cache using shelve.
"""
import time
import shelve
from cachetools import TTLCache

class CacheService:
    def __init__(self, use_file=False, file_path='./.cache_store', maxsize=1024, ttl=3600):
        self.use_file = use_file
        self.maxsize = maxsize
        self.ttl = ttl
        self.in_memory = TTLCache(maxsize=maxsize, ttl=ttl)
        self.file_path = file_path
        self._shelf = None  # Lazy open for file cache

    def _open_shelf(self):
        if not self._shelf:
            self._shelf = shelve.open(self.file_path, writeback=True)
        return self._shelf

    def set(self, key, value, ttl=None):
        ttl = ttl or self.ttl
        if self.use_file:
            shelf = self._open_shelf()
            shelf[key] = {"value": value, "cached_at": time.time(), "ttl": ttl}
            shelf.sync()
        else:
            self.in_memory[key] = {"value": value, "cached_at": time.time()}

    def get(self, key):
        if self.use_file:
            shelf = self._open_shelf()
            data = shelf.get(key)
            if not data:
                return None
            if time.time() - data["cached_at"] > data["ttl"]:
                del shelf[key]
                shelf.sync()
                return None
            return data["value"]
        else:
            val = self.in_memory.get(key)
            return None if not val else val["value"]

    def close(self):
        if self.use_file and self._shelf:
            self._shelf.close()
            self._shelf = None

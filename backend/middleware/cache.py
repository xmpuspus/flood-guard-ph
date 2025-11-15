"""LRU cache implementation for API responses

Enhancement #16: Implement Caching with LRU cache
"""
import hashlib
import json
import time
import logging
from typing import Any, Optional, Dict
from collections import OrderedDict
from threading import Lock

logger = logging.getLogger(__name__)


class LRUCache:
    """Thread-safe LRU cache with TTL support"""

    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        """
        Args:
            max_size: Maximum number of items in cache
            default_ttl: Default time-to-live in seconds (5 minutes)
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: OrderedDict = OrderedDict()
        self.timestamps: Dict[str, float] = {}
        self.lock = Lock()
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Optional[Any]:
        """Get item from cache"""
        with self.lock:
            if key not in self.cache:
                self.misses += 1
                return None

            # Check if expired
            if self._is_expired(key):
                self._remove(key)
                self.misses += 1
                return None

            # Move to end (most recently used)
            self.cache.move_to_end(key)
            self.hits += 1
            return self.cache[key]

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set item in cache"""
        with self.lock:
            # Remove if exists (to update position)
            if key in self.cache:
                self._remove(key)

            # Add new item
            self.cache[key] = value
            self.timestamps[key] = time.time()

            # Enforce size limit (remove oldest)
            if len(self.cache) > self.max_size:
                oldest_key = next(iter(self.cache))
                self._remove(oldest_key)

    def invalidate(self, key: str):
        """Remove item from cache"""
        with self.lock:
            self._remove(key)

    def clear(self):
        """Clear entire cache"""
        with self.lock:
            self.cache.clear()
            self.timestamps.clear()
            logger.info("Cache cleared")

    def get_stats(self) -> Dict:
        """Get cache statistics"""
        with self.lock:
            total = self.hits + self.misses
            hit_rate = (self.hits / total * 100) if total > 0 else 0

            return {
                "size": len(self.cache),
                "max_size": self.max_size,
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate": round(hit_rate, 2),
                "utilization": round(len(self.cache) / self.max_size * 100, 2)
            }

    def _is_expired(self, key: str) -> bool:
        """Check if cache entry is expired"""
        if key not in self.timestamps:
            return True

        age = time.time() - self.timestamps[key]
        return age > self.default_ttl

    def _remove(self, key: str):
        """Remove item (internal, assumes lock held)"""
        if key in self.cache:
            del self.cache[key]
        if key in self.timestamps:
            del self.timestamps[key]


class CacheManager:
    """
    Multi-tier cache manager

    Caches:
    - Search results (5 min TTL)
    - Project stats (10 min TTL)
    - News articles (15 min TTL)
    """

    def __init__(self):
        # Separate caches for different data types
        self.search_cache = LRUCache(max_size=500, default_ttl=300)  # 5 min
        self.stats_cache = LRUCache(max_size=200, default_ttl=600)   # 10 min
        self.news_cache = LRUCache(max_size=300, default_ttl=900)    # 15 min

    def generate_key(self, prefix: str, params: Dict) -> str:
        """Generate cache key from parameters"""
        # Sort params for consistent keys
        sorted_params = json.dumps(params, sort_keys=True)
        hash_key = hashlib.md5(sorted_params.encode()).hexdigest()
        return f"{prefix}:{hash_key}"

    def get_search_result(self, filters: Dict) -> Optional[Any]:
        """Get cached search result"""
        key = self.generate_key("search", filters)
        return self.search_cache.get(key)

    def set_search_result(self, filters: Dict, result: Any):
        """Cache search result"""
        key = self.generate_key("search", filters)
        self.search_cache.set(key, result)
        logger.debug(f"Cached search result: {key}")

    def get_stats(self, filters: Dict) -> Optional[Any]:
        """Get cached stats"""
        key = self.generate_key("stats", filters)
        return self.stats_cache.get(key)

    def set_stats(self, filters: Dict, stats: Any):
        """Cache stats"""
        key = self.generate_key("stats", filters)
        self.stats_cache.set(key, stats)
        logger.debug(f"Cached stats: {key}")

    def get_news(self, query: str, params: Dict) -> Optional[Any]:
        """Get cached news"""
        cache_params = {"query": query, **params}
        key = self.generate_key("news", cache_params)
        return self.news_cache.get(key)

    def set_news(self, query: str, params: Dict, articles: Any):
        """Cache news"""
        cache_params = {"query": query, **params}
        key = self.generate_key("news", cache_params)
        self.news_cache.set(key, articles)
        logger.debug(f"Cached news: {key}")

    def invalidate_all_search(self):
        """Invalidate all search caches (e.g., when data updated)"""
        self.search_cache.clear()
        self.stats_cache.clear()
        logger.info("Invalidated search and stats caches")

    def get_all_stats(self) -> Dict:
        """Get statistics for all caches"""
        return {
            "search_cache": self.search_cache.get_stats(),
            "stats_cache": self.stats_cache.get_stats(),
            "news_cache": self.news_cache.get_stats()
        }


# Global cache manager instance
cache_manager = CacheManager()

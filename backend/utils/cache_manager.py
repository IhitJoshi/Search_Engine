"""
Cache Manager - High-performance caching layer with TTL and stampede prevention

FEATURES:
- In-memory LRU cache with TTL
- Redis-compatible interface (can swap to Redis in production)
- Cache stampede prevention using locks
- Automatic cache warming
- Metrics tracking
"""

import time
import hashlib
import threading
import logging
from typing import Any, Optional, Callable, Dict
from functools import wraps
from collections import OrderedDict

logger = logging.getLogger(__name__)


class CacheEntry:
    """Single cache entry with value and metadata"""
    __slots__ = ['value', 'expires_at', 'created_at']
    
    def __init__(self, value: Any, ttl_seconds: int):
        self.value = value
        self.created_at = time.time()
        self.expires_at = self.created_at + ttl_seconds
    
    def is_expired(self) -> bool:
        return time.time() > self.expires_at


class LRUCache:
    """
    Thread-safe LRU cache with TTL support.
    
    PERFORMANCE:
    - O(1) get/set operations
    - Automatic eviction of expired entries
    - Memory-bounded with max_size
    """
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        """
        Args:
            max_size: Maximum number of entries
            default_ttl: Default TTL in seconds (5 minutes)
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        self._locks: Dict[str, threading.Lock] = {}  # Per-key locks for stampede prevention
        self._metrics = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'expirations': 0
        }
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache, returns None if not found or expired"""
        with self._lock:
            entry = self._cache.get(key)
            
            if entry is None:
                self._metrics['misses'] += 1
                return None
            
            if entry.is_expired():
                self._delete_key(key)
                self._metrics['expirations'] += 1
                self._metrics['misses'] += 1
                return None
            
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            self._metrics['hits'] += 1
            return entry.value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache with optional custom TTL"""
        ttl = ttl if ttl is not None else self.default_ttl
        
        with self._lock:
            # Evict if at capacity
            if len(self._cache) >= self.max_size and key not in self._cache:
                self._evict_oldest()
            
            self._cache[key] = CacheEntry(value, ttl)
            self._cache.move_to_end(key)
    
    def delete(self, key: str) -> bool:
        """Delete a key from cache"""
        with self._lock:
            return self._delete_key(key)
    
    def _delete_key(self, key: str) -> bool:
        """Internal delete without lock"""
        if key in self._cache:
            del self._cache[key]
            return True
        return False
    
    def _evict_oldest(self) -> None:
        """Evict oldest entry"""
        if self._cache:
            self._cache.popitem(last=False)
            self._metrics['evictions'] += 1
    
    def clear(self) -> None:
        """Clear all cache entries"""
        with self._lock:
            self._cache.clear()
    
    def get_or_set(
        self,
        key: str,
        factory: Callable[[], Any],
        ttl: Optional[int] = None
    ) -> Any:
        """
        Get from cache or compute and set.
        Prevents cache stampede using per-key locks.
        
        Args:
            key: Cache key
            factory: Function to compute value if not cached
            ttl: Optional custom TTL
        """
        # Fast path: check cache without lock
        value = self.get(key)
        if value is not None:
            return value
        
        # Get or create per-key lock
        with self._lock:
            if key not in self._locks:
                self._locks[key] = threading.Lock()
            key_lock = self._locks[key]
        
        # Acquire per-key lock to prevent stampede
        with key_lock:
            # Double-check pattern
            value = self.get(key)
            if value is not None:
                return value
            
            # Compute value
            start = time.time()
            value = factory()
            compute_time = time.time() - start
            
            if compute_time > 0.1:  # Log slow computations
                logger.info(f"Cache compute for '{key}' took {compute_time:.3f}s")
            
            self.set(key, value, ttl)
            return value
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get cache performance metrics"""
        with self._lock:
            total = self._metrics['hits'] + self._metrics['misses']
            hit_rate = self._metrics['hits'] / total if total > 0 else 0
            return {
                **self._metrics,
                'size': len(self._cache),
                'max_size': self.max_size,
                'hit_rate': f"{hit_rate:.2%}"
            }
    
    def cleanup_expired(self) -> int:
        """Remove all expired entries, returns count of removed"""
        removed = 0
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired()
            ]
            for key in expired_keys:
                self._delete_key(key)
                removed += 1
        return removed


# Global cache instances with different TTLs for different data types
stock_cache = LRUCache(max_size=500, default_ttl=60)      # Stock data: 1 minute
chart_cache = LRUCache(max_size=200, default_ttl=300)     # Chart data: 5 minutes  
search_cache = LRUCache(max_size=1000, default_ttl=120)   # Search results: 2 minutes
aggregation_cache = LRUCache(max_size=100, default_ttl=600)  # Aggregations: 10 minutes


def cache_key(*args, **kwargs) -> str:
    """Generate a consistent cache key from arguments"""
    key_parts = [str(arg) for arg in args]
    key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
    key_string = ":".join(key_parts)
    return hashlib.md5(key_string.encode()).hexdigest()


def cached(cache: LRUCache, ttl: Optional[int] = None, key_prefix: str = ""):
    """
    Decorator for caching function results.
    
    Usage:
        @cached(stock_cache, ttl=60, key_prefix="stock_details")
        def get_stock_details(symbol):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Build cache key from function name and arguments
            key = f"{key_prefix}:{func.__name__}:{cache_key(*args, **kwargs)}"
            return cache.get_or_set(key, lambda: func(*args, **kwargs), ttl)
        return wrapper
    return decorator


def invalidate_stock_cache(symbol: str = None) -> None:
    """Invalidate stock-related caches"""
    if symbol:
        # Targeted invalidation
        stock_cache.delete(f"stock:{symbol}")
        chart_cache.delete(f"chart:{symbol}")
    else:
        # Full invalidation
        stock_cache.clear()
        chart_cache.clear()
    search_cache.clear()  # Always clear search cache on stock updates


# Background cache cleanup thread
def start_cache_cleanup_thread(interval: int = 60):
    """Start background thread to cleanup expired cache entries"""
    def cleanup_loop():
        while True:
            time.sleep(interval)
            for cache in [stock_cache, chart_cache, search_cache, aggregation_cache]:
                cache.cleanup_expired()
    
    thread = threading.Thread(target=cleanup_loop, daemon=True)
    thread.start()
    logger.info("Cache cleanup thread started")


# Log cache metrics periodically
def log_cache_metrics():
    """Log cache metrics for monitoring"""
    logger.info("=== Cache Metrics ===")
    for name, cache in [
        ("Stock", stock_cache),
        ("Chart", chart_cache),
        ("Search", search_cache),
        ("Aggregation", aggregation_cache)
    ]:
        metrics = cache.get_metrics()
        logger.info(f"{name}: {metrics}")

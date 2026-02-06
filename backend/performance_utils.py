"""
Performance Utilities - Profiling, Metrics, and Monitoring

FEATURES:
- Request profiling decorator
- Performance metrics collection
- Query profiling utilities
- Memory usage tracking
- Logging configuration
"""

import time
import logging
import functools
import threading
from typing import Dict, Any, Callable, Optional
from collections import defaultdict
from datetime import datetime
import traceback

logger = logging.getLogger(__name__)


class PerformanceMetrics:
    """
    Thread-safe performance metrics collector.
    
    USAGE:
    - Track request latencies
    - Count errors
    - Monitor throughput
    - Identify slow endpoints
    """
    
    def __init__(self):
        self._lock = threading.Lock()
        self._request_times: Dict[str, list] = defaultdict(list)
        self._error_counts: Dict[str, int] = defaultdict(int)
        self._request_counts: Dict[str, int] = defaultdict(int)
        self._slow_requests: list = []
        self._max_samples = 1000  # Keep last N samples per endpoint
    
    def record_request(
        self,
        endpoint: str,
        duration: float,
        status_code: int = 200
    ):
        """Record a request's performance"""
        with self._lock:
            # Update request times (bounded list)
            times = self._request_times[endpoint]
            times.append(duration)
            if len(times) > self._max_samples:
                times.pop(0)
            
            # Update counts
            self._request_counts[endpoint] += 1
            
            if status_code >= 400:
                self._error_counts[endpoint] += 1
            
            # Track slow requests
            if duration > 0.5:  # > 500ms
                self._slow_requests.append({
                    'endpoint': endpoint,
                    'duration': duration,
                    'timestamp': datetime.now().isoformat()
                })
                if len(self._slow_requests) > 100:
                    self._slow_requests.pop(0)
    
    def get_stats(self, endpoint: Optional[str] = None) -> Dict[str, Any]:
        """Get performance statistics"""
        with self._lock:
            if endpoint:
                return self._get_endpoint_stats(endpoint)
            
            # Aggregate all endpoints
            stats = {}
            for ep in self._request_times.keys():
                stats[ep] = self._get_endpoint_stats(ep)
            
            return {
                'endpoints': stats,
                'slow_requests': self._slow_requests[-10:],  # Last 10 slow requests
                'total_requests': sum(self._request_counts.values()),
                'total_errors': sum(self._error_counts.values())
            }
    
    def _get_endpoint_stats(self, endpoint: str) -> Dict[str, Any]:
        """Get stats for single endpoint"""
        times = self._request_times.get(endpoint, [])
        if not times:
            return {
                'requests': 0,
                'errors': 0,
                'avg_ms': 0,
                'p50_ms': 0,
                'p95_ms': 0,
                'p99_ms': 0
            }
        
        sorted_times = sorted(times)
        n = len(sorted_times)
        
        return {
            'requests': self._request_counts.get(endpoint, 0),
            'errors': self._error_counts.get(endpoint, 0),
            'avg_ms': round(sum(times) / n * 1000, 2),
            'min_ms': round(min(times) * 1000, 2),
            'max_ms': round(max(times) * 1000, 2),
            'p50_ms': round(sorted_times[n // 2] * 1000, 2),
            'p95_ms': round(sorted_times[int(n * 0.95)] * 1000, 2) if n > 20 else None,
            'p99_ms': round(sorted_times[int(n * 0.99)] * 1000, 2) if n > 100 else None
        }
    
    def reset(self):
        """Reset all metrics"""
        with self._lock:
            self._request_times.clear()
            self._error_counts.clear()
            self._request_counts.clear()
            self._slow_requests.clear()


# Global metrics instance
metrics = PerformanceMetrics()


def profile_endpoint(name: Optional[str] = None):
    """
    Decorator to profile endpoint performance.
    
    Usage:
        @profile_endpoint("get_stocks")
        def get_stocks():
            ...
    """
    def decorator(func: Callable) -> Callable:
        endpoint_name = name or func.__name__
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            status = 200
            
            try:
                result = func(*args, **kwargs)
                # Try to extract status code
                if hasattr(result, 'status_code'):
                    status = result.status_code
                elif isinstance(result, tuple) and len(result) > 1:
                    status = result[1]
                return result
            
            except Exception as e:
                status = 500
                raise
            
            finally:
                duration = time.time() - start
                metrics.record_request(endpoint_name, duration, status)
                
                if duration > 0.5:
                    logger.warning(
                        f"Slow endpoint: {endpoint_name} took {duration*1000:.2f}ms"
                    )
        
        return wrapper
    return decorator


def profile_function(func: Callable) -> Callable:
    """
    Decorator for profiling any function.
    
    Logs execution time for functions taking > 100ms.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        try:
            return func(*args, **kwargs)
        finally:
            duration = time.time() - start
            if duration > 0.1:  # Log if > 100ms
                logger.info(f"Function {func.__name__} took {duration*1000:.2f}ms")
    return wrapper


class QueryProfiler:
    """
    Profile database queries.
    
    USAGE:
    - Identify slow queries
    - Detect N+1 problems
    - Track query patterns
    """
    
    def __init__(self):
        self._lock = threading.Lock()
        self._queries: list = []
        self._query_counts: Dict[str, int] = defaultdict(int)
        self._max_queries = 1000
    
    def record_query(self, query: str, duration: float, params: tuple = None):
        """Record a database query"""
        # Normalize query for grouping
        normalized = self._normalize_query(query)
        
        with self._lock:
            self._query_counts[normalized] += 1
            
            # Track slow queries
            if duration > 0.1:  # > 100ms
                self._queries.append({
                    'query': query[:200],  # Truncate
                    'duration_ms': round(duration * 1000, 2),
                    'timestamp': datetime.now().isoformat()
                })
                if len(self._queries) > self._max_queries:
                    self._queries.pop(0)
    
    def _normalize_query(self, query: str) -> str:
        """Normalize query for grouping (remove specific values)"""
        import re
        # Replace numeric values
        normalized = re.sub(r'\b\d+\b', '?', query)
        # Replace string literals
        normalized = re.sub(r"'[^']*'", '?', normalized)
        return normalized[:100]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get query statistics"""
        with self._lock:
            # Find most frequent queries (potential N+1)
            frequent = sorted(
                self._query_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
            
            return {
                'slow_queries': self._queries[-10:],
                'frequent_queries': [
                    {'query': q, 'count': c}
                    for q, c in frequent
                ],
                'total_queries': sum(self._query_counts.values())
            }
    
    def detect_n_plus_one(self, threshold: int = 10) -> list:
        """Detect potential N+1 query patterns"""
        with self._lock:
            suspicious = [
                {'query': query, 'count': count}
                for query, count in self._query_counts.items()
                if count > threshold
            ]
            return sorted(suspicious, key=lambda x: x['count'], reverse=True)


query_profiler = QueryProfiler()


class MemoryTracker:
    """
    Track memory usage.
    
    Useful for detecting memory leaks in long-running processes.
    Note: Requires psutil package for full functionality.
    """
    
    @staticmethod
    def get_memory_usage() -> Dict[str, float]:
        """Get current memory usage (requires psutil)"""
        try:
            import psutil  # type: ignore
            process = psutil.Process()
            mem = process.memory_info()
            return {
                'rss_mb': round(mem.rss / 1024 / 1024, 2),
                'vms_mb': round(mem.vms / 1024 / 1024, 2),
                'percent': round(process.memory_percent(), 2)
            }
        except ImportError:
            return {'error': 'psutil not installed - run: pip install psutil'}
    
    @staticmethod
    def get_object_counts() -> Dict[str, int]:
        """Get counts of Python objects (for debugging)"""
        import gc
        counts: Dict[str, int] = defaultdict(int)
        for obj in gc.get_objects():
            counts[type(obj).__name__] += 1
        
        # Return top 20
        return dict(sorted(counts.items(), key=lambda x: x[1], reverse=True)[:20])


def configure_logging(
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    json_format: bool = False
):
    """
    Configure application logging.
    
    Args:
        level: Logging level
        log_file: Optional file path for logs
        json_format: Use JSON format for structured logging
    """
    handlers = [logging.StreamHandler()]
    
    if log_file:
        handlers.append(logging.FileHandler(log_file, encoding='utf-8'))
    
    if json_format:
        import json
        
        class JsonFormatter(logging.Formatter):
            def format(self, record):
                log_obj = {
                    'timestamp': datetime.now().isoformat(),
                    'level': record.levelname,
                    'message': record.getMessage(),
                    'module': record.module,
                    'function': record.funcName,
                    'line': record.lineno
                }
                if record.exc_info:
                    log_obj['exception'] = traceback.format_exception(*record.exc_info)
                return json.dumps(log_obj)
        
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    for handler in handlers:
        handler.setFormatter(formatter)
    
    logging.basicConfig(level=level, handlers=handlers)


def log_performance_summary():
    """Log a summary of performance metrics"""
    stats = metrics.get_stats()
    logger.info("=" * 60)
    logger.info("PERFORMANCE SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total Requests: {stats['total_requests']}")
    logger.info(f"Total Errors: {stats['total_errors']}")
    
    for endpoint, ep_stats in stats.get('endpoints', {}).items():
        logger.info(
            f"  {endpoint}: "
            f"avg={ep_stats['avg_ms']}ms, "
            f"p95={ep_stats.get('p95_ms', 'N/A')}ms, "
            f"requests={ep_stats['requests']}"
        )
    
    if stats.get('slow_requests'):
        logger.info("Recent Slow Requests:")
        for req in stats['slow_requests'][-5:]:
            logger.info(f"  {req['endpoint']}: {req['duration']*1000:.2f}ms")

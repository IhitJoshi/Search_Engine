"""
Background chart cache prefetcher.

Warms 1D chart cache to avoid slow first-click chart loads.
"""

import threading
import time
import logging

from utils.cache_manager import chart_cache
from utils.optimized_db import optimized_db
from services.async_fetcher import fetch_chart_data_parallel

logger = logging.getLogger(__name__)


def _prefetch_1d_for_symbols(symbols):
    for symbol in symbols:
        try:
            cache_key = f"chart:{symbol}:1D"
            if chart_cache.get(cache_key):
                continue
            data = fetch_chart_data_parallel(symbol, ["1D"]).get("1D", [])
            if data:
                chart_cache.set(cache_key, data, ttl=180)
        except Exception as e:
            logger.error(f"Chart prefetch failed for {symbol}: {e}")
        time.sleep(0.2)


def start_chart_prefetcher(interval: int = 180):
    """Start background prefetcher for 1D charts."""
    def _loop():
        while True:
            try:
                rows = optimized_db.get_latest_stocks(limit=None)
                symbols = [r.get("symbol") for r in rows if r.get("symbol")]
                _prefetch_1d_for_symbols(symbols)
            except Exception:
                logger.exception("Chart prefetch loop failed")
            time.sleep(interval)

    thread = threading.Thread(target=_loop, daemon=True)
    thread.start()
    logger.info("Chart prefetcher started (interval=%ss)", interval)

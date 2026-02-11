"""
Background price cache updater.

Refreshes latest stock prices into the in-memory cache on a fixed interval.
"""

import threading
import time
import logging
from datetime import datetime

from utils.cache_manager import stock_cache
from utils.optimized_db import optimized_db

logger = logging.getLogger(__name__)

PRICE_CACHE_PREFIX = "live_stock"


def refresh_price_cache() -> int:
    """Fetch latest prices from DB and refresh cache entries."""
    stocks = optimized_db.get_latest_stocks()
    updated = 0
    now_iso = datetime.utcnow().isoformat() + "Z"

    for stock in stocks:
        symbol = (stock.get("symbol") or "").upper()
        if not symbol:
            continue
        payload = {**stock, "cache_timestamp": now_iso}
        stock_cache.set(f"{PRICE_CACHE_PREFIX}:{symbol}", payload, ttl=20)
        updated += 1

    return updated


def start_price_cache_updater(interval: int = 5) -> None:
    """Start a background thread that refreshes the price cache."""
    def _loop():
        while True:
            try:
                refreshed = refresh_price_cache()
                if refreshed == 0:
                    logger.warning("Price cache refresh returned 0 stocks")
            except Exception:
                logger.exception("Price cache refresh failed")
            time.sleep(interval)

    thread = threading.Thread(target=_loop, daemon=True)
    thread.start()
    logger.info("Price cache updater started (interval=%ss)", interval)

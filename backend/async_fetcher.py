"""
Async Stock Fetcher - Parallel API calls using asyncio and ThreadPoolExecutor

FEATURES:
- Parallel stock data fetching (10x faster than sequential)
- Rate limiting to avoid API throttling
- Retry logic with exponential backoff
- Batch processing with chunking
- Background update scheduling
"""

import asyncio
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional
from datetime import datetime
import threading

try:
    import yfinance as yf
except ImportError:
    yf = None

from cache_manager import stock_cache, invalidate_stock_cache
from optimized_db import optimized_db

logger = logging.getLogger(__name__)


class AsyncStockFetcher:
    """
    High-performance stock data fetcher with parallel execution.
    
    PERFORMANCE GAINS:
    - Sequential: ~50 stocks × 1s each = 50 seconds
    - Parallel (10 workers): ~50 stocks ÷ 10 = 5 seconds
    - With caching: <100ms for cache hits
    """
    
    def __init__(
        self,
        max_workers: int = 10,
        rate_limit_delay: float = 0.1,
        retry_attempts: int = 3,
        batch_size: int = 20
    ):
        """
        Args:
            max_workers: Maximum concurrent API calls
            rate_limit_delay: Delay between API calls per worker
            retry_attempts: Number of retry attempts on failure
            batch_size: Number of stocks to process in each batch
        """
        self.max_workers = max_workers
        self.rate_limit_delay = rate_limit_delay
        self.retry_attempts = retry_attempts
        self.batch_size = batch_size
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._lock = threading.Lock()
        self._last_fetch_time: Dict[str, float] = {}
    
    def fetch_single_stock(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetch single stock with caching and retry logic.
        
        OPTIMIZATION: Check cache first, only call API if miss.
        """
        # Check cache first
        cache_key = f"stock:{symbol}"
        cached_data = stock_cache.get(cache_key)
        if cached_data:
            logger.debug(f"Cache hit for {symbol}")
            return cached_data
        
        # Fetch from API with retry
        for attempt in range(self.retry_attempts):
            try:
                data = self._fetch_from_api(symbol)
                if data:
                    # Cache the result
                    stock_cache.set(cache_key, data, ttl=60)
                    return data
            except Exception as e:
                if attempt < self.retry_attempts - 1:
                    wait_time = (2 ** attempt) * 0.5  # Exponential backoff
                    logger.warning(f"Retry {attempt + 1} for {symbol}: {e}")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Failed to fetch {symbol} after {self.retry_attempts} attempts: {e}")
        
        return None
    
    def _fetch_from_api(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch stock data from Yahoo Finance API"""
        if yf is None:
            logger.error("yfinance not installed")
            return None
        
        # Rate limiting
        time.sleep(self.rate_limit_delay)
        
        stock = yf.Ticker(symbol)
        info = stock.info
        
        if not info or 'symbol' not in info:
            return None
        
        # Extract price from multiple possible fields
        current_price = (
            info.get('currentPrice') or
            info.get('regularMarketPrice') or
            info.get('previousClose')
        )
        
        # Calculate change percent
        previous_close = info.get('previousClose')
        change_percent = None
        if current_price and previous_close and previous_close != 0:
            change_percent = ((current_price - previous_close) / previous_close) * 100
        
        return {
            'symbol': symbol,
            'company_name': info.get('longName', symbol),
            'sector': info.get('sector', 'Unknown'),
            'price': round(current_price, 2) if current_price else None,
            'volume': info.get('volume') or info.get('regularMarketVolume'),
            'average_volume': info.get('averageVolume'),
            'market_cap': info.get('marketCap'),
            'change_percent': round(change_percent, 2) if change_percent else None,
            'summary': (info.get('longBusinessSummary') or '')[:500],
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def fetch_multiple_parallel(
        self,
        symbols: List[str],
        use_cache: bool = True
    ) -> Dict[str, Dict[str, Any]]:
        """
        Fetch multiple stocks in parallel.
        
        PERFORMANCE: 10x faster than sequential fetching.
        """
        results = {}
        to_fetch = []
        
        # Check cache for all symbols first
        if use_cache:
            for symbol in symbols:
                cached = stock_cache.get(f"stock:{symbol}")
                if cached:
                    results[symbol] = cached
                else:
                    to_fetch.append(symbol)
        else:
            to_fetch = symbols
        
        if not to_fetch:
            logger.info(f"All {len(symbols)} stocks served from cache")
            return results
        
        logger.info(f"Fetching {len(to_fetch)} stocks in parallel (cached: {len(results)})")
        
        # Parallel fetch using ThreadPoolExecutor
        start_time = time.time()
        
        future_to_symbol = {
            self._executor.submit(self.fetch_single_stock, symbol): symbol
            for symbol in to_fetch
        }
        
        for future in as_completed(future_to_symbol):
            symbol = future_to_symbol[future]
            try:
                data = future.result()
                if data:
                    results[symbol] = data
            except Exception as e:
                logger.error(f"Error fetching {symbol}: {e}")
        
        elapsed = time.time() - start_time
        logger.info(f"Parallel fetch completed: {len(results)}/{len(symbols)} in {elapsed:.2f}s")
        
        return results
    
    def fetch_and_store_batch(
        self,
        symbols: List[str],
        sector_mapping: Optional[Dict[str, str]] = None
    ) -> int:
        """
        Fetch stocks and batch insert to database.
        
        OPTIMIZATION: Combines parallel fetch with batch DB insert.
        """
        # Parallel fetch
        stock_data = self.fetch_multiple_parallel(symbols)
        
        if not stock_data:
            return 0
        
        # Apply sector mapping if provided
        if sector_mapping:
            for symbol, data in stock_data.items():
                if symbol in sector_mapping:
                    data['sector'] = sector_mapping[symbol]
        
        # Batch insert to database
        stocks_list = list(stock_data.values())
        count = optimized_db.batch_upsert_stocks(stocks_list)
        
        # Invalidate search cache after update
        invalidate_stock_cache()
        
        logger.info(f"Stored {count} stocks to database")
        return count
    
    def shutdown(self):
        """Shutdown executor"""
        self._executor.shutdown(wait=True)


class BackgroundStockUpdater:
    """
    Background service for periodic stock updates.
    
    FEATURES:
    - Non-blocking background updates
    - Configurable update intervals
    - Automatic retry on failures
    - Graceful shutdown
    """
    
    def __init__(
        self,
        fetcher: AsyncStockFetcher,
        symbols: List[str],
        update_interval: int = 60,
        sector_mapping: Optional[Dict[str, str]] = None
    ):
        self.fetcher = fetcher
        self.symbols = symbols
        self.update_interval = update_interval
        self.sector_mapping = sector_mapping
        self._running = False
        self._thread: Optional[threading.Thread] = None
    
    def start(self):
        """Start background update thread"""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._update_loop, daemon=True)
        self._thread.start()
        logger.info(f"Background updater started: {len(self.symbols)} symbols, {self.update_interval}s interval")
    
    def stop(self):
        """Stop background updates"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Background updater stopped")
    
    def _update_loop(self):
        """Main update loop"""
        # Initial fetch
        self._do_update()
        
        while self._running:
            time.sleep(self.update_interval)
            if self._running:
                self._do_update()
    
    def _do_update(self):
        """Perform one update cycle"""
        try:
            start = time.time()
            count = self.fetcher.fetch_and_store_batch(
                self.symbols,
                self.sector_mapping
            )
            elapsed = time.time() - start
            logger.info(f"Background update: {count} stocks in {elapsed:.2f}s")
        except Exception as e:
            logger.exception(f"Background update failed: {e}")


# Global instances
async_fetcher = AsyncStockFetcher(max_workers=10)


def fetch_chart_data_parallel(
    symbol: str,
    periods: List[str] = None
) -> Dict[str, Any]:
    """
    Fetch chart data for multiple periods in parallel.
    
    OPTIMIZATION: Instead of sequential fetches for 1D, 5D, 1M, etc.,
    fetch all at once.
    """
    from cache_manager import chart_cache
    
    if periods is None:
        periods = ['1D', '5D', '1M', '3M', '1Y']
    
    cache_key = f"chart:{symbol}:all"
    cached = chart_cache.get(cache_key)
    if cached:
        return cached
    
    if yf is None:
        return {}
    
    results = {}
    
    # Define period configurations
    period_config = {
        '1D': ('1d', '5m'),
        '5D': ('5d', '30m'),
        '1M': ('1mo', '1d'),
        '3M': ('3mo', '1d'),
        '1Y': ('1y', '1wk')
    }
    
    def fetch_period(period: str) -> tuple:
        try:
            config = period_config.get(period)
            if not config:
                return period, None
            
            stock = yf.Ticker(symbol)
            hist = stock.history(period=config[0], interval=config[1])
            
            if hist.empty:
                return period, None
            
            hist = hist.reset_index()
            date_col = 'Datetime' if 'Datetime' in hist.columns else 'Date'
            
            chart_data = [
                {
                    'date': row[date_col].strftime('%Y-%m-%d' if period != '1D' else '%H:%M'),
                    'price': float(row['Close'])
                }
                for _, row in hist.iterrows()
            ]
            
            return period, chart_data
        except Exception as e:
            logger.error(f"Error fetching {period} chart for {symbol}: {e}")
            return period, None
    
    # Parallel fetch all periods
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(fetch_period, p): p for p in periods}
        for future in as_completed(futures):
            period, data = future.result()
            if data:
                results[period] = data
    
    # Cache combined result
    chart_cache.set(cache_key, results, ttl=300)
    
    return results

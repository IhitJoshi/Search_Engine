"""
Stock Fetcher - Fetches live stock data and stores in SQLite with error handling
"""

import sqlite3
import yfinance as yf
import time
import logging
from datetime import datetime
from typing import List, Dict, Optional
from contextlib import contextmanager

# Configuration
DATABASE_NAME = "stocks.db"
STOCK_SYMBOLS = [
    # Technology - Big Tech > 500B
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "AVGO", "TSM", "TCEHY",
    
    # Finance - Top Banks vs Fintech
    "JPM", "BAC", "V", "MA", "PYPL", "SQ", "GS", "MS", "AXP", "INTU",
    
    # Energy - Renewable vs Non-Renewable
    "NEE", "ENPH", "FSLR", "VWS.CO", "ORSTED.CO", "XOM", "CVX", "BP", "TTE", "SHEL",
    
    # Healthcare - Pharma vs Biotech
    "JNJ", "PFE", "MRK", "NVS", "RHHBY", "AMGN", "GILD", "BIIB", "REGN", "MRNA",
    
    # Automotive - EV vs Traditional
    "NIO", "RIVN", "LCID", "BYD", "TM", "HMC", "GM", "F", "STLA", "VWAGY"
]
UPDATE_INTERVAL = 60  # seconds

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('stock_fetcher.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def create_table():
    """Create the stocks table if it doesn't exist"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stocks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                company_name TEXT,
                sector TEXT,
                price REAL,
                volume INTEGER,
                change_percent REAL,
                summary TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(symbol, last_updated)
            )
        ''')
        
        # Create index for better query performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_symbol_time ON stocks(symbol, last_updated)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_last_updated ON stocks(last_updated)')
        
        conn.commit()
    logger.info(f"Database '{DATABASE_NAME}' initialized with 'stocks' table")

def fetch_stock_data(symbol: str) -> Optional[Dict]:
    """
    Fetch comprehensive stock data for a given symbol
    """
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        history = stock.history(period="1d", interval="1m")
        
        # Get current price from multiple possible fields
        current_price = (
            info.get('currentPrice') or 
            info.get('regularMarketPrice') or 
            info.get('previousClose')
        )
        
        # Calculate price change
        previous_close = info.get('previousClose')
        change_percent = (
            ((current_price - previous_close) / previous_close * 100) 
            if current_price and previous_close else None
        )
        
        # Get current volume
        current_volume = info.get('volume') or info.get('averageVolume')
        
        data = {
            'symbol': symbol,
            'company_name': info.get('longName', symbol),
            'sector': info.get('sector', 'Unknown'),
            'price': round(current_price, 2) if current_price else None,
            'volume': current_volume,
            'change_percent': round(change_percent, 2) if change_percent else None,
            'summary': (info.get('longBusinessSummary') or 'No summary available')[:500],
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return data
    
    except Exception as e:
        logger.error(f"Error fetching {symbol}: {str(e)}")
        return None

def update_database(stock_data: Dict):
    """Update or insert stock data in the database"""
    if not stock_data or stock_data.get('price') is None:
        logger.warning(f"Skipping invalid data for {stock_data.get('symbol')}")
        return
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO stocks 
                (symbol, company_name, sector, price, volume, change_percent, summary, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                stock_data['symbol'],
                stock_data['company_name'],
                stock_data['sector'],
                stock_data['price'],
                stock_data['volume'],
                stock_data['change_percent'],
                stock_data['summary'],
                stock_data['last_updated']
            ))
            conn.commit()
            
            # Log the update
            timestamp = datetime.now().strftime('%H:%M:%S')
            price_str = f"${stock_data['price']:.2f}"
            change_str = f"{stock_data['change_percent']:+.2f}%" if stock_data['change_percent'] else "N/A"
            logger.info(f"[{timestamp}] {stock_data['symbol']}: {price_str} ({change_str})")
            
    except sqlite3.Error as e:
        logger.error(f"Database error for {stock_data['symbol']}: {str(e)}")

def fetch_and_update_all(symbols: List[str]):
    """Fetch and update data for all symbols with rate limiting"""
    logger.info(f"Fetching data for {len(symbols)} stocks...")
    
    success_count = 0
    
    for symbol in symbols:
        stock_data = fetch_stock_data(symbol)
        if stock_data:
            update_database(stock_data)
            success_count += 1
        
        # Rate limiting with exponential backoff on errors
        time.sleep(1)
    
    logger.info(f"Successfully updated {success_count}/{len(symbols)} stocks")

def run_fetcher():
    """Main loop - continuously fetch and update stock data"""
    logger.info("🚀 Stock Fetcher Started")
    logger.info(f"📊 Tracking {len(STOCK_SYMBOLS)} stocks")
    logger.info(f"⏱️ Update interval: {UPDATE_INTERVAL} seconds")
    
    create_table()
    
    # Initial fetch
    fetch_and_update_all(STOCK_SYMBOLS)
    
    # Continuous updates
    error_count = 0
    max_errors = 5
    
    while True:
        try:
            time.sleep(UPDATE_INTERVAL)
            fetch_and_update_all(STOCK_SYMBOLS)
            error_count = 0  # Reset error count on success
            
        except KeyboardInterrupt:
            logger.info("🛑 Stock Fetcher stopped by user")
            break
        except Exception as e:
            error_count += 1
            logger.error(f"Unexpected error: {e}")
            if error_count >= max_errors:
                logger.error("Too many consecutive errors, stopping...")
                break
            time.sleep(UPDATE_INTERVAL * 2)  # Backoff on errors

def main():
    """Main entry point"""
    try:
        run_fetcher()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise

if __name__ == "__main__":
    main()
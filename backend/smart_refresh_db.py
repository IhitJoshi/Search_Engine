"""
Smart Refresh Database Layer
Handles SQLite operations with thread-safe timestamp management
"""

import sqlite3
import threading
from datetime import datetime
from pathlib import Path

# Thread-safe lock for timestamp operations
TIMESTAMP_LOCK = threading.RLock()
DB_PATH = Path(__file__).parent / "stocks.db"


def get_db_connection():
    """Get thread-safe SQLite connection"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database schema if not exists"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT UNIQUE NOT NULL,
            company_name TEXT NOT NULL,
            sector TEXT NOT NULL,
            price REAL NOT NULL,
            volume INTEGER NOT NULL,
            change_percent REAL NOT NULL,
            summary TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()


def get_all_stocks():
    """Fetch all stocks from database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM stocks ORDER BY symbol")
    stocks = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return stocks


def get_stock(symbol):
    """Fetch single stock by symbol"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM stocks WHERE symbol = ?", (symbol,))
    stock = cursor.fetchone()
    
    conn.close()
    return dict(stock) if stock else None


def update_stock(symbol, price, volume, change_percent, **kwargs):
    """Update stock price and volume"""
    with TIMESTAMP_LOCK:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE stocks 
                SET price = ?, volume = ?, change_percent = ?, last_updated = CURRENT_TIMESTAMP
                WHERE symbol = ?
            """, (price, volume, change_percent, symbol))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Error updating stock {symbol}: {e}")
            return False
        finally:
            conn.close()


def insert_stock(symbol, company_name, sector, price, volume, change_percent, summary=""):
    """Insert new stock into database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO stocks (symbol, company_name, sector, price, volume, change_percent, summary, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (symbol, company_name, sector, price, volume, change_percent, summary))
        
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # Stock already exists
        return False
    except Exception as e:
        print(f"Error inserting stock {symbol}: {e}")
        return False
    finally:
        conn.close()


def get_last_update_timestamp(symbol=None):
    """
    Get last update timestamp for a stock or all stocks
    Thread-safe using RLock
    """
    with TIMESTAMP_LOCK:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if symbol:
            cursor.execute("SELECT last_updated FROM stocks WHERE symbol = ?", (symbol,))
        else:
            # Get the most recent update across all stocks
            cursor.execute("SELECT MAX(last_updated) as latest FROM stocks")
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            timestamp_str = result[0]
            if timestamp_str:
                return datetime.fromisoformat(timestamp_str)
        
        return None


def get_time_since_last_update(symbol=None):
    """
    Get seconds since last update for a stock or all stocks
    Returns float (seconds) or None if no data
    """
    last_update = get_last_update_timestamp(symbol)
    if last_update:
        delta = datetime.utcnow() - last_update.replace(tzinfo=None)
        return delta.total_seconds()
    return None


def should_refresh():
    """
    Determine if a refresh is needed
    Returns True if > 30 seconds since last update
    """
    seconds_since = get_time_since_last_update()
    if seconds_since is None:
        return True  # No data, refresh needed
    return seconds_since > 30  # Refresh if older than 30 seconds


def is_data_fresh():
    """Check if cached data is fresh (< 30 seconds old)"""
    return not should_refresh()


def clear_database():
    """Clear all stocks from database (for testing)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM stocks")
    conn.commit()
    conn.close()


def get_stock_count():
    """Get total number of stocks in database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM stocks")
    count = cursor.fetchone()[0]
    conn.close()
    return count


def update_all_stocks(stocks_data):
    """
    Atomically update all stock prices
    stocks_data: list of dicts with symbol, price, volume, change_percent
    """
    if not stocks_data:
        return False
    
    with TIMESTAMP_LOCK:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            for stock in stocks_data:
                cursor.execute("""
                    UPDATE stocks 
                    SET price = ?, volume = ?, change_percent = ?, last_updated = CURRENT_TIMESTAMP
                    WHERE symbol = ?
                """, (stock['price'], stock['volume'], stock['change_percent'], stock['symbol']))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Error batch updating stocks: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

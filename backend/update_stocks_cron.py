"""
Stock Price Updater - Cron Job Script
Runs periodically to update stock prices
No infinite loops - designed for Render Cron Jobs or system cron

Usage:
    python update_stocks_cron.py

For Render Cron Job:
    Schedule: */1 * * * * (every 1 minute)
    Command: python update_stocks_cron.py
"""

import sys
import logging
from datetime import datetime
from services.stock_fetcher import fetch_stock_data, STOCK_SYMBOLS, get_db_connection, create_table

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('stock_updater_cron.log')
    ]
)
logger = logging.getLogger(__name__)


def update_stock_in_db(symbol: str, stock_data: dict) -> bool:
    """
    Update a single stock in the database
    
    Args:
        symbol: Stock ticker symbol
        stock_data: Dictionary with stock information
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            timestamp = datetime.now().isoformat()
            
            cursor.execute("""
                INSERT INTO stocks 
                (symbol, company_name, sector, price, volume, change_percent, summary, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                symbol,
                stock_data.get('company_name', ''),
                stock_data.get('sector', ''),
                stock_data.get('price', 0.0),
                stock_data.get('volume', 0),
                stock_data.get('change_percent', 0.0),
                stock_data.get('summary', ''),
                timestamp
            ))
            
            conn.commit()
            logger.info(f"✓ Updated {symbol}: ${stock_data.get('price', 0):.2f} ({stock_data.get('change_percent', 0):+.2f}%)")
            return True
            
    except Exception as e:
        logger.error(f"✗ Failed to update {symbol} in database: {e}")
        return False


def update_all_stocks():
    """
    Main function to update all stock prices
    Called by cron job - runs once and exits
    """
    logger.info("=" * 60)
    logger.info("Starting stock price update job")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    logger.info(f"Stocks to update: {len(STOCK_SYMBOLS)}")
    logger.info("=" * 60)
    
    try:
        # Ensure database table exists
        create_table()
        
        success_count = 0
        fail_count = 0
        
        # Update each stock
        for symbol in STOCK_SYMBOLS:
            try:
                logger.info(f"Fetching data for {symbol}...")
                stock_data = fetch_stock_data(symbol)
                
                if stock_data:
                    if update_stock_in_db(symbol, stock_data):
                        success_count += 1
                    else:
                        fail_count += 1
                else:
                    logger.warning(f"No data returned for {symbol}")
                    fail_count += 1
                    
            except Exception as e:
                logger.error(f"Failed to process {symbol}: {e}")
                fail_count += 1
        
        logger.info("=" * 60)
        logger.info(f"Update job completed:")
        logger.info(f"  ✓ Successful: {success_count}")
        logger.info(f"  ✗ Failed: {fail_count}")
        logger.info(f"  Total: {len(STOCK_SYMBOLS)}")
        logger.info("=" * 60)
        
        return success_count > 0
        
    except Exception as e:
        logger.error(f"Critical error in update job: {e}")
        return False


if __name__ == "__main__":
    """
    Entry point for cron job
    Runs update and exits cleanly
    """
    try:
        success = update_all_stocks()
        
        if success:
            logger.info("✓ Exiting successfully")
            sys.exit(0)
        else:
            logger.error("✗ Exiting with errors")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

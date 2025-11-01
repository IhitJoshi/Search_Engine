"""
Main Application Entry Point - Stock Search Engine
Handles everything: database setup, stock fetching, search engine
"""

import logging
import sys
import os
import sqlite3
import time
import yfinance as yf
import pandas as pd
from datetime import datetime
from typing import Optional, Dict, Any, List
from contextlib import contextmanager

# Setup logging with ASCII-only characters for Windows compatibility
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('app.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Configuration - 48 Stock Portfolio
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

# Sector mapping - maps stock symbols to our standardized sectors
SECTOR_MAPPING = {
    # Technology
    "AAPL": "Technology", "MSFT": "Technology", "NVDA": "Technology", "AMZN": "Technology",
    "GOOGL": "Technology", "META": "Technology", "TSLA": "Technology", "AVGO": "Technology",
    "TSM": "Technology", "TCEHY": "Technology",
    
    # Financial Services
    "JPM": "Financial Services", "BAC": "Financial Services", "V": "Financial Services",
    "MA": "Financial Services", "PYPL": "Financial Services", "SQ": "Financial Services",
    "GS": "Financial Services", "MS": "Financial Services", "AXP": "Financial Services",
    "INTU": "Financial Services",
    
    # Energy
    "NEE": "Energy", "ENPH": "Energy", "FSLR": "Energy", "VWS.CO": "Energy",
    "ORSTED.CO": "Energy", "XOM": "Energy", "CVX": "Energy", "BP": "Energy", "TTE": "Energy",
    "SHEL": "Energy",
    
    # Healthcare
    "JNJ": "Healthcare", "PFE": "Healthcare", "MRK": "Healthcare", "NVS": "Healthcare",
    "RHHBY": "Healthcare", "AMGN": "Healthcare", "GILD": "Healthcare", "BIIB": "Healthcare",
    "REGN": "Healthcare", "MRNA": "Healthcare",
    
    # Automotive
    "NIO": "Automotive", "RIVN": "Automotive", "LCID": "Automotive", "BYD": "Automotive",
    "TM": "Automotive", "HMC": "Automotive", "GM": "Automotive", "F": "Automotive",
    "STLA": "Automotive", "VWAGY": "Automotive"
}

UPDATE_INTERVAL = 60  # seconds

class DatabaseManager:
    """Handles all database operations"""
    
    def __init__(self, db_name="stocks.db"):
        self.db_name = db_name
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def create_tables(self):
        """Create all required tables with updated schema"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Drop and recreate stocks table to ensure latest schema
            cursor.execute('DROP TABLE IF EXISTS stocks')
            
            cursor.execute('''
                CREATE TABLE stocks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL UNIQUE,
                    company_name TEXT,
                    sector TEXT,
                    price REAL,
                    volume INTEGER,
                    change_percent REAL,
                    summary TEXT,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_symbol ON stocks(symbol)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sector ON stocks(sector)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_last_updated ON stocks(last_updated)')
            
            conn.commit()
        logger.info("Database tables created with latest schema")

class StockFetcher:
    """Handles stock data fetching from Yahoo Finance"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    def fetch_stock_data(self, symbol: str) -> Optional[Dict]:
        """Fetch stock data for a given symbol"""
        try:
            stock = yf.Ticker(symbol)
            info = stock.info
            
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
            
            # Use our standardized sector mapping instead of Yahoo Finance sector
            sector = SECTOR_MAPPING.get(symbol, info.get('sector', 'Unknown'))
            
            data = {
                'symbol': symbol,
                'company_name': info.get('longName', symbol),
                'sector': sector,  # Use our standardized sector
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
    
    def update_database(self, stock_data: Dict):
        """Update stock data in database"""
        if not stock_data or stock_data.get('price') is None:
            return
        
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO stocks 
                    (symbol, company_name, sector, price, volume, change_percent, summary, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (
                    stock_data['symbol'],
                    stock_data['company_name'],
                    stock_data['sector'],
                    stock_data['price'],
                    stock_data['volume'],
                    stock_data['change_percent'],
                    stock_data['summary']
                ))
                conn.commit()
                
                # Log the update
                timestamp = datetime.now().strftime('%H:%M:%S')
                price_str = f"${stock_data['price']:.2f}"
                change_str = f"{stock_data['change_percent']:+.2f}%" if stock_data['change_percent'] else "N/A"
                logger.info(f"[{timestamp}] {stock_data['symbol']}: {price_str} ({change_str})")
                
        except sqlite3.Error as e:
            logger.error(f"Database error for {stock_data['symbol']}: {str(e)}")
    
    def fetch_all_stocks(self, symbols: List[str]):
        """Fetch data for all symbols"""
        logger.info(f"Fetching data for {len(symbols)} stocks...")
        
        success_count = 0
        for symbol in symbols:
            stock_data = self.fetch_stock_data(symbol)
            if stock_data:
                self.update_database(stock_data)
                success_count += 1
            time.sleep(1)  # Rate limiting
        
        logger.info(f"Successfully updated {success_count}/{len(symbols)} stocks")
    
    def run_continuous_fetch(self, symbols: List[str], interval: int):
        """Run continuous stock data fetching"""
        logger.info("Starting continuous stock data fetch...")
        logger.info(f"Tracking {len(symbols)} stocks")
        logger.info(f"Update interval: {interval} seconds")
        
        error_count = 0
        max_errors = 5
        
        while True:
            try:
                self.fetch_all_stocks(symbols)
                error_count = 0  # Reset error count on success
                logger.info(f"Waiting {interval} seconds until next update...")
                time.sleep(interval)
                
            except KeyboardInterrupt:
                logger.info("Stock fetcher stopped by user")
                break
            except Exception as e:
                error_count += 1
                logger.error(f"Unexpected error: {e}")
                if error_count >= max_errors:
                    logger.error("Too many consecutive errors, stopping...")
                    break
                time.sleep(interval * 2)  # Backoff on errors

class SearchEngine:
    """Handles search functionality"""
    
    def __init__(self):
        self.df = None
        self.inverted_index = None
    
    def load_stock_data(self, db_manager):
        """Load stock data from database for searching"""
        logger.info("Loading stock data for search engine...")
        
        try:
            with db_manager.get_connection() as conn:
                # Get the latest data for each symbol
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT s1.* FROM stocks s1
                    JOIN (
                        SELECT symbol, MAX(last_updated) as latest 
                        FROM stocks 
                        GROUP BY symbol
                    ) s2 ON s1.symbol = s2.symbol AND s1.last_updated = s2.latest
                ''')
                
                rows = cursor.fetchall()
                stocks_data = [dict(row) for row in rows]
                
                if not stocks_data:
                    logger.warning("No stock data found in database")
                    return
                
                # Convert to DataFrame
                self.df = pd.DataFrame(stocks_data)
                logger.info(f"Loaded {len(self.df)} stocks for searching")
                
                # Preprocess for search
                self._preprocess_data()
                self._build_index()
                
        except Exception as e:
            logger.error(f"Error loading stock data: {e}")
            raise
    
    def _preprocess_data(self):
        """Preprocess data for search"""
        if self.df is None:
            return
        
        # Combine searchable fields into one text field
        self.df['search_text'] = (
            self.df['symbol'].fillna('') + ' ' +
            self.df['company_name'].fillna('') + ' ' +
            self.df['sector'].fillna('') + ' ' +
            self.df['summary'].fillna('')
        )
        
        # Simple tokenization (you can enhance this)
        self.df['tokens'] = self.df['search_text'].apply(
            lambda x: [token.lower() for token in str(x).split() if len(token) > 2]
        )
    
    def _build_index(self):
        """Build simple inverted index"""
        self.inverted_index = {}
        
        for doc_idx, tokens in enumerate(self.df['tokens']):
            for token in set(tokens):  # Use set to avoid duplicates
                if token not in self.inverted_index:
                    self.inverted_index[token] = []
                self.inverted_index[token].append(doc_idx)
        
        logger.info(f"Built index with {len(self.inverted_index)} unique terms")
    
    def search(self, query: str, top_n: int = 5):
        """Simple search implementation"""
        if self.df is None or self.inverted_index is None:
            logger.error("Search engine not initialized")
            return []
        
        query_tokens = [token.lower() for token in query.split() if len(token) > 2]
        
        # Simple TF-based scoring
        scores = {}
        for token in query_tokens:
            if token in self.inverted_index:
                for doc_idx in self.inverted_index[token]:
                    scores[doc_idx] = scores.get(doc_idx, 0) + 1
        
        # Sort by score
        results = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_n]
        
        # Format results
        formatted_results = []
        for doc_idx, score in results:
            stock = self.df.iloc[doc_idx]
            formatted_results.append({
                'symbol': stock['symbol'],
                'company_name': stock['company_name'],
                'sector': stock['sector'],
                'price': stock['price'],
                'score': score,
                'change_percent': stock.get('change_percent', 'N/A')
            })
        
        return formatted_results

class StockSearchApp:
    """
    Main application class that orchestrates everything
    """
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.stock_fetcher = StockFetcher(self.db_manager)
        self.search_engine = SearchEngine()
    
    def initialize_system(self):
        """Initialize the entire system"""
        logger.info("=" * 60)
        logger.info("STOCK SEARCH ENGINE - INITIALIZING SYSTEM")
        logger.info("=" * 60)
        
        try:
            # Step 1: Setup database
            logger.info("Step 1: Setting up database...")
            self.db_manager.create_tables()
            logger.info("[SUCCESS] Database setup completed")
            
            # Step 2: Fetch initial stock data
            logger.info("Step 2: Fetching initial stock data...")
            self.stock_fetcher.fetch_all_stocks(STOCK_SYMBOLS)
            logger.info("[SUCCESS] Initial stock data fetched")
            
            # Step 3: Initialize search engine
            logger.info("Step 3: Initializing search engine...")
            self.search_engine.load_stock_data(self.db_manager)
            logger.info("[SUCCESS] Search engine initialized")
            
            # Step 4: Display system info
            self._display_system_info()
            
            logger.info("=" * 60)
            logger.info("[SUCCESS] SYSTEM INITIALIZATION COMPLETED")
            logger.info("=" * 60)
            
            return True
            
        except Exception as e:
            logger.error(f"[ERROR] System initialization failed: {e}")
            return False
    
    def _display_system_info(self):
        """Display system information"""
        logger.info("=" * 50)
        logger.info("SYSTEM INFORMATION")
        logger.info("=" * 50)
        
        if self.search_engine.df is not None:
            logger.info(f"Stocks loaded: {len(self.search_engine.df)}")
            logger.info(f"Search terms: {len(self.search_engine.inverted_index) if self.search_engine.inverted_index else 0}")
            
            # Show sample of loaded stocks
            logger.info("Sample stocks:")
            for _, stock in self.search_engine.df.head(3).iterrows():
                logger.info(f"  {stock['symbol']}: {stock['company_name']} - ${stock['price']}")
    
    def run_interactive_search(self):
        """Run interactive search interface"""
        if self.search_engine.df is None:
            logger.error("Search engine not available. Please initialize system first.")
            return
        
        logger.info("\n" + "=" * 50)
        logger.info("INTERACTIVE SEARCH")
        logger.info("=" * 50)
        logger.info("Enter search queries to find stocks")
        logger.info("Type 'exit' to quit, 'refresh' to update data")
        
        while True:
            try:
                query = input("\nEnter search query: ").strip()
                
                if query.lower() == 'exit':
                    break
                elif query.lower() == 'refresh':
                    logger.info("Refreshing stock data...")
                    self.stock_fetcher.fetch_all_stocks(STOCK_SYMBOLS)
                    self.search_engine.load_stock_data(self.db_manager)
                    continue
                elif not query:
                    continue
                
                # Perform search
                results = self.search_engine.search(query)
                
                if not results:
                    logger.info("No results found for your query.")
                else:
                    logger.info(f"\nFound {len(results)} results:")
                    for i, result in enumerate(results, 1):
                        change_str = f"{result['change_percent']:+.2f}%" if result['change_percent'] != 'N/A' else 'N/A'
                        logger.info(f"{i}. {result['symbol']} - {result['company_name']}")
                        logger.info(f"   Sector: {result['sector']} | Price: ${result['price']} | Change: {change_str}")
                        logger.info(f"   Score: {result['score']}")
                        
            except KeyboardInterrupt:
                logger.info("\nSearch interrupted by user")
                break
            except Exception as e:
                logger.error(f"Search error: {e}")
    
    def run_continuous_mode(self):
        """Run in continuous mode (fetch + search)"""
        logger.info("Starting continuous mode...")
        logger.info("Stock data will be updated automatically")
        logger.info("Press Ctrl+C to stop")
        
        try:
            while True:
                # Fetch new data
                self.stock_fetcher.fetch_all_stocks(STOCK_SYMBOLS)
                
                # Reload search data
                self.search_engine.load_stock_data(self.db_manager)
                
                # Wait for next update
                time.sleep(UPDATE_INTERVAL)
                
        except KeyboardInterrupt:
            logger.info("Continuous mode stopped by user")

def main():
    """Main application entry point"""
    app = StockSearchApp()
    
    # Initialize the system
    if not app.initialize_system():
        return
    
    # Ask user for mode
    while True:
        print("\n" + "=" * 50)
        print("SELECT MODE:")
        print("1. Interactive Search")
        print("2. Continuous Stock Monitoring")
        print("3. Exit")
        
        choice = input("Enter your choice (1-3): ").strip()
        
        if choice == '1':
            app.run_interactive_search()
        elif choice == '2':
            app.run_continuous_mode()
        elif choice == '3':
            logger.info("Thank you for using Stock Search Engine!")
            break
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")

if __name__ == "__main__":
    from flask import Flask
    try:
        app.run(host="0.0.0.0", port=5000, debug=True)
    except NameError:
        print("Flask app instance not found — make sure `app = Flask(__name__)` exists in this file.")


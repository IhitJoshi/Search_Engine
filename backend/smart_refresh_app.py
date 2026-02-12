"""
Smart On-Demand Refresh Flask Application
No Cron Jobs, No Background Workers, No Infinite Loops
Refresh happens intelligently in the GET /stocks endpoint
"""

import os
import logging
from datetime import datetime, timedelta
from flask import Flask, jsonify, request
from flask_cors import CORS
import smart_refresh_db as db

# ==========================================
# Configuration
# ==========================================
app = Flask(__name__)
CORS(app)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
REFRESH_THRESHOLD = 30  # Seconds - refresh if older than this
CACHE_TTL = 60  # Seconds - how long to keep cached data
MAX_RETRIES = 3


# ==========================================
# Mock Data Generator (Simulates Live API)
# ==========================================

STOCK_SYMBOLS = {
    'AAPL': {'name': 'Apple Inc.', 'sector': 'Technology'},
    'MSFT': {'name': 'Microsoft Corporation', 'sector': 'Technology'},
    'GOOGL': {'name': 'Alphabet Inc.', 'sector': 'Technology'},
    'AMZN': {'name': 'Amazon.com Inc.', 'sector': 'Consumer Cyclical'},
    'TSLA': {'name': 'Tesla Inc.', 'sector': 'Automotive'},
    'META': {'name': 'Meta Platforms Inc.', 'sector': 'Technology'},
    'NVDA': {'name': 'NVIDIA Corporation', 'sector': 'Technology'},
    'JPM': {'name': 'JPMorgan Chase Co.', 'sector': 'Financial'},
    'V': {'name': 'Visa Inc.', 'sector': 'Financial'},
    'WMT': {'name': 'Walmart Inc.', 'sector': 'Consumer Defensive'},
    'JNJ': {'name': 'Johnson & Johnson', 'sector': 'Healthcare'},
    'PG': {'name': 'Procter & Gamble Co.', 'sector': 'Consumer Defensive'},
    'XOM': {'name': 'Exxon Mobil Corporation', 'sector': 'Energy'},
    'BRK.B': {'name': 'Berkshire Hathaway Inc.', 'sector': 'Financial'},
    'MCD': {'name': "McDonald's Corporation", 'sector': 'Consumer Cyclical'},
}

BASE_PRICES = {
    'AAPL': 150.0, 'MSFT': 380.0, 'GOOGL': 140.0, 'AMZN': 165.0,
    'TSLA': 240.0, 'META': 380.0, 'NVDA': 875.0, 'JPM': 185.0,
    'V': 280.0, 'WMT': 90.0, 'JNJ': 160.0, 'PG': 85.0,
    'XOM': 105.0, 'BRK.B': 405.0, 'MCD': 295.0,
}


def fetch_live_data():
    """
    Mock function that simulates fetching live stock data from yfinance
    In production, replace with: yfinance.download() or API call
    
    Returns list of stocks with fresh prices
    """
    import random
    
    stocks = []
    for symbol, info in STOCK_SYMBOLS.items():
        base_price = BASE_PRICES[symbol]
        
        # Simulate realistic price fluctuations
        price_change = random.uniform(-2, 2)  # +/- 2 dollars
        new_price = max(base_price * 0.9, base_price + price_change)
        
        change_percent = (new_price - base_price) / base_price * 100
        volume = random.randint(1000000, 50000000)
        
        stocks.append({
            'symbol': symbol,
            'company_name': info['name'],
            'sector': info['sector'],
            'price': round(new_price, 2),
            'volume': volume,
            'change_percent': round(change_percent, 2),
            'summary': f"{info['name']} - {info['sector']} sector"
        })
    
    return stocks


# ==========================================
# Smart Refresh Logic
# ==========================================

def refresh_stocks_if_needed():
    """
    Smart refresh logic - only fetch if data is stale
    This is the CORE of the on-demand system
    """
    try:
        # Check if refresh is needed
        if not db.should_refresh():
            logger.info(f"Data is fresh (< 30s old). Using cache.")
            return True
        
        # Data is stale, fetch new data
        logger.info("Data is stale (> 30s old). Fetching fresh data...")
        
        new_stocks = fetch_live_data()
        
        if not new_stocks:
            logger.warning("Failed to fetch stock data")
            return False
        
        # Update database with new prices
        success = db.update_all_stocks(new_stocks)
        
        if success:
            logger.info(f"Successfully updated {len(new_stocks)} stocks")
            return True
        else:
            logger.error("Failed to update stocks in database")
            return False
            
    except Exception as e:
        logger.error(f"Error in refresh_stocks_if_needed: {e}")
        return False


def ensure_data_exists():
    """
    Ensure database is populated with initial stock data
    Runs on first request or when database is empty
    """
    if db.get_stock_count() == 0:
        logger.info("Database is empty. Initializing with stock data...")
        stocks = fetch_live_data()
        
        for stock in stocks:
            db.insert_stock(
                symbol=stock['symbol'],
                company_name=stock['company_name'],
                sector=stock['sector'],
                price=stock['price'],
                volume=stock['volume'],
                change_percent=stock['change_percent'],
                summary=stock['summary']
            )
        
        logger.info(f"Initialized database with {len(stocks)} stocks")
        return True
    
    return False


# ==========================================
# API Routes
# ==========================================

@app.route('/health', methods=['GET'])
def health():
    """
    Health check endpoint for Render
    Used by Render to verify app is running
    """
    try:
        # Quick database connectivity check
        count = db.get_stock_count()
        status = "healthy" if count > 0 else "initializing"
        
        return jsonify({
            'status': status,
            'timestamp': datetime.utcnow().isoformat(),
            'stocks_count': count,
            'last_refresh': db.get_time_since_last_update()
        }), 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500


@app.route('/api/stocks', methods=['GET'])
def get_stocks():
    """
    Smart On-Demand Refresh endpoint
    
    Flow:
    1. Ensure data exists in database
    2. Check if cached data is fresh (< 30 seconds)
    3. If stale (> 30 seconds), fetch new data from mock API
    4. Return stocks with timestamp info
    
    This is where the magic happens - NO CRON JOBS NEEDED!
    """
    try:
        # Step 1: Ensure database has initial data
        ensure_data_exists()
        
        # Step 2: Smart refresh - only if data is stale
        refresh_stocks_if_needed()
        
        # Step 3: Fetch and return stocks from database
        stocks = db.get_all_stocks()
        
        # Get metadata about last refresh
        time_since_update = db.get_time_since_last_update()
        
        return jsonify({
            'data': stocks,
            'meta': {
                'count': len(stocks),
                'last_refresh_seconds_ago': round(time_since_update, 2) if time_since_update else None,
                'timestamp': datetime.utcnow().isoformat(),
                'needs_refresh': db.should_refresh()
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error in get_stocks: {e}")
        return jsonify({
            'error': 'Failed to fetch stocks',
            'details': str(e)
        }), 500


@app.route('/api/stocks/<symbol>', methods=['GET'])
def get_stock(symbol):
    """
    Get single stock by symbol
    Also performs smart refresh check for this symbol
    """
    try:
        # Ensure data exists first
        ensure_data_exists()
        
        # Smart refresh if needed
        refresh_stocks_if_needed()
        
        # Get stock
        stock = db.get_stock(symbol.upper())
        
        if not stock:
            return jsonify({'error': f'Stock {symbol} not found'}), 404
        
        return jsonify({
            'data': stock,
            'meta': {
                'timestamp': datetime.utcnow().isoformat()
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error in get_stock {symbol}: {e}")
        return jsonify({
            'error': 'Failed to fetch stock',
            'details': str(e)
        }), 500


@app.route('/api/search', methods=['POST'])
def search_stocks():
    """
    Search stocks by query (existing endpoint maintained)
    """
    try:
        data = request.get_json()
        query = data.get('query', '').lower().strip()
        limit = data.get('limit', 50)
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        # Ensure data exists and refresh if needed
        ensure_data_exists()
        refresh_stocks_if_needed()
        
        all_stocks = db.get_all_stocks()
        
        # Search logic
        results = []
        for stock in all_stocks:
            if (query in stock['symbol'].lower() or 
                query in stock['company_name'].lower() or
                query in stock['sector'].lower()):
                results.append(stock)
        
        return jsonify({
            'results': results[:limit],
            'count': len(results),
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error in search: {e}")
        return jsonify({
            'error': 'Search failed',
            'details': str(e)
        }), 500


@app.route('/api/refresh-status', methods=['GET'])
def refresh_status():
    """
    Debug endpoint to check refresh status
    Shows how much time remains before next refresh
    """
    try:
        time_since = db.get_time_since_last_update()
        needs_refresh = db.should_refresh()
        time_until_refresh = max(0, 30 - (time_since or 0))
        
        return jsonify({
            'last_update_seconds_ago': round(time_since, 2) if time_since else None,
            'needs_refresh': needs_refresh,
            'seconds_until_next_refresh': round(time_until_refresh, 2),
            'threshold': 30,
            'stock_count': db.get_stock_count(),
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"Error in refresh_status: {e}")
        return jsonify({'error': str(e)}), 500


# ==========================================
# Error Handlers
# ==========================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def server_error(error):
    logger.error(f"Server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500


# ==========================================
# Initialization
# ==========================================

def initialize_app():
    """Initialize app on startup"""
    logger.info("🚀 Smart On-Demand Refresh System Starting...")
    logger.info("✅ No Cron Jobs | No Background Workers | No Infinite Loops")
    
    # Initialize database
    db.init_db()
    
    logger.info("✅ Database initialized")
    logger.info(f"📊 Smart Refresh Threshold: {REFRESH_THRESHOLD} seconds")
    logger.info("🟢 App ready for requests")


if __name__ == '__main__':
    initialize_app()
    
    # Development
    app.run(host='0.0.0.0', port=5000, debug=False)
else:
    # Production (Gunicorn)
    initialize_app()



from flask import Flask, request, jsonify, session
from flask_cors import CORS
import pandas as pd
import hashlib
import logging
from typing import Dict, Any
from app import StockSearchApp
import threading
import sqlite3
from ai_parser import parse_stock_query
from search import search_engine, search_stocks
from preprocessing import load_dataset, tokenize_all_columns
from database import init_db, get_connection, hash_password
from dotenv import load_dotenv
import google.generativeai as genai
import os
import re
import yfinance as yf
from ai_filter import parse_query_to_filters
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
models = genai.list_models(page_size=50)
print([m.name for m in models])

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = "supersecretkey_change_in_production"
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS

# CORS configuration
CORS(app, 
     supports_credentials=True,
     origins=[
    "http://localhost:5173",
    "http://127.0.0.1:5173"
],  # Frontend URLs
     allow_headers=["Content-Type", "Authorization"],
     methods=["GET", "POST", "PUT", "DELETE"])

# Initialize StockSearchApp
stock_app = StockSearchApp()

def initialize_stock_system():
    """Initialize stock system in background"""
    try:
        stock_app.initialize_system()
        logger.info("Stock system initialization completed")
    except Exception as e:
        logger.error(f"Stock system initialization failed: {e}")

def run_background_fetcher():
    # Fetch all 48 stocks from our complete list
    all_stocks = [
        # Technology
        "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "AVGO", "TSM", "TCEHY",
        # Finance
        "JPM", "BAC", "V", "MA", "PYPL", "SQ", "GS", "MS", "AXP", "INTU",
        # Energy
    "NEE", "ENPH", "FSLR", "VWS.CO", "ORSTED.CO", "XOM", "CVX", "BP", "TTE", "SHEL",
        # Healthcare
        "JNJ", "PFE", "MRK", "NVS", "RHHBY", "AMGN", "GILD", "BIIB", "REGN", "MRNA",
        # Automotive
        "NIO", "RIVN", "LCID", "BYD", "TM", "HMC", "GM", "F", "STLA", "VWAGY"
    ]
    stock_app.stock_fetcher.run_continuous_fetch(all_stocks, 60)

# Run initialization and background fetcher in separate threads
threading.Thread(target=initialize_stock_system, daemon=True).start()
threading.Thread(target=run_background_fetcher, daemon=True).start()

# Initialize database
init_db()

class APIError(Exception):
    """Custom API error class"""
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

@app.errorhandler(APIError)
def handle_api_error(error: APIError):
    """Handle API errors"""
    return jsonify({'error': error.message}), error.status_code

@app.errorhandler(Exception)
def handle_unexpected_error(error: Exception):
    """Handle unexpected errors"""
    logger.error(f"Unexpected error: {error}")
    return jsonify({'error': 'An unexpected error occurred'}), 500

def require_auth():
    """Decorator to require authentication"""
    def decorator(f):
        def wrapped(*args, **kwargs):
            if 'username' not in session:
                raise APIError('Authentication required', 401)
            return f(*args, **kwargs)
        wrapped.__name__ = f.__name__
        return wrapped
    return decorator

# Load and prepare data at startup
@app.before_request
def initialize_app():
    """Initialize application data"""
    # Skip heavy initialization for auth-related endpoints
    auth_paths = {"/api/login", "/api/signup", "/api/logout", "/api/auth/check", "/api/forgot-password"}
    try:
        if request.path in auth_paths or request.path.startswith("/static"):
            return
    except Exception:
        # In case request is not available or other edge cases, continue safely
        pass

    if not hasattr(app, "_initialized"):
        try:
            logger.info("Loading dataset and building search index...")
            global df
            df = load_dataset()
            df = tokenize_all_columns(df)
            search_engine.build_index(df)
            logger.info("Application initialized successfully")
            app._initialized = True
        except Exception as e:
            logger.error(f"Failed to initialize application: {e}")
            raise

# Authentication routes
@app.route("/api/signup", methods=["POST"])
def signup():
    """User registration endpoint"""
    try:
        data = request.get_json()
        print("📩 Received signup data:", data)
        if not data:
            raise APIError("No JSON data provided")
            
        username = data.get("username", "").strip()
        email = data.get("email", "").strip()
        password = data.get("password", "")
        
        if not all([username, email, password]):
            raise APIError("Missing required fields: username, email, password")
        
        if len(password) < 6:
            raise APIError("Password must be at least 6 characters long")
        
        with get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                    (username, email, hash_password(password))
                )
                conn.commit()
            except sqlite3.IntegrityError as e:
                if "username" in str(e):
                    raise APIError("Username already exists")
                elif "email" in str(e):
                    raise APIError("Email already exists")
                else:
                    raise APIError("User already exists")
        
        logger.info(f"New user registered: {username}")
        return jsonify({
            'message': 'Registration successful!',
            'username': username
        }), 201
        
    except APIError:
        raise
    except Exception as e:
        logger.error(f"Signup error: {e}")
        raise APIError("Registration failed")

@app.route("/api/login", methods=["POST"])
def login():
    """User login endpoint"""
    try:
        data = request.get_json()
        if not data:
            raise APIError("No JSON data provided")
            
        username = data.get("username", "").strip()
        password = data.get("password", "")
        
        if not username or not password:
            raise APIError("Username and password required")
        
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT username, email FROM users WHERE username = ? AND password_hash = ?",
                (username, hash_password(password))
            )
            user = cursor.fetchone()
        
        if user:
            session['username'] = user['username']
            session['email'] = user['email']
            
            logger.info(f"User logged in: {username}")
            return jsonify({
                'message': 'Login successful!',
                'user': {
                    'username': user['username'],
                    'email': user['email']
                }
            })
        else:
            raise APIError("Invalid credentials", 401)
            
    except APIError:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise APIError("Login failed")

@app.route("/api/logout", methods=["POST"])
@require_auth()
def logout():
    """User logout endpoint"""
    username = session.get('username')
    session.clear()
    logger.info(f"User logged out: {username}")
    return jsonify({'message': 'Logout successful!'})

@app.route("/api/forgot-password", methods=["POST"])
def forgot_password():
    """Forgot password endpoint - sends reset instructions"""
    try:
        data = request.get_json()
        if not data:
            raise APIError("No JSON data provided")
            
        email = data.get("email", "").strip()
        
        if not email:
            raise APIError("Email is required")
        
        # For development: Always respond success without DB dependency
        # This avoids blocking on DB or email infra and prevents noisy errors
        logger.info(f"Password reset requested for email: {email}")
        return jsonify({
            'message': 'If that email exists, password reset instructions have been sent',
            'email': email
        })
            
    except APIError:
        raise
    except Exception as e:
        logger.error(f"Forgot password error: {e}")
        raise APIError("Failed to process password reset request")

@app.route("/api/auth/check", methods=["GET"])
def check_auth():
    """Check authentication status"""
    if 'username' in session:
        return jsonify({
            'logged_in': True,
            'username': session['username'],
            'email': session.get('email')
        })
    return jsonify({'logged_in': False})

# Search routes
@app.route('/api/search', methods=['POST'])
@require_auth()
def search():
    """Search endpoint with authentication"""
    try:
        data = request.get_json()
        if not data:
            raise APIError("No JSON data provided")
            
        query = data.get('query', '').strip()
        sector_filter = data.get('sector', '').strip()  # Optional sector filter
        limit = data.get('limit', 50)  # Optional limit
        
        # Allow empty query and sector to show all stocks
        if query and len(query) > 500:
            raise APIError("Query too long")

        logger.info(f"Received search query: '{query}', sector: '{sector_filter}', limit: {limit}")

        # --- If sector filter is provided, filter by sector first ---
        working_df = df
        if sector_filter:
            # Filter stocks by sector from the database
            with stock_app.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT DISTINCT symbol FROM stocks 
                    WHERE sector = ? 
                    ORDER BY last_updated DESC
                ''', (sector_filter,))
                sector_symbols = [row['symbol'] for row in cursor.fetchall()]
            
            if sector_symbols and 'symbol' in df.columns:
                # Filter dataframe to only include stocks from this sector
                working_df = df[df['symbol'].isin(sector_symbols)]
                logger.info(f"Filtered to {len(working_df)} stocks in sector '{sector_filter}'")
            else:
                logger.warning(f"No stocks found for sector '{sector_filter}'")
                working_df = df[df.index < 0]  # Empty dataframe
        else:
            # No sector filter - get ALL stocks from database
            with stock_app.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT DISTINCT symbol FROM stocks 
                    ORDER BY last_updated DESC
                ''')
                all_symbols = [row['symbol'] for row in cursor.fetchall()]
            
            if all_symbols and 'symbol' in df.columns:
                # Filter dataframe to only include stocks we have in database
                working_df = df[df['symbol'].isin(all_symbols)]
                logger.info(f"Showing all stocks: {len(working_df)} stocks in database")
        
        # --- Primary: use search engine ---
        if query:
            results = search_engine.search(query, working_df, top_n=limit)
        else:
            # If no query, just return all stocks from the filtered sector
            results = [(i, 1.0) for i in working_df.index[:limit]]

        # --- Fallback: direct keyword match if no results ---
        if not results or len(results) == 0:
            logger.warning(f"No results from search engine for '{query}', using fallback match.")
            query_lower = query.lower() if query else ""

            # Match against key columns if they exist
            match_columns = [c for c in ["symbol", "company_name", "sector", "industry", "name"] if c in working_df.columns]

            if match_columns and query_lower:
                filtered_df = working_df[
                    working_df.apply(
                        lambda row: any(
                            query_lower in str(row[col]).lower() for col in match_columns
                        ),
                        axis=1,
                    )
                ]

                # Create dummy scores for fallback results
                results = [(i, 1.0) for i in filtered_df.index[:limit]]
            else:
                logger.error(f"No searchable columns found in dataset for fallback.")
                results = []

        # --- Format results for JSON output ---
        # First, get live stock data from database
        with stock_app.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT s1.* FROM stocks s1
                JOIN (
                    SELECT symbol, MAX(last_updated) as latest 
                    FROM stocks 
                    GROUP BY symbol
                ) s2 ON s1.symbol = s2.symbol AND s1.last_updated = s2.latest
            ''')
            live_stocks = {row['symbol']: dict(row) for row in cursor.fetchall()}
        
        formatted_results = []
        for idx, (doc_idx, score) in enumerate(results[:limit], 1):
            if doc_idx >= len(working_df):
                continue
            doc_data = working_df.iloc[doc_idx]

            # Convert pandas types to Python native types for JSON serialization
            result_item = {}
            for col in working_df.columns:
                if col != 'tokens':
                    val = doc_data[col]
                    if pd.isna(val):
                        result_item[col] = None
                    elif isinstance(val, (pd.Int64Dtype, pd.Int32Dtype)) or hasattr(val, 'item'):
                        result_item[col] = int(val) if pd.notna(val) else None
                    elif isinstance(val, (float, pd.Float64Dtype)):
                        result_item[col] = float(val) if pd.notna(val) else None
                    else:
                        result_item[col] = str(val)
            
            # Merge with live stock data if available
            symbol = result_item.get('symbol')
            if symbol and symbol in live_stocks:
                # Override with live data
                result_item.update(live_stocks[symbol])
            
            # Add rank and score for reference
            result_item['_rank'] = idx
            result_item['_score'] = float(score)
            
            formatted_results.append(result_item)

        logger.info(f"Search completed for '{query}': {len(formatted_results)} results")
        return jsonify({
            'query': query,
            'total_results': len(formatted_results),
            'results': formatted_results,
            'time': 0  # Add time for compatibility
        })

    except APIError:
        raise
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise APIError("Search failed")

@app.route("/api/stocks", methods=["GET"])
def get_stocks():
    """Return latest stock data"""
    with stock_app.db_manager.get_connection() as conn:
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
        stocks = [dict(row) for row in rows]
    return jsonify(stocks)

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'documents': len(df) if 'df' in globals() else 0,
        'search_ready': search_engine.inverted_index is not None
    })

@app.route('/api/info', methods=['GET'])
@require_auth()
def app_info():
    """Application information endpoint"""
    return jsonify({
        'name': 'Stock Search API',
        'version': '1.0.0',
        'search_terms': len(search_engine.inverted_index) if search_engine.inverted_index else 0,
        'documents': len(df) if 'df' in globals() else 0
    })

# 🚀 In-memory cache for stock details (TTL: 5 minutes)
stock_details_cache = {}
CACHE_TTL = 300  # 5 minutes in seconds

@app.route("/api/stocks/<symbol>", methods=["GET"])
def get_stock_details(symbol):
    import traceback
    import pandas as pd
    import yfinance as yf
    from flask import jsonify, request

    try:
        range_param = request.args.get("range", "1D").upper()
        stock = yf.Ticker(symbol)

        # 🕒 Choose period + interval
        if range_param == "1D":
            # Intraday data for 1 day (shows time on x-axis)
            hist = stock.history(period="1d", interval="5m")
        elif range_param == "5D":
            hist = stock.history(period="5d", interval="30m")
        elif range_param == "1M":
            hist = stock.history(period="1mo", interval="1d")
        elif range_param == "3M":
            hist = stock.history(period="3mo", interval="1d")
        elif range_param == "1Y":
            hist = stock.history(period="1y", interval="1wk")
        else:
            hist = stock.history(period="1mo", interval="1d")

        if hist.empty:
            return jsonify({"error": "No data found"}), 404

        # 🔧 Handle Date or Datetime columns
        hist = hist.reset_index()
        date_col = "Date"
        if "Datetime" in hist.columns:
            date_col = "Datetime"

        # Format date/time nicely
        if range_param == "1D":
            hist[date_col] = pd.to_datetime(hist[date_col]).dt.strftime("%H:%M")
        else:
            hist[date_col] = pd.to_datetime(hist[date_col]).dt.strftime("%Y-%m-%d")

        # Remove duplicates
        hist = hist.drop_duplicates(subset=[date_col], keep="last")

        # 📊 Fetch basic stock info
        info = {}
        try:
            info = stock.info
        except Exception as e:
            print("[DEBUG] Failed fetching stock.info:", e)

        details = {
            "symbol": symbol,
            "name": info.get("longName", symbol),
            "sector": info.get("sector", "N/A"),
            "currentPrice": info.get("currentPrice", None),
            "marketCap": info.get("marketCap", None),
            "volume": info.get("volume", None),
        }

        chart_data = [
            {"date": row[date_col], "price": float(row["Close"])}
            for _, row in hist.iterrows()
        ]

        return jsonify({"details": details, "chart": chart_data})

    except Exception as e:
        print("[ERROR] Detailed exception:")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/api/query", methods=["POST"])
def ai_query():
    try:
        data = request.get_json()
        user_query = data.get("query", "")
        if not user_query:
            return jsonify({"error": "Missing query"}), 400

        print("[AI PARSER] Query:", user_query)
        filters = parse_stock_query(user_query)
        print("[AI PARSER] Filters:", filters)

        # Pass the parsed filters to your search logic
        results = search_stocks(filters)
        return jsonify({"filters": filters, "results": results})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
def parse_query_with_gemini(query):
    # --- Replace with your Gemini call if you have it ---
    return query.lower()
STOCK_DATABASE = [
    # Technology
    {"name": "Apple Inc.", "symbol": "AAPL", "sector": "Technology"},
    {"name": "Microsoft Corporation", "symbol": "MSFT", "sector": "Technology"},
    {"name": "Alphabet Inc.", "symbol": "GOOGL", "sector": "Technology"},
    {"name": "Amazon.com Inc.", "symbol": "AMZN", "sector": "Consumer Discretionary"},
    {"name": "NVIDIA Corporation", "symbol": "NVDA", "sector": "Technology"},
    {"name": "Meta Platforms Inc.", "symbol": "META", "sector": "Technology"},
    {"name": "Tesla Inc.", "symbol": "TSLA", "sector": "Automotive"},
    {"name": "Adobe Inc.", "symbol": "ADBE", "sector": "Technology"},
    {"name": "Intel Corporation", "symbol": "INTC", "sector": "Technology"},
    {"name": "Oracle Corporation", "symbol": "ORCL", "sector": "Technology"},

    # Finance
    {"name": "JPMorgan Chase & Co.", "symbol": "JPM", "sector": "Financials"},
    {"name": "Bank of America Corporation", "symbol": "BAC", "sector": "Financials"},
    {"name": "Wells Fargo & Company", "symbol": "WFC", "sector": "Financials"},
    {"name": "Goldman Sachs Group", "symbol": "GS", "sector": "Financials"},
    {"name": "Citigroup Inc.", "symbol": "C", "sector": "Financials"},
    {"name": "Visa Inc.", "symbol": "V", "sector": "Financials"},
    {"name": "Mastercard Incorporated", "symbol": "MA", "sector": "Financials"},

    # Healthcare
    {"name": "Johnson & Johnson", "symbol": "JNJ", "sector": "Healthcare"},
    {"name": "Pfizer Inc.", "symbol": "PFE", "sector": "Healthcare"},
    {"name": "Merck & Co.", "symbol": "MRK", "sector": "Healthcare"},
    {"name": "UnitedHealth Group", "symbol": "UNH", "sector": "Healthcare"},
    {"name": "AbbVie Inc.", "symbol": "ABBV", "sector": "Healthcare"},
    {"name": "Eli Lilly and Company", "symbol": "LLY", "sector": "Healthcare"},

    # Energy
    {"name": "Exxon Mobil Corporation", "symbol": "XOM", "sector": "Energy"},
    {"name": "Chevron Corporation", "symbol": "CVX", "sector": "Energy"},
    {"name": "Shell PLC", "symbol": "SHEL", "sector": "Energy"},
    {"name": "BP p.l.c.", "symbol": "BP", "sector": "Energy"},
    {"name": "TotalEnergies SE", "symbol": "TTE", "sector": "Energy"},

    # Retail & Consumer
    {"name": "Walmart Inc.", "symbol": "WMT", "sector": "Retail"},
    {"name": "The Home Depot, Inc.", "symbol": "HD", "sector": "Retail"},
    {"name": "Costco Wholesale Corporation", "symbol": "COST", "sector": "Retail"},
    {"name": "McDonald's Corporation", "symbol": "MCD", "sector": "Consumer"},
    {"name": "Nike, Inc.", "symbol": "NKE", "sector": "Consumer"},
    {"name": "Starbucks Corporation", "symbol": "SBUX", "sector": "Consumer"},

    # Indian Market
    {"name": "Reliance Industries Ltd.", "symbol": "RELIANCE.NS", "sector": "Energy"},
    {"name": "Infosys Ltd.", "symbol": "INFY.NS", "sector": "Technology"},
    {"name": "Tata Consultancy Services Ltd.", "symbol": "TCS.NS", "sector": "Technology"},
    {"name": "HDFC Bank Ltd.", "symbol": "HDFCBANK.NS", "sector": "Financials"},
    {"name": "ICICI Bank Ltd.", "symbol": "ICICIBANK.NS", "sector": "Financials"},
    {"name": "State Bank of India", "symbol": "SBIN.NS", "sector": "Financials"},
    {"name": "Bharti Airtel Ltd.", "symbol": "BHARTIARTL.NS", "sector": "Telecom"},
    {"name": "ITC Ltd.", "symbol": "ITC.NS", "sector": "Consumer"},
    {"name": "Hindustan Unilever Ltd.", "symbol": "HINDUNILVR.NS", "sector": "Consumer"},
    {"name": "Adani Enterprises Ltd.", "symbol": "ADANIENT.NS", "sector": "Infrastructure"},
]

# ---------------------------------------------
# Helper to match query keywords
# ---------------------------------------------
def filter_stocks_by_query(query):
    query_lower = query.lower()

    matched = []
    for stock in STOCK_DATABASE:
        if (
            query_lower in stock["name"].lower()
            or query_lower in stock["symbol"].lower()
            or query_lower in stock["sector"].lower()
        ):
            matched.append(stock)

    # Keyword-based filters
    keyword_map = {
        "tech": "Technology",
        "software": "Technology",
        "bank": "Financials",
        "finance": "Financials",
        "health": "Healthcare",
        "energy": "Energy",
        "oil": "Energy",
        "retail": "Retail",
        "consumer": "Consumer",
        "india": ".NS",
        "indian": ".NS",
    }

    for key, sector in keyword_map.items():
        if key in query_lower:
            matched += [s for s in STOCK_DATABASE if sector in (s["sector"] or s["symbol"])]

    # Remove duplicates
    seen = set()
    unique = []
    for m in matched:
        if m["symbol"] not in seen:
            unique.append(m)
            seen.add(m["symbol"])
    return unique

# ---------------------------------------------
# AI Search Route (main logic)
# ---------------------------------------------
@app.route("/api/ai_search", methods=["POST"])
def ai_search():
    try:
        data = request.get_json()
        query = data.get("query", "").strip()

        if not query:
            return jsonify({"error": "Empty query"}), 400

        # Reject gibberish queries (no alphabets or too short)
        if len(query) < 3 or not re.search("[a-zA-Z]", query):
            return jsonify({"results": []})

        filtered_stocks = filter_stocks_by_query(query)

        if not filtered_stocks:
            return jsonify({"results": []})

        results = []
        for stock in filtered_stocks[:10]:  # Limit 10 to prevent slowdowns
            try:
                ticker = yf.Ticker(stock["symbol"])
                info = ticker.info

                results.append({
                    "company_name": stock["name"],
                    "symbol": stock["symbol"],
                    "sector": stock["sector"],
                    "price": info.get("currentPrice") or info.get("regularMarketPrice"),
                    "volume": info.get("volume"),
                    "change_percent": info.get("regularMarketChangePercent"),
                    "changed": "up" if (info.get("regularMarketChange", 0) or 0) > 0 else "down",
                })
            except Exception as e:
                print(f"Error fetching {stock['symbol']}: {e}")
                continue

        return jsonify({"results": results})

    except Exception as e:
        print("AI Search Error:", e)
        return jsonify({"error": str(e)}), 500




if __name__ == '__main__':
    logger.info("Starting Flask application...")
    app.run(debug=False, host='0.0.0.0', port=5000)


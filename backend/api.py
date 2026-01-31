

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
import os
import re
import json
import yfinance as yf
from ai_filter import parse_query_to_filters
# Import BM25 stock ranking system
from stock_tokenizer import stock_tokenizer, query_tokenizer
from bm25_stock_ranker import create_ranker
# Import response synthesizer
from response_synthesizer import response_synthesizer
from datetime import datetime
load_dotenv()

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
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "http://localhost:5175",
    "http://127.0.0.1:5175"
],  # Frontend URLs
     allow_headers=["Content-Type", "Authorization"],
     methods=["GET", "POST", "PUT", "DELETE"])

# Initialize StockSearchApp
stock_app = StockSearchApp()

# Initialize BM25 stock ranker (safe defaults: k1=1.5, b=0.75)
# WHY: k1=1.5 balances term frequency, b=0.75 provides moderate length normalization
stock_ranker = create_ranker(
    stock_tokenizer=stock_tokenizer,
    query_tokenizer=query_tokenizer,
    k1=1.5,  # Term frequency saturation - good for stock signals
    b=0.75   # Document length normalization - moderate penalty
)

def initialize_stock_system():
    """Initialize stock system in background, then start the fetcher"""
    try:
        # First, initialize the system (creates tables)
        stock_app.initialize_system()
        logger.info("Stock system initialization completed")
        
        # Only start the background fetcher AFTER initialization is complete
        run_background_fetcher()
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

# Run initialization in a single background thread
# The background fetcher will start automatically after initialization completes
threading.Thread(target=initialize_stock_system, daemon=True).start()

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
    """
    Search endpoint with BM25-based stock ranking.
    
    FLOW:
    1. Extract query and filters from request
    2. Fetch live stock data from database
    3. Apply sector/filters if specified
    4. Tokenize query and stocks
    5. Rank with BM25
    6. Return top-K results
    """
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

        # --- STEP 1: Fetch live stock data from database ---
        with stock_app.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            if sector_filter:
                # Filter by specific sector
                cursor.execute('''
                    SELECT s1.* FROM stocks s1
                    JOIN (
                        SELECT symbol, MAX(last_updated) as latest 
                        FROM stocks 
                        WHERE sector = ?
                        GROUP BY symbol
                    ) s2 ON s1.symbol = s2.symbol AND s1.last_updated = s2.latest
                    ORDER BY s1.last_updated DESC
                ''', (sector_filter,))
            else:
                # Get all latest stock data
                cursor.execute('''
                    SELECT s1.* FROM stocks s1
                    JOIN (
                        SELECT symbol, MAX(last_updated) as latest 
                        FROM stocks 
                        GROUP BY symbol
                    ) s2 ON s1.symbol = s2.symbol AND s1.last_updated = s2.latest
                    ORDER BY s1.last_updated DESC
                ''')
            
            live_stocks = [dict(row) for row in cursor.fetchall()]
        
        logger.info(f"Fetched {len(live_stocks)} live stock snapshots")
        
        if not live_stocks:
            logger.warning("No stock data available in database")
            return jsonify({
                'query': query,
                'total_results': 0,
                'results': [],
                'message': 'No stock data available. Please wait for data to be fetched.'
            })
        
        # --- STEP 2: Use BM25 ranking if query provided ---
        if query:
            # Use BM25 ranker for intent-based search
            ranked_results = stock_ranker.rank_live_stocks(
                query=query,
                live_stocks=live_stocks,
                top_k=limit
            )
            
            # Convert ranker output to response synthesizer input format
            # WHY: Ranker returns tuples, synthesizer expects dicts with tokens
            formatted_for_synthesizer = []
            for symbol, score, stock_data in ranked_results:
                # Preserve all stock data and add score + tokens
                result_dict = {**stock_data}  # Copy all fields
                result_dict['_score'] = score
                # Tokens are already in stock_data from ranker
                formatted_for_synthesizer.append(result_dict)
            
            # Use response synthesizer to create structured response
            # WHY: Separates ranking from response formatting
            response = response_synthesizer.synthesize_response(
                query=query,
                ranked_results=formatted_for_synthesizer,
                ranking_method='bm25',
                metadata={'sector_filter': sector_filter} if sector_filter else None
            )
            
            logger.info(f"BM25 ranking completed: {len(response['results'])} results")
            return jsonify(response)
        else:
            # No query - return all stocks using synthesizer for consistency
            formatted_for_synthesizer = []
            for stock_data in live_stocks[:limit]:
                result_dict = {**stock_data}
                result_dict['_score'] = 1.0
                result_dict['tokens'] = []  # No matching tokens
                formatted_for_synthesizer.append(result_dict)
            
            response = response_synthesizer.synthesize_response(
                query=query or '',
                ranked_results=formatted_for_synthesizer,
                ranking_method='default',
                metadata={'sector_filter': sector_filter} if sector_filter else None
            )
            
            logger.info(f"Returning all stocks: {len(response['results'])} results")
            return jsonify(response)

    except APIError:
        raise
    except Exception as e:
        logger.error(f"Search error: {e}", exc_info=True)
        raise APIError(f"Search failed: {str(e)}")

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
# AI Search Route - BM25 Based (NO LLM)
# ---------------------------------------------
# DESIGN RATIONALE:
# - Uses BM25 for deterministic, explainable ranking
# - Token-based explanations instead of AI-generated text
# - Safer for financial applications (no hallucinations)
# - Fast and reliable (no external API calls)

@app.route("/api/ai_search", methods=["POST"])
def ai_search():
    """
    Search endpoint using BM25 ranking with deterministic response generation.
    NO LLM USAGE - All explanations come from static token mappings.
    """
    logger.info("API HIT: /api/ai_search")
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
            
        query = data.get("query", "").strip()

        if not query:
            return jsonify({"error": "Empty query"}), 400

        if len(query) > 500:
            return jsonify({"error": "Query too long"}), 400

        logger.info(f"Processing search query: '{query}'")

        # --- STEP 1: Fetch live stock data from database ---
        with stock_app.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT s1.* FROM stocks s1
                JOIN (
                    SELECT symbol, MAX(last_updated) as latest 
                    FROM stocks 
                    GROUP BY symbol
                ) s2 ON s1.symbol = s2.symbol AND s1.last_updated = s2.latest
                ORDER BY s1.last_updated DESC
            ''')
            live_stocks = [dict(row) for row in cursor.fetchall()]

        if not live_stocks:
            logger.warning("No stock data available in database")
            return jsonify({
                "query": query,
                "summary": "No stock data available. Please wait for data to be fetched.",
                "results": []
            })

        logger.info(f"Fetched {len(live_stocks)} live stock snapshots")

        # --- STEP 2: Rank stocks using BM25 ---
        ranked_results = stock_ranker.rank_live_stocks(
            query=query,
            live_stocks=live_stocks,
            top_k=12
        )

        if not ranked_results:
            return jsonify({
                "query": query,
                "summary": f"No matching stocks found for '{query}'.",
                "results": []
            })

        # --- STEP 3: Format results using response synthesizer ---
        formatted_for_synthesizer = []
        for symbol, score, stock_data in ranked_results:
            result_dict = {**stock_data}
            result_dict['_score'] = score
            formatted_for_synthesizer.append(result_dict)

        response = response_synthesizer.synthesize_response(
            query=query,
            ranked_results=formatted_for_synthesizer,
            ranking_method='bm25'
        )

        # --- STEP 4: Generate deterministic summary ---
        summary = _generate_deterministic_summary(query, response['results'])

        # --- STEP 5: Format final response for frontend ---
        results = []
        for item in response['results']:
            results.append({
                "symbol": item.get('symbol'),
                "name": item.get('company_name', item.get('symbol')),
                "price": item.get('metrics', {}).get('price'),
                "volume": item.get('metrics', {}).get('volume'),
                "change_percent": item.get('metrics', {}).get('change_percent'),
                "changed": "up" if (item.get('metrics', {}).get('change_percent') or 0) > 0 else "down",
                "rank": item.get('rank'),
                "score": item.get('score'),
                "reasons": item.get('reasons', [])
            })

        logger.info(f"Returning {len(results)} ranked results for query: '{query}'")

        return jsonify({
            "query": query,
            "summary": summary,
            "results": results,
            "timestamp": datetime.now().isoformat() + 'Z'
        })

    except Exception as e:
        logger.error(f"AI Search Error: {e}", exc_info=True)
        return jsonify({"error": "Search failed. Please try again."}), 500



def _generate_deterministic_summary(query: str, results: list) -> str:
    """Generate a deterministic, rule-based summary from search results."""
    if not results:
        return f"No stocks found matching '{query}'."
    
    num_results = len(results)
    top_symbols = [r.get('symbol', 'Unknown') for r in results[:5]]
    
    all_reasons = set()
    for r in results:
        for reason in r.get('reasons', []):
            all_reasons.add(reason)
    
    summary_parts = [f"Found {num_results} stocks matching '{query}'."]
    
    if top_symbols:
        summary_parts.append(f"Top matches: {', '.join(top_symbols)}.")
    
    if all_reasons:
        top_reasons = list(all_reasons)[:3]
        summary_parts.append(f"Key signals: {'; '.join(top_reasons)}.")
    
    return " ".join(summary_parts)


if __name__ == '__main__':
    logger.info("Starting Flask application...")
    app.run(debug=False, host='0.0.0.0', port=5000)


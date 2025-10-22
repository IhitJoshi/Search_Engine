

from flask import Flask, request, jsonify, session
from flask_cors import CORS
import pandas as pd
import hashlib
import logging
from typing import Dict, Any
from app import StockSearchApp
import threading
import sqlite3

from search import search_engine, preprocess_query
from preprocessing import load_dataset, tokenize_all_columns
from database import init_db, get_connection, hash_password

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
# Initialize StockSearchApp and run data fetcher in background
stock_app = StockSearchApp()
stock_app.initialize_system()

def run_background_fetcher():
    stock_app.stock_fetcher.run_continuous_fetch(["AAPL","MSFT","GOOG","AMZN","TSLA","NVDA","META","NFLX","AMD","INTC"], 60)

# Run background fetcher in a separate thread
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

@app.route("/api/auth/check", methods=["GET"])
def check_auth():
    """Check authentication status"""
    if 'username' in session:
        return jsonify({
            'authenticated': True,
            'user': {
                'username': session['username'],
                'email': session.get('email')
            }
        })
    return jsonify({'authenticated': False})

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
        if not query:
            raise APIError("Query cannot be empty")
        if len(query) > 500:
            raise APIError("Query too long")
        print(df.columns)
        print(df.head().to_dict(orient="records"))

        logger.info(f"Received search query: '{query}'")

        # --- Primary: use search engine ---
        results = search_engine.search(query, df, top_n=10)

        # --- Fallback: direct keyword match if no results ---
        if not results or len(results) == 0:
            logger.warning(f"No results from search engine for '{query}', using fallback match.")
            query_lower = query.lower()

            # Match against key columns if they exist
            match_columns = [c for c in ["symbol", "company_name", "sector", "industry", "name"] if c in df.columns]

            if match_columns:
                filtered_df = df[
                    df.apply(
                        lambda row: any(
                            query_lower in str(row[col]).lower() for col in match_columns
                        ),
                        axis=1,
                    )
                ]

                # Create dummy scores for fallback results
                results = [(i, 1.0) for i in filtered_df.index]
            else:
                logger.error(f"No searchable columns found in dataset for fallback.")
                results = []

        # --- Format results for JSON output ---
        formatted_results = []
        for idx, (doc_idx, score) in enumerate(results, 1):
            if doc_idx >= len(df):
                continue
            doc_data = df.iloc[doc_idx]

            # Create preview text
            preview_parts = []
            for col in df.columns:
                if col != 'tokens' and pd.notna(doc_data[col]):
                    preview_parts.append(str(doc_data[col]))
            preview = " ".join(preview_parts)
            if len(preview) > 200:
                preview = preview[:200] + "..."

            formatted_results.append({
                'rank': idx,
                'doc_id': int(doc_idx),
                'score': float(score),
                'preview': preview.strip(),
                'data': {col: doc_data[col] for col in df.columns if col != 'tokens'}
            })

        logger.info(f"Search completed for '{query}': {len(formatted_results)} results")
        return jsonify({
            'query': query,
            'total_results': len(formatted_results),
            'results': formatted_results
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

if __name__ == '__main__':
    logger.info("Starting Flask application...")
    app.run(debug=True, host='0.0.0.0', port=5000)

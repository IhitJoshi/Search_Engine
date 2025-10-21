"""
Enhanced Flask API with better error handling and authentication
"""

from app import StockSearchApp

# Initialize the main application
try:
    stock_app = StockSearchApp()
    stock_app.initialize_databases()
    stock_app.load_and_preprocess_data()
    stock_app.initialize_search_engine()
    logger.info("Stock Search Application initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Stock Search Application: {e}")
    # You might want to exit here or handle this appropriately

# Then in your search endpoint, use:
@app.route('/api/search', methods=['POST'])
@require_auth()
def search():
    # Instead of using global df and search_engine
    results = stock_app.search(query, top_n=10)
    # ... rest of the function

from flask import Flask, request, jsonify, session
from flask_cors import CORS
import pandas as pd
import hashlib
import logging
from typing import Dict, Any

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
     origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # Frontend URLs
     allow_headers=["Content-Type", "Authorization"],
     methods=["GET", "POST", "PUT", "DELETE"])

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
@app.before_first_request
def initialize_app():
    """Initialize application data"""
    try:
        logger.info("Loading dataset and building search index...")
        global df
        df = load_dataset()
        df = tokenize_all_columns(df)
        search_engine.build_index(df)
        logger.info("Application initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        raise

# Authentication routes
@app.route("/api/signup", methods=["POST"])
def signup():
    """User registration endpoint"""
    try:
        data = request.get_json()
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
        
        # Perform search
        results = search_engine.search(query, df, top_n=10)
        
        # Format results
        formatted_results = []
        for idx, (doc_idx, score) in enumerate(results, 1):
            doc_data = df.iloc[doc_idx]
            
            # Create preview from all non-token columns
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
        
        logger.info(f"Search completed for '{query}': {len(results)} results")
        return jsonify({
            'query': query,
            'total_results': len(results),
            'results': formatted_results
        })
        
    except APIError:
        raise
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise APIError("Search failed")

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
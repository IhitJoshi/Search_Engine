from flask import Flask, request
from flask_cors import CORS
import logging
from dotenv import load_dotenv
import threading
from services.app import StockSearchApp
from core.bm25_stock_ranker import create_ranker
from utils.stock_tokenizer import stock_tokenizer, query_tokenizer
from utils.database import init_db
from utils.preprocessing import load_dataset, tokenize_all_columns
from core.search import search_engine
import os

# Import optimization modules
from utils.cache_manager import start_cache_cleanup_thread
from routes.optimized_routes import register_optimized_routes
from utils.performance_utils import configure_logging, metrics

load_dotenv()

# Setup optimized logging
configure_logging(
    level=logging.INFO,
    log_file='flask_log.txt',
    json_format=False
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "supersecretkey_change_in_production")
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = True  # Required for cross-origin cookies
app.config['SESSION_COOKIE_SAMESITE'] = 'None'  # Required for cross-origin cookies

# CORS configuration - Production origins
CORS(
    app,
    resources={r"/api/*": {
        "origins": [
            "https://stock-engine.vercel.app",
            "https://stock-engine-git-main-ihit-joshis-projects.vercel.app",
            "http://localhost:5173",
            "http://localhost:5174",
            "http://localhost:5175"
        ]
    }},
    supports_credentials=True
)


@app.after_request
def force_cors_headers(response):
    origin = request.headers.get("Origin")

    allowed_origins = [
        "https://stock-engine.vercel.app",
        "https://stock-engine-git-main-ihit-joshis-projects.vercel.app"
    ]

    if origin in allowed_origins:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"

    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"

    return response


# Health check endpoint
@app.route('/', methods=['GET'])
def root_health_check():
    return {"status": "ok", "message": "Service is running"}, 200

# Initialize StockSearchApp and DB
stock_app = StockSearchApp()

# Initialize BM25 stock ranker
stock_ranker = create_ranker(
    stock_tokenizer=stock_tokenizer,
    query_tokenizer=query_tokenizer,
    k1=1.5,
    b=0.75
)

# Background initialization and fetcher
def run_background_fetcher():
    all_stocks = [
        "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "AVGO", "TSM", "TCEHY",
        "JPM", "BAC", "V", "MA", "PYPL", "SQ", "GS", "MS", "AXP", "INTU",
        "NEE", "ENPH", "FSLR", "VWS.CO", "ORSTED.CO", "XOM", "CVX", "BP", "TTE", "SHEL",
        "JNJ", "PFE", "MRK", "NVS", "RHHBY", "AMGN", "GILD", "BIIB", "REGN", "MRNA",
        "NIO", "RIVN", "LCID", "BYD", "TM", "HMC", "GM", "F", "STLA", "VWAGY"
    ]
    try:
        stock_app.stock_fetcher.run_continuous_fetch(all_stocks, 60)
    except Exception:
        logger.exception("Background fetcher failed to start")


def initialize_stock_system():
    try:
        stock_app.initialize_system()
        logger.info("Stock system initialization completed")
        run_background_fetcher()
        logger.info("Background fetcher started - fetching all stocks")
    except Exception:
        logger.exception("Stock system initialization failed")

# Start initialization thread
threading.Thread(target=initialize_stock_system, daemon=True).start()

# Initialize database
init_db()

# Start cache cleanup thread
start_cache_cleanup_thread(interval=60)

# Register optimized API routes (/api/v2/*)
register_optimized_routes(app)

# App startup: load dataset and build search index lazily before first request
@app.before_request
def initialize_app():
    auth_paths = {"/api/login", "/api/signup", "/api/logout", "/api/auth/check", "/api/forgot-password"}
    try:
        if request.path in auth_paths or request.path.startswith("/static") or request.path.startswith("/api/v2"):
            return
    except Exception:
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
        except Exception:
            logger.exception("Failed to initialize application")


__all__ = ["app", "logger", "stock_app", "stock_ranker"]

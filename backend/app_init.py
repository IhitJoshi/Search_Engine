from flask import Flask, request
from flask_cors import CORS
import logging
from dotenv import load_dotenv
import threading
from app import StockSearchApp
from bm25_stock_ranker import create_ranker
from stock_tokenizer import stock_tokenizer, query_tokenizer
from database import init_db
from preprocessing import load_dataset, tokenize_all_columns
from search import search_engine
import os

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "supersecretkey_change_in_production")
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
     ],
     allow_headers=["Content-Type", "Authorization"],
     methods=["GET", "POST", "PUT", "DELETE"])

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

# App startup: load dataset and build search index lazily before first request
@app.before_request
def initialize_app():
    auth_paths = {"/api/login", "/api/signup", "/api/logout", "/api/auth/check", "/api/forgot-password"}
    try:
        if request.path in auth_paths or request.path.startswith("/static"):
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

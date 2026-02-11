from app_init import app
import errors
from routes import auth_routes
from routes import search_routes
from routes import stock_routes
from routes import ws_routes

# Export app for Vercel serverless function
# This allows Vercel to properly handle the Flask application
handler = app

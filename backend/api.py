from app_init import app
import errors
from routes import auth_routes
from routes import search_routes
from routes import stock_routes

# Export app for Vercel serverless function
# This allows Vercel to properly handle the Flask application
handler = app

# For local development
if __name__ == "__main__":
    import os
    # Run Flask development server
    port = int(os.environ.get("PORT", 5000))
    app.run(
        host="0.0.0.0",
        port=port,
        debug=True  # Enable debug mode for local development
    )

import os
from app_init import app, logger

# Import modules to register their routes and handlers
import errors      # registers error handlers
from routes import auth_routes
from routes import search_routes
from routes import stock_routes


if __name__ == "__main__":
    logger.info("Starting Flask application...")

    port = int(os.environ.get("PORT", 8000))  # <-- REQUIRED

    app.run(
        debug=False,
        host="0.0.0.0",
        port=port,
        threaded=True,
        use_reloader=False
    )

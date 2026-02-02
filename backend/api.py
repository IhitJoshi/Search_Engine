from app_init import app, logger

# Import modules to register their routes and handlers
import errors  # registers error handlers
import auth_routes
import search_routes
import stock_routes


if __name__ == '__main__':
    logger.info("Starting Flask application...")
    app.run(debug=False, host='0.0.0.0', port=5000, threaded=True, use_reloader=False)


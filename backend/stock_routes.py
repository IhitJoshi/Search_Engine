from flask import jsonify, request
from app_init import app, stock_app, logger
from errors import APIError, require_auth
import yfinance as yf
import pandas as pd


@app.route("/api/stocks", methods=["GET"])
def get_stocks():
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
    return jsonify({
        'status': 'healthy',
        'documents': len(app.df) if hasattr(app, 'df') else 0,
        'search_ready': getattr(app, '_initialized', False)
    })


@app.route('/api/info', methods=['GET'])
@require_auth()
def app_info():
    return jsonify({
        'name': 'Stock Search API',
        'version': '1.0.0',
        'search_terms': len(getattr(app, 'df', [])) if getattr(app, '_initialized', False) else 0,
        'documents': len(app.df) if hasattr(app, 'df') else 0
    })


@app.route("/api/stocks/<symbol>", methods=["GET"])
def get_stock_details(symbol):
    try:
        range_param = request.args.get("range", "1D").upper()
        stock = yf.Ticker(symbol)

        if range_param == "1D":
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

        hist = hist.reset_index()
        date_col = "Date"
        if "Datetime" in hist.columns:
            date_col = "Datetime"

        if range_param == "1D":
            hist[date_col] = pd.to_datetime(hist[date_col]).dt.strftime("%H:%M")
        else:
            hist[date_col] = pd.to_datetime(hist[date_col]).dt.strftime("%Y-%m-%d")

        hist = hist.drop_duplicates(subset=[date_col], keep="last")

        info = {}
        try:
            info = stock.info
        except Exception:
            logger.exception("Failed fetching stock.info")

        details = {
            "symbol": symbol,
            "name": info.get("longName", symbol),
            "sector": info.get("sector", "N/A"),
            "currentPrice": info.get("currentPrice", None),
            "marketCap": info.get("marketCap", None),
            "volume": info.get("volume", None),
        }

        chart_data = [
            {"date": row[date_col], "price": float(row["Close"]) }
            for _, row in hist.iterrows()
        ]

        return jsonify({"details": details, "chart": chart_data})

    except Exception:
        logger.exception("Stock details error")
        return jsonify({"error": "Failed to fetch stock details"}), 500

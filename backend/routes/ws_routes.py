import json
import time
import logging
from datetime import datetime

from app_init import sock
from utils.cache_manager import stock_cache
from utils.price_updater import PRICE_CACHE_PREFIX

logger = logging.getLogger(__name__)


@sock.route("/ws/stocks")
def stocks_ws(ws):
    """
    WebSocket endpoint for live stock updates.

    Client sends a single JSON message:
      { "symbols": ["AAPL", "MSFT"] }
    Server responds every 5 seconds with:
      { "timestamp": "...", "stocks": [ ... ] }
    """
    try:
        raw = ws.receive()
        if raw is None:
            return

        try:
            data = json.loads(raw)
        except Exception:
            data = {}

        symbols = data.get("symbols") or []
        symbols = [s.upper() for s in symbols if isinstance(s, str) and s.strip()]

        while True:
            now = datetime.utcnow().isoformat() + "Z"
            updates = []
            cached_map = {}

            for sym in symbols:
                cached = stock_cache.get(f"{PRICE_CACHE_PREFIX}:{sym}")
                if cached:
                    cached_map[sym] = cached

            for sym in symbols:
                payload = cached_map.get(sym)
                if payload:
                    updates.append({**payload, "timestamp": now})

            ws.send(json.dumps({"timestamp": now, "stocks": updates}))
            time.sleep(5)
    except Exception:
        logger.exception("WebSocket error")
    finally:
        try:
            ws.close()
        except Exception:
            pass

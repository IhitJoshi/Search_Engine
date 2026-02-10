import os
import time
import threading
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

import yfinance as yf
from flask import request
from flask_socketio import SocketIO, join_room, leave_room

logger = logging.getLogger(__name__)

DEFAULT_POLL_INTERVAL = int(os.environ.get("SOCKET_STOCK_POLL_INTERVAL", "10"))
MIN_POLL_INTERVAL = int(os.environ.get("SOCKET_STOCK_MIN_INTERVAL", "5"))
MAX_POLL_INTERVAL = int(os.environ.get("SOCKET_STOCK_MAX_INTERVAL", "60"))
DEFAULT_CACHE_TTL = int(os.environ.get("SOCKET_STOCK_CACHE_TTL", "5"))


def _clamp_interval(value: Optional[int]) -> int:
    if value is None:
        return DEFAULT_POLL_INTERVAL
    return max(MIN_POLL_INTERVAL, min(MAX_POLL_INTERVAL, int(value)))


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class StockStreamManager:
    def __init__(self, socketio: SocketIO):
        self.socketio = socketio
        self._lock = threading.RLock()
        self._subscriptions: Dict[str, set] = {}
        self._client_symbols: Dict[str, set] = {}
        self._client_intervals: Dict[str, Dict[str, int]] = {}
        self._symbol_intervals: Dict[str, int] = {}
        self._workers: Dict[str, bool] = {}
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._last_sent: Dict[str, Dict[str, Any]] = {}

    def register_handlers(self):
        @self.socketio.on("connect")
        def on_connect():
            return {"status": "ok"}

        @self.socketio.on("subscribe")
        def on_subscribe(data):
            payload = data or {}
            symbols = payload.get("symbols") or []
            interval = _clamp_interval(payload.get("interval"))
            self.subscribe(request.sid, symbols, interval)
            return {"subscribed": symbols, "interval": interval}

        @self.socketio.on("unsubscribe")
        def on_unsubscribe(data):
            payload = data or {}
            symbols = payload.get("symbols") or []
            self.unsubscribe(request.sid, symbols)
            return {"unsubscribed": symbols}

        @self.socketio.on("disconnect")
        def on_disconnect():
            self.disconnect(request.sid)

    def subscribe(self, sid: str, symbols: List[str], interval: int):
        if not symbols:
            return
        symbols = [s.upper().strip() for s in symbols if s]
        with self._lock:
            if sid not in self._client_symbols:
                self._client_symbols[sid] = set()
            if sid not in self._client_intervals:
                self._client_intervals[sid] = {}

            for symbol in symbols:
                join_room(symbol)
                self._client_symbols[sid].add(symbol)
                self._client_intervals[sid][symbol] = interval
                if symbol not in self._subscriptions:
                    self._subscriptions[symbol] = set()
                self._subscriptions[symbol].add(sid)

                current = self._symbol_intervals.get(symbol)
                self._symbol_intervals[symbol] = interval if current is None else min(current, interval)

                if not self._workers.get(symbol):
                    self._workers[symbol] = True
                    self.socketio.start_background_task(self._run_symbol_stream, symbol)

    def unsubscribe(self, sid: str, symbols: List[str]):
        if not symbols:
            return
        symbols = [s.upper().strip() for s in symbols if s]
        with self._lock:
            for symbol in symbols:
                leave_room(symbol)
                if sid in self._subscriptions.get(symbol, set()):
                    self._subscriptions[symbol].discard(sid)
                if sid in self._client_symbols:
                    self._client_symbols[sid].discard(symbol)
                if sid in self._client_intervals:
                    self._client_intervals[sid].pop(symbol, None)
                self._recalculate_interval(symbol)

    def disconnect(self, sid: str):
        with self._lock:
            symbols = list(self._client_symbols.get(sid, set()))
        if symbols:
            self.unsubscribe(sid, symbols)
        with self._lock:
            self._client_symbols.pop(sid, None)
            self._client_intervals.pop(sid, None)

    def _recalculate_interval(self, symbol: str):
        intervals = []
        for sid, sym_intervals in self._client_intervals.items():
            if symbol in sym_intervals:
                intervals.append(sym_intervals[symbol])
        if intervals:
            self._symbol_intervals[symbol] = min(intervals)
        else:
            self._symbol_intervals.pop(symbol, None)

    def _run_symbol_stream(self, symbol: str):
        try:
            while True:
                with self._lock:
                    has_subs = bool(self._subscriptions.get(symbol))
                    interval = self._symbol_intervals.get(symbol, DEFAULT_POLL_INTERVAL)
                if not has_subs:
                    break

                data = self._get_cached_or_fetch(symbol)
                if data:
                    last = self._last_sent.get(symbol)
                    if not last or last.get("price") != data.get("price") or last.get("change_percent") != data.get("change_percent"):
                        self.socketio.emit("stock_update", data, room=symbol)
                        self._last_sent[symbol] = {
                            "price": data.get("price"),
                            "change_percent": data.get("change_percent")
                        }
                self.socketio.sleep(interval)
        finally:
            with self._lock:
                self._workers.pop(symbol, None)

    def _get_cached_or_fetch(self, symbol: str) -> Optional[Dict[str, Any]]:
        now = time.time()
        cached = self._cache.get(symbol)
        if cached and (now - cached["fetched_at"] < DEFAULT_CACHE_TTL):
            return cached["data"]

        data = fetch_live_stock(symbol)
        if data:
            self._cache[symbol] = {"data": data, "fetched_at": now}
        return data


def fetch_live_stock(symbol: str) -> Optional[Dict[str, Any]]:
    try:
        ticker = yf.Ticker(symbol)
        info = {}
        fast = {}
        try:
            fast = ticker.fast_info or {}
        except Exception:
            fast = {}

        price = (
            fast.get("last_price") or
            fast.get("regular_market_price") or
            fast.get("regularMarketPrice")
        )
        previous_close = (
            fast.get("previous_close") or
            fast.get("previousClose")
        )

        if price is None:
            try:
                info = ticker.info or {}
            except Exception:
                info = {}
            price = (
                info.get("currentPrice") or
                info.get("regularMarketPrice") or
                info.get("previousClose")
            )
            previous_close = info.get("previousClose")

        change_percent = None
        if price is not None and previous_close:
            try:
                change_percent = ((price - previous_close) / previous_close) * 100
            except Exception:
                change_percent = None

        data = {
            "symbol": symbol,
            "price": round(price, 2) if price is not None else None,
            "change_percent": round(change_percent, 2) if change_percent is not None else None,
            "last_updated": _utc_iso()
        }
        return data
    except Exception as exc:
        logger.warning("Live fetch failed for %s: %s", symbol, exc)
        return None


def register_stock_streaming(socketio: SocketIO) -> StockStreamManager:
    manager = StockStreamManager(socketio)
    manager.register_handlers()
    logger.info("WebSocket stock streaming initialized")
    return manager

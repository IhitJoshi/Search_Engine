"""
Optimized API Routes - Compressed responses, lazy loading, micro-endpoints

FEATURES:
- GZIP compression for all responses
- Optimized stock endpoints with caching
- Micro-endpoints for specific data needs
- Response size reduction
- Performance timing headers
"""

import time
import gzip
import json
import logging
from functools import wraps
from flask import Blueprint, jsonify, request, Response, g
from typing import Optional

from utils.cache_manager import (
    stock_cache, chart_cache, search_cache, aggregation_cache,
    cache_key, cached
)
from utils.optimized_db import optimized_db
from services.async_fetcher import async_fetcher, fetch_chart_data_parallel
from utils.optimized_processing import optimized_tokenizer, tokenize_query_cached

logger = logging.getLogger(__name__)

# Create optimized API blueprint
optimized_api = Blueprint('optimized_api', __name__, url_prefix='/api/v2')


# ============================================================================
# MIDDLEWARE
# ============================================================================

def timing_middleware(f):
    """Add timing headers to responses"""
    @wraps(f)
    def decorated(*args, **kwargs):
        start = time.time()
        response = f(*args, **kwargs)
        elapsed = time.time() - start
        
        # Add timing header
        if hasattr(response, 'headers'):
            response.headers['X-Response-Time'] = f"{elapsed*1000:.2f}ms"
        
        # Log slow requests
        if elapsed > 0.5:
            logger.warning(f"Slow request: {request.path} took {elapsed:.3f}s")
        
        return response
    return decorated


def compress_response(f):
    """GZIP compress large responses"""
    @wraps(f)
    def decorated(*args, **kwargs):
        response = f(*args, **kwargs)
        
        # Check if client accepts gzip
        if 'gzip' not in request.headers.get('Accept-Encoding', ''):
            return response
        
        # Only compress JSON responses > 1KB
        if hasattr(response, 'data') and len(response.data) > 1024:
            compressed = gzip.compress(response.data)
            
            # Only use compression if it actually reduces size
            if len(compressed) < len(response.data):
                return Response(
                    compressed,
                    status=response.status_code,
                    headers={
                        'Content-Encoding': 'gzip',
                        'Content-Type': 'application/json',
                        'X-Original-Size': str(len(response.data)),
                        'X-Compressed-Size': str(len(compressed))
                    }
                )
        
        return response
    return decorated


# Apply middleware to all endpoints
@optimized_api.before_request
def before_request():
    g.start_time = time.time()


@optimized_api.after_request
def after_request(response):
    if hasattr(g, 'start_time'):
        elapsed = time.time() - g.start_time
        response.headers['X-Response-Time'] = f"{elapsed*1000:.2f}ms"
    return response


# ============================================================================
# STOCK ENDPOINTS - OPTIMIZED
# ============================================================================

@optimized_api.route('/stocks', methods=['GET'])
@compress_response
def get_stocks_optimized():
    """
    Get all stocks with caching and pagination.
    
    OPTIMIZATIONS:
    - Cached response (60s TTL)
    - Pagination support
    - Minimal response fields option
    """
    sector = request.args.get('sector')
    limit = min(int(request.args.get('limit', 100)), 500)
    offset = int(request.args.get('offset', 0))
    minimal = request.args.get('minimal', 'false').lower() == 'true'
    
    # Cache key includes all parameters
    key = cache_key('stocks', sector or 'all', limit, offset, minimal)
    
    cached_result = stock_cache.get(key)
    if cached_result:
        return jsonify(cached_result)
    
    # Fetch from optimized database
    stocks = optimized_db.get_latest_stocks(sector=sector, limit=limit + offset)
    stocks = stocks[offset:offset + limit]
    
    # Minimal response for list views
    if minimal:
        stocks = [
            {
                'symbol': s['symbol'],
                'company_name': s.get('company_name', s['symbol']),
                'price': s.get('price'),
                'change_percent': s.get('change_percent')
            }
            for s in stocks
        ]
    
    result = {
        'stocks': stocks,
        'count': len(stocks),
        'pagination': {
            'limit': limit,
            'offset': offset,
            'has_more': len(stocks) == limit
        }
    }
    
    stock_cache.set(key, result, ttl=60)
    return jsonify(result)


@optimized_api.route('/stocks/<symbol>', methods=['GET'])
@compress_response  
def get_stock_detail_optimized(symbol: str):
    """
    Get single stock details with chart data.
    
    OPTIMIZATIONS:
    - Cached stock details
    - Optional chart data (lazy loading)
    - Parallel chart fetching for all periods
    """
    include_chart = request.args.get('chart', 'false').lower() == 'true'
    chart_period = request.args.get('period', '1D')
    
    symbol = symbol.upper()
    
    # Check stock cache
    cache_key_stock = f"stock_detail:{symbol}"
    cached_stock = stock_cache.get(cache_key_stock)
    
    if not cached_stock:
        # Fetch from database
        stocks = optimized_db.get_stocks_batch([symbol])
        if symbol not in stocks:
            return jsonify({'error': 'Stock not found'}), 404
        cached_stock = stocks[symbol]
        stock_cache.set(cache_key_stock, cached_stock, ttl=60)
    
    result = {'details': cached_stock}
    
    # Lazy load chart data only if requested
    if include_chart:
        cache_key_chart = f"chart:{symbol}:{chart_period}"
        cached_chart = chart_cache.get(cache_key_chart)
        
        if not cached_chart:
            all_charts = fetch_chart_data_parallel(symbol, [chart_period])
            cached_chart = all_charts.get(chart_period, [])
            chart_cache.set(cache_key_chart, cached_chart, ttl=300)
        
        result['chart'] = cached_chart
    
    return jsonify(result)


@optimized_api.route('/stocks/<symbol>/chart', methods=['GET'])
@compress_response
def get_chart_only(symbol: str):
    """
    Micro-endpoint for chart data only.
    
    OPTIMIZATION: Smaller payload for chart-only updates.
    """
    period = request.args.get('period', '1D')
    symbol = symbol.upper()
    
    cache_key_chart = f"chart:{symbol}:{period}"
    cached_chart = chart_cache.get(cache_key_chart)
    
    if cached_chart:
        return jsonify({'symbol': symbol, 'period': period, 'data': cached_chart})
    
    all_charts = fetch_chart_data_parallel(symbol, [period])
    chart_data = all_charts.get(period, [])
    
    chart_cache.set(cache_key_chart, chart_data, ttl=300)
    
    return jsonify({'symbol': symbol, 'period': period, 'data': chart_data})


@optimized_api.route('/stocks/<symbol>/charts', methods=['GET'])
@compress_response
def get_all_charts(symbol: str):
    """
    Get all chart periods in single request.
    
    OPTIMIZATION: Single request instead of 5 separate requests.
    """
    symbol = symbol.upper()
    
    cache_key_all = f"charts_all:{symbol}"
    cached = chart_cache.get(cache_key_all)
    
    if cached:
        return jsonify({'symbol': symbol, 'charts': cached})
    
    charts = fetch_chart_data_parallel(symbol)
    chart_cache.set(cache_key_all, charts, ttl=300)
    
    return jsonify({'symbol': symbol, 'charts': charts})


# ============================================================================
# SEARCH ENDPOINT - OPTIMIZED
# ============================================================================

@optimized_api.route('/search', methods=['POST'])
@compress_response
def search_optimized():
    """
    Optimized search with caching.
    
    OPTIMIZATIONS:
    - Cached search results (2min TTL)
    - Pre-tokenized queries
    - Vectorized scoring
    """
    from bm25_stock_ranker import create_ranker
    from stock_tokenizer import stock_tokenizer, query_tokenizer
    from response_synthesizer import response_synthesizer
    
    data = request.get_json() or {}
    query = data.get('query', '').strip()
    sector = data.get('sector', '').strip()
    limit = min(data.get('limit', 50), 100)
    
    if not query:
        return jsonify({'error': 'Query required'}), 400
    
    # Check search cache
    search_key = cache_key('search', query, sector, limit)
    cached_result = search_cache.get(search_key)
    if cached_result:
        cached_result['cached'] = True
        return jsonify(cached_result)
    
    # Get stocks from optimized DB
    stocks = optimized_db.get_latest_stocks(sector=sector or None, limit=None)
    
    if not stocks:
        return jsonify({
            'query': query,
            'total_results': 0,
            'results': []
        })
    
    # Use optimized tokenization
    tokenized_stocks = []
    for stock in stocks:
        tokens = optimized_tokenizer.tokenize_stock_fast(stock)
        tokenized_stocks.append({**stock, 'tokens': tokens})
    
    # Use cached query tokenization
    query_tokens = list(tokenize_query_cached(query))
    
    if not query_tokens:
        return jsonify({
            'query': query,
            'total_results': 0,
            'results': []
        })
    
    # Vectorized scoring
    from optimized_processing import vectorized_scorer
    
    doc_tokens = [s['tokens'] for s in tokenized_stocks]
    scored_indices = vectorized_scorer.compute_bm25_vectorized(
        query_tokens, doc_tokens, top_k=limit
    )
    
    # Build results
    ranked_results = []
    for idx, score in scored_indices:
        stock = tokenized_stocks[idx]
        ranked_results.append({
            **stock,
            '_score': score
        })
    
    # Synthesize response
    response = response_synthesizer.synthesize_response(
        query=query,
        ranked_results=ranked_results,
        ranking_method='bm25_vectorized'
    )
    
    response['cached'] = False
    search_cache.set(search_key, response, ttl=120)
    
    return jsonify(response)


# ============================================================================
# AGGREGATION ENDPOINTS - PRE-COMPUTED
# ============================================================================

@optimized_api.route('/aggregations/sectors', methods=['GET'])
@compress_response
def get_sector_aggregations():
    """
    Get pre-computed sector statistics.
    
    OPTIMIZATION: Aggregated at DB level, cached for 10 minutes.
    """
    cached = aggregation_cache.get('sector_stats')
    if cached:
        return jsonify({'sectors': cached, 'cached': True})
    
    stats = optimized_db.get_sector_aggregations()
    aggregation_cache.set('sector_stats', stats, ttl=600)
    
    return jsonify({'sectors': stats, 'cached': False})


@optimized_api.route('/aggregations/trending', methods=['GET'])
@compress_response
def get_trending():
    """
    Get trending stocks (gainers/losers).
    
    OPTIMIZATION: Pre-sorted at DB level.
    """
    direction = request.args.get('direction', 'up')
    limit = min(int(request.args.get('limit', 10)), 50)
    
    cache_key_trend = f"trending:{direction}:{limit}"
    cached = aggregation_cache.get(cache_key_trend)
    
    if cached:
        return jsonify({'stocks': cached, 'direction': direction, 'cached': True})
    
    stocks = optimized_db.get_trending_stocks(direction=direction, limit=limit)
    
    # Minimal response for trending
    minimal_stocks = [
        {
            'symbol': s['symbol'],
            'company_name': s.get('company_name'),
            'price': s.get('price'),
            'change_percent': s.get('change_percent')
        }
        for s in stocks
    ]
    
    aggregation_cache.set(cache_key_trend, minimal_stocks, ttl=120)
    
    return jsonify({
        'stocks': minimal_stocks,
        'direction': direction,
        'cached': False
    })


# ============================================================================
# HEALTH & METRICS ENDPOINTS
# ============================================================================

@optimized_api.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': time.time()
    })


@optimized_api.route('/metrics', methods=['GET'])
def get_metrics():
    """Get performance metrics"""
    from utils.cache_manager import stock_cache, chart_cache, search_cache, aggregation_cache
    
    return jsonify({
        'caches': {
            'stock': stock_cache.get_metrics(),
            'chart': chart_cache.get_metrics(),
            'search': search_cache.get_metrics(),
            'aggregation': aggregation_cache.get_metrics()
        },
        'tokenizer': optimized_tokenizer.get_cache_stats(),
        'database': optimized_db.pool.get_stats()
    })


@optimized_api.route('/cache/clear', methods=['POST'])
def clear_caches():
    """Clear all caches (admin endpoint)"""
    from utils.cache_manager import invalidate_stock_cache
    
    invalidate_stock_cache()
    aggregation_cache.clear()
    
    return jsonify({'status': 'cleared'})


def register_optimized_routes(app):
    """Register optimized routes with Flask app"""
    app.register_blueprint(optimized_api)
    logger.info("Registered optimized API routes at /api/v2")

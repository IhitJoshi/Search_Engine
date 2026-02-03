from flask import request, jsonify
from app_init import app, stock_app, stock_ranker, logger
from errors import APIError, require_auth
from preprocessing import parse_query_filters
from response_synthesizer import response_synthesizer


@app.route('/api/search', methods=['POST'])
@require_auth()
def search():
    try:
        data = request.get_json()
        if not data:
            raise APIError("No JSON data provided")

        query = data.get('query', '').strip()
        sector_filter = data.get('sector', '').strip()
        limit = data.get('limit', 50)

        if query and len(query) > 500:
            raise APIError("Query too long")

        logger.info(f"Received search query: '{query}', sector: '{sector_filter}', limit: {limit}")

        # Fetch live stock data
        with stock_app.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            if sector_filter:
                cursor.execute('''
                    SELECT s1.* FROM stocks s1
                    JOIN (
                        SELECT symbol, MAX(last_updated) as latest 
                        FROM stocks 
                        WHERE sector = ?
                        GROUP BY symbol
                    ) s2 ON s1.symbol = s2.symbol AND s1.last_updated = s2.latest
                    ORDER BY s1.last_updated DESC
                ''', (sector_filter,))
            else:
                cursor.execute('''
                    SELECT s1.* FROM stocks s1
                    JOIN (
                        SELECT symbol, MAX(last_updated) as latest 
                        FROM stocks 
                        GROUP BY symbol
                    ) s2 ON s1.symbol = s2.symbol AND s1.last_updated = s2.latest
                    ORDER BY s1.last_updated DESC
                ''')
            live_stocks = [dict(row) for row in cursor.fetchall()]

        if not live_stocks:
            return jsonify({'query': query, 'total_results': 0, 'results': [], 'message': 'No stock data available. Please wait for data to be fetched.'})

        # parse implicit filters
        parsed_filters = parse_query_filters(query or "")
        implicit_sector = parsed_filters.get('sector', '')
        implicit_trend = parsed_filters.get('trend', '')
        is_all_stocks_query = parsed_filters.get('all_stocks', False)
        effective_sector = sector_filter or implicit_sector

        # If the user asked for "all stocks" WITHOUT specifying a sector,
        # ignore any sector filters so that a plain "all stocks" query
        # truly returns all stocks regardless of category. Preserve sector
        # filtering when the query explicitly includes a sector (e.g., "all stocks tech").
        if is_all_stocks_query and not (sector_filter or implicit_sector):
            effective_sector = ''

        # Apply sector filter if needed
        if effective_sector:
            eff = effective_sector.lower()
            def sector_match(row):
                try:
                    sec = (row.get('sector') or '').lower()
                    sym = (row.get('symbol') or '').lower()
                    if eff == 'india' and (sym.endswith('.ns') or '.ns' in sym):
                        return True
                    return eff in sec or eff in sym
                except Exception:
                    return False
            live_stocks = [s for s in live_stocks if sector_match(s)]

        # Apply trend filter
        trend_to_apply = implicit_trend
        if trend_to_apply:
            def get_change_value(s):
                for k in ('change_percent', 'change', 'price_change', 'chg'):
                    if k in s and s[k] is not None:
                        try:
                            return float(s[k])
                        except Exception:
                            continue
                try:
                    if 'previous_close' in s and 'price' in s and s['previous_close'] is not None and s['price'] is not None:
                        return float(s['price']) - float(s['previous_close'])
                    if 'close' in s and 'open' in s and s['close'] is not None and s['open'] is not None:
                        return float(s['close']) - float(s['open'])
                except Exception:
                    pass
                return None

            if trend_to_apply == 'up':
                live_stocks = [s for s in live_stocks if (get_change_value(s) or 0) > 0]
            elif trend_to_apply == 'down':
                live_stocks = [s for s in live_stocks if (get_change_value(s) or 0) < 0]

        # Ranking
        if is_all_stocks_query:
            # For "all stocks" queries, return all stocks without ranking
            formatted_for_synthesizer = []
            for stock_data in live_stocks[:limit]:
                result_dict = {**stock_data}
                result_dict['_score'] = 1.0
                result_dict['tokens'] = []
                formatted_for_synthesizer.append(result_dict)
            response = response_synthesizer.synthesize_response(query=query or 'all stocks', ranked_results=formatted_for_synthesizer, ranking_method='default', metadata={'sector_filter': effective_sector, 'all_stocks': True} if effective_sector else {'all_stocks': True})
            return jsonify(response)
        elif query:
            ranked_results = stock_ranker.rank_live_stocks(query=query, live_stocks=live_stocks, top_k=limit)
            formatted_for_synthesizer = []
            for symbol, score, stock_data in ranked_results:
                result_dict = {**stock_data}
                result_dict['_score'] = score
                formatted_for_synthesizer.append(result_dict)
            response = response_synthesizer.synthesize_response(query=query, ranked_results=formatted_for_synthesizer, ranking_method='bm25', metadata={'sector_filter': effective_sector} if effective_sector else None)
            return jsonify(response)
        else:
            formatted_for_synthesizer = []
            for stock_data in live_stocks[:limit]:
                result_dict = {**stock_data}
                result_dict['_score'] = 1.0
                result_dict['tokens'] = []
                formatted_for_synthesizer.append(result_dict)
            response = response_synthesizer.synthesize_response(query=query or '', ranked_results=formatted_for_synthesizer, ranking_method='default', metadata={'sector_filter': effective_sector} if effective_sector else None)
            return jsonify(response)

    except APIError:
        raise
    except Exception:
        logger.exception("Search error")
        raise APIError("Search failed")


@app.route("/api/ai_search", methods=["POST"])
def ai_search():
    logger.info("API HIT: /api/ai_search")
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        query = data.get("query", "").strip()
        limit = data.get("limit", 50)
        if not query:
            return jsonify({"error": "Empty query"}), 400
        if len(query) > 500:
            return jsonify({"error": "Query too long"}), 400

        # Fetch live stocks
        with stock_app.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT s1.* FROM stocks s1
                JOIN (
                    SELECT symbol, MAX(last_updated) as latest 
                    FROM stocks 
                    GROUP BY symbol
                ) s2 ON s1.symbol = s2.symbol AND s1.last_updated = s2.latest
                ORDER BY s1.last_updated DESC
            ''')
            live_stocks = [dict(row) for row in cursor.fetchall()]

        if not live_stocks:
            return jsonify({"query": query, "summary": "No stock data available. Please wait for data to be fetched.", "results": []})

        # apply implicit filters
        parsed_filters = parse_query_filters(query)
        effective_sector = parsed_filters.get('sector', '')
        trend_to_apply = parsed_filters.get('trend', '')
        is_all_stocks_query = parsed_filters.get('all_stocks', False)
        if is_all_stocks_query and not effective_sector:
            effective_sector = ''
        if effective_sector:
            eff = effective_sector.lower()
            def sector_match(row):
                try:
                    sec = (row.get('sector') or '').lower()
                    sym = (row.get('symbol') or '').lower()
                    if eff == 'india' and (sym.endswith('.ns') or '.ns' in sym):
                        return True
                    return eff in sec or eff in sym
                except Exception:
                    return False
            live_stocks = [s for s in live_stocks if sector_match(s)]
        if trend_to_apply:
            def get_change_value(s):
                for k in ('change_percent', 'change', 'price_change', 'chg'):
                    if k in s and s[k] is not None:
                        try:
                            return float(s[k])
                        except Exception:
                            continue
                try:
                    if 'previous_close' in s and 'price' in s and s['previous_close'] is not None and s['price'] is not None:
                        return float(s['price']) - float(s['previous_close'])
                    if 'close' in s and 'open' in s and s['close'] is not None and s['open'] is not None:
                        return float(s['close']) - float(s['open'])
                except Exception:
                    pass
                return None
            if trend_to_apply == 'up':
                live_stocks = [s for s in live_stocks if (get_change_value(s) or 0) > 0]
            elif trend_to_apply == 'down':
                live_stocks = [s for s in live_stocks if (get_change_value(s) or 0) < 0]

        if is_all_stocks_query:
            results = []
            for idx, item in enumerate(live_stocks[:limit], start=1):
                results.append({
                    "symbol": item.get('symbol'),
                    "name": item.get('company_name', item.get('symbol')),
                    "price": item.get('price'),
                    "volume": item.get('volume'),
                    "change_percent": item.get('change_percent'),
                    "changed": "up" if (item.get('change_percent') or 0) > 0 else "down",
                    "rank": idx,
                    "score": 1.0,
                    "reasons": []
                })
            summary = f"Found {len(results)} stocks for '{query}'."
            return jsonify({"query": query, "summary": summary, "results": results, "timestamp": __import__('datetime').datetime.now().isoformat() + 'Z'})

        ranked_results = stock_ranker.rank_live_stocks(query=query, live_stocks=live_stocks, top_k=12)
        if not ranked_results:
            return jsonify({"query": query, "summary": f"No matching stocks found for '{query}'.", "results": []})

        formatted_for_synthesizer = []
        for symbol, score, stock_data in ranked_results:
            result_dict = {**stock_data}
            result_dict['_score'] = score
            formatted_for_synthesizer.append(result_dict)

        response = response_synthesizer.synthesize_response(query=query, ranked_results=formatted_for_synthesizer, ranking_method='bm25')
        summary = _generate_deterministic_summary(query, response['results'])

        results = []
        for item in response['results']:
            results.append({
                "symbol": item.get('symbol'),
                "name": item.get('company_name', item.get('symbol')),
                "price": item.get('metrics', {}).get('price'),
                "volume": item.get('metrics', {}).get('volume'),
                "change_percent": item.get('metrics', {}).get('change_percent'),
                "changed": "up" if (item.get('metrics', {}).get('change_percent') or 0) > 0 else "down",
                "rank": item.get('rank'),
                "score": item.get('score'),
                "reasons": item.get('reasons', [])
            })

        return jsonify({"query": query, "summary": summary, "results": results, "timestamp": __import__('datetime').datetime.now().isoformat() + 'Z'})

    except Exception:
        logger.exception("AI Search Error")
        return jsonify({"error": "Search failed. Please try again."}), 500


# keep helper to allow import
def _generate_deterministic_summary(query: str, results: list) -> str:
    if not results:
        return f"No stocks found matching '{query}'."
    num_results = len(results)
    top_symbols = [r.get('symbol', 'Unknown') for r in results[:5]]
    all_reasons = set()
    for r in results:
        for reason in r.get('reasons', []):
            all_reasons.add(reason)
    summary_parts = [f"Found {num_results} stocks matching '{query}'."]
    if top_symbols:
        summary_parts.append(f"Top matches: {', '.join(top_symbols)}.")
    if all_reasons:
        top_reasons = list(all_reasons)[:3]
        summary_parts.append(f"Key signals: {'; '.join(top_reasons)}.")
    return " ".join(summary_parts)

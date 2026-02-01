"""
BM25 Ranker for Tokenized Stock Snapshots

CORE CONCEPT:
- This is NOT document retrieval
- A "document" = a tokenized stock snapshot (ephemeral, last few seconds)
- BM25 operates on symbolic tokens, NOT text
- Computed in-memory, no persistent index
- Returns TOP-K stock symbols ranked by relevance

ARCHITECTURE:
- Separates data fetching, tokenization, ranking, and responding
- Can be used with live streaming data
- Fast enough for real-time queries
"""

import math
import logging
from typing import List, Tuple, Dict, Any
from collections import Counter, defaultdict
from query_filter_engine import query_filter_engine

logger = logging.getLogger(__name__)


class StockBM25Ranker:
    """
    BM25 scoring for tokenized stock snapshots.
    
    WHY BM25:
    - Proven ranking algorithm (used in search engines)
    - Handles term frequency saturation (repeated tokens don't dominate)
    - Document length normalization (prevents bias toward long token lists)
    - Fast and deterministic
    
    PARAMETERS:
    - k1: Controls term frequency saturation (1.2-2.0 typical)
    - b: Controls document length normalization (0.75 typical)
    """
    
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        """
        Initialize BM25 ranker with configurable parameters.
        
        Args:
            k1: Term frequency saturation parameter
                - Lower k1 (1.2): Term frequency matters less after first occurrence
                - Higher k1 (2.0): Term frequency continues to matter more
                - Default 1.5: Balanced - good for stock signals
                
            b: Document length normalization parameter
                - b=0: No length normalization (all docs treated equally)
                - b=1: Full length normalization (penalizes longer docs)
                - Default 0.75: Moderate normalization
                
        WHY these defaults:
        - Stock snapshots are similar length (10-30 tokens typically)
        - k1=1.5: Repeated signals matter but not excessively
        - b=0.75: Some normalization but not aggressive
        """
        self.k1 = k1
        self.b = b
    
    def rank_stocks(
        self,
        query_tokens: List[str],
        stock_snapshots: List[Dict[str, Any]],
        top_k: int = 10
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """
        Rank stocks using BM25 on tokenized snapshots.
        
        WHY: This is the core ranking function that matches user intent
        to stock signals using BM25 scoring.
        
        NOTE: Filtering happens BEFORE this function is called.
        This function only performs BM25 ranking on pre-filtered stocks.
        
        Args:
            query_tokens: List of tokens from user query (from QueryTokenizer)
            stock_snapshots: List of dicts, each containing:
                - 'symbol': Stock ticker (e.g., 'AAPL')
                - 'tokens': List of tokens from StockTokenizer
                - Other metadata for display (price, sector, etc.)
            top_k: Number of top results to return
            
        Returns:
            List of tuples: (symbol, score, stock_data)
            Sorted by score descending (highest relevance first)
        """
        if not query_tokens:
            logger.warning("Empty query tokens, returning no results")
            return []
        
        if not stock_snapshots:
            logger.warning("No stock snapshots to rank")
            return []
        
        # STEP 1: Build ephemeral inverted index
        # WHY: Quick lookup of which stocks contain which tokens
        inverted_index = self._build_inverted_index(stock_snapshots)
        
        # STEP 2: Compute document statistics
        # WHY: Needed for BM25 formula (avg length, document frequencies)
        N = len(stock_snapshots)  # Total number of stocks
        doc_lengths = [len(snap.get('tokens', [])) for snap in stock_snapshots]
        avgdl = sum(doc_lengths) / N if N > 0 else 0
        
        # STEP 3: Score each stock
        # WHY: BM25 scoring matches query tokens to stock tokens
        scores = []
        
        for idx, snapshot in enumerate(stock_snapshots):
            symbol = snapshot.get('symbol', f'UNKNOWN_{idx}')
            doc_tokens = snapshot.get('tokens', [])
            doc_length = doc_lengths[idx]
            
            # Compute BM25 score for this stock
            score = self._compute_bm25_score(
                query_tokens=query_tokens,
                doc_tokens=doc_tokens,
                doc_length=doc_length,
                avgdl=avgdl,
                N=N,
                inverted_index=inverted_index
            )
            
            if score > 0:  # Only include stocks with non-zero relevance
                scores.append((symbol, score, snapshot))
        
        # STEP 4: Sort and return top K
        # WHY: Users only care about the most relevant stocks
        scores.sort(key=lambda x: x[1], reverse=True)
        top_results = scores[:top_k]
        
        logger.info(f"Ranked {len(stock_snapshots)} stocks, returning top {len(top_results)}")
        
        if top_results:
            logger.debug(f"Top result: {top_results[0][0]} (score: {top_results[0][1]:.4f})")
        
        return top_results
    
    def _build_inverted_index(
        self,
        stock_snapshots: List[Dict[str, Any]]
    ) -> Dict[str, List[int]]:
        """
        Build inverted index: token → list of document indices.
        
        WHY: Allows O(1) lookup of which stocks contain a token.
        This is ephemeral - rebuilt for each query with fresh data.
        
        Args:
            stock_snapshots: List of stock snapshot dictionaries
            
        Returns:
            Dict mapping token → list of document indices containing that token
        """
        inverted_index = defaultdict(list)
        
        for idx, snapshot in enumerate(stock_snapshots):
            tokens = snapshot.get('tokens', [])
            # Use set to avoid counting same token multiple times for same doc
            for token in set(tokens):
                inverted_index[token].append(idx)
        
        return dict(inverted_index)
    
    def _compute_bm25_score(
        self,
        query_tokens: List[str],
        doc_tokens: List[str],
        doc_length: int,
        avgdl: float,
        N: int,
        inverted_index: Dict[str, List[int]]
    ) -> float:
        """
        Compute BM25 score for a single document.
        
        WHY: This is the actual BM25 formula implementation.
        Each query term contributes to the final score based on:
        1. How rare the term is across all stocks (IDF)
        2. How frequently it appears in this stock (TF)
        3. Length normalization
        
        BM25 Formula:
        score = Σ IDF(qi) * (f(qi, D) * (k1 + 1)) / (f(qi, D) + k1 * (1 - b + b * |D| / avgdl))
        
        Where:
        - qi: Query term
        - f(qi, D): Frequency of qi in document D
        - |D|: Document length
        - avgdl: Average document length
        - IDF(qi): Inverse document frequency
        
        Args:
            query_tokens: Tokens from query
            doc_tokens: Tokens from stock snapshot
            doc_length: Number of tokens in document
            avgdl: Average document length across all stocks
            N: Total number of stocks
            inverted_index: Token to document indices mapping
            
        Returns:
            BM25 score (float)
        """
        score = 0.0
        doc_token_counts = Counter(doc_tokens)
        
        for query_token in query_tokens:
            # Term frequency in this document
            tf = doc_token_counts.get(query_token, 0)
            
            if tf == 0:
                continue  # Skip if term not in document
            
            # Document frequency: how many stocks contain this token
            df = len(inverted_index.get(query_token, []))
            
            if df == 0:
                continue  # Skip if term not in any document
            
            # IDF: Inverse document frequency with smoothing
            # WHY smoothing: Prevents log(0) and extreme IDF values
            idf = math.log((N - df + 0.5) / (df + 0.5) + 1.0)
            
            # BM25 TF component with saturation and length normalization
            # WHY: Prevents one repeated token from dominating the score
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (
                1 - self.b + self.b * (doc_length / avgdl)
            )
            
            term_score = idf * (numerator / denominator)
            score += term_score
        
        return score


class RealTimeStockRanker:
    """
    High-level interface for real-time stock ranking.
    
    WHY: Orchestrates the full pipeline:
    1. Fetch live stock data
    2. Tokenize snapshots
    3. Tokenize query
    4. Rank with BM25
    5. Return formatted results
    """
    
    def __init__(
        self,
        stock_tokenizer,
        query_tokenizer,
        k1: float = 1.5,
        b: float = 0.75
    ):
        """
        Initialize with tokenizers and BM25 parameters.
        
        Args:
            stock_tokenizer: Instance of StockTokenizer
            query_tokenizer: Instance of QueryTokenizer
            k1: BM25 k1 parameter
            b: BM25 b parameter
        """
        self.stock_tokenizer = stock_tokenizer
        self.query_tokenizer = query_tokenizer
        self.bm25_ranker = StockBM25Ranker(k1=k1, b=b)
    
    def rank_live_stocks(
        self,
        query: str,
        live_stocks: List[Dict[str, Any]],
        top_k: int = 10
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """
        Complete pipeline: query → filter → tokens → BM25 → soft filter → ranked results.
        
        WHY: This is the main entry point for the API.
        Takes raw query and raw stock data, returns ranked results.
        
        ARCHITECTURE:
        1. Tokenize stocks first (needed for filtering)
        2. Apply hard constraint filters from query (sector)
        3. Tokenize query for BM25
        4. Rank filtered stocks with BM25
        5. Apply soft filters (growth direction) to remove contradicting results
        
        Args:
            query: User's natural language query
            live_stocks: List of stock data dicts from database/API
            top_k: Number of results to return
            
        Returns:
            List of (symbol, score, stock_data) tuples, sorted by relevance
        """
        logger.info(f"Ranking query: '{query}' across {len(live_stocks)} stocks")
        
        # STEP 1: Tokenize all stock snapshots FIRST
        # WHY: Filtering needs tokens to match against hard constraints
        tokenized_snapshots = []
        for stock in live_stocks:
            tokens = self.stock_tokenizer.tokenize_stock(stock)
            tokenized_snapshot = {
                **stock,  # Preserve all original data
                'tokens': tokens  # Add tokens
            }
            tokenized_snapshots.append(tokenized_snapshot)
        
        # STEP 2: Apply hard constraint filtering BEFORE BM25
        # WHY: Eliminates stocks that don't meet mandatory requirements
        # Uses raw query string to extract filters (e.g., "tech" → sector_technology)
        filtered_snapshots = query_filter_engine.filter_stocks(query, tokenized_snapshots)
        
        if not filtered_snapshots:
            logger.warning(f"No stocks passed hard filters for query: '{query}'")
            return []
        
        logger.info(f"Filtering: {len(tokenized_snapshots)} → {len(filtered_snapshots)} stocks")
        
        # STEP 3: Convert query to tokens for BM25 ranking
        query_tokens = self.query_tokenizer.tokenize_query(query)
        logger.info(f"Query tokens: {query_tokens}")
        
        if not query_tokens:
            logger.warning("No valid query tokens generated")
            return []
        
        # STEP 4: Rank filtered stocks with BM25
        # WHY: BM25 ranks relevance within the already-filtered set
        results = self.bm25_ranker.rank_stocks(
            query_tokens=query_tokens,
            stock_snapshots=filtered_snapshots,
            top_k=top_k * 3  # Get more results for soft filtering
        )
        
        # STEP 5: Apply soft filters based on user intent
        # WHY: "growing stocks" should NOT return falling stocks
        # This is a post-ranking filter that removes contradicting results
        results = self._apply_soft_filters(query, results)
        
        # Return top_k after soft filtering
        return results[:top_k]
    
    def _apply_soft_filters(
        self,
        query: str,
        results: List[Tuple[str, float, Dict[str, Any]]]
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """
        Apply soft filters based on user intent keywords.
        
        WHY: 
        - Hard filters (sector) determine WHAT category to search
        - Soft filters determine WHICH stocks within that category match intent
        - "tech growing stocks" means: tech sector (hard) + positive growth (soft)
        
        SOFT FILTER RULES:
        - If query contains growth-positive words → exclude stocks with negative change
        - If query contains growth-negative words → exclude stocks with positive change
        - If no growth keywords → return all results (no soft filter)
        
        Args:
            query: Original user query
            results: BM25 ranked results
            
        Returns:
            Filtered results that match user intent
        """
        query_lower = query.lower()
        
        # Define intent keywords (include base forms like 'grow' and verb forms)
        growth_positive_keywords = [
            'grow', 'growing', 'rise', 'rising', 'gain', 'gaining', 
            'bullish', 'up', 'increase', 'increasing',
            'climb', 'climbing', 'surge', 'surging', 'rally', 'rallying', 
            'positive', 'green', 'winners', 'gainers', 'outperforming', 'hot'
        ]
        growth_negative_keywords = [
            'fall', 'falling', 'decline', 'declining', 'drop', 'dropping',
            'bearish', 'down', 'decrease', 'decreasing',
            'sink', 'sinking', 'crash', 'crashing', 'lose', 'losing',
            'negative', 'red', 'losers', 'underperforming', 'cold'
        ]
        
        # Check for growth intent in query using word boundaries
        import re
        wants_positive = any(
            re.search(r'\b' + re.escape(kw) + r'\b', query_lower)
            for kw in growth_positive_keywords
        )
        wants_negative = any(
            re.search(r'\b' + re.escape(kw) + r'\b', query_lower)
            for kw in growth_negative_keywords
        )
        
        # If no growth intent or conflicting intent, return all results
        if not wants_positive and not wants_negative:
            logger.debug("No growth intent detected, returning all results")
            return results
        
        if wants_positive and wants_negative:
            logger.debug("Conflicting growth intent, returning all results")
            return results
        
        # Apply soft filter based on intent
        filtered_results = []
        for symbol, score, stock_data in results:
            change_percent = stock_data.get('change_percent', 0) or 0
            
            if wants_positive and change_percent > 0:
                # User wants growing stocks, this stock is growing
                filtered_results.append((symbol, score, stock_data))
            elif wants_negative and change_percent < 0:
                # User wants falling stocks, this stock is falling
                filtered_results.append((symbol, score, stock_data))
        
        if not filtered_results:
            # If soft filter removes all results, return original
            # (better to show some results than none)
            logger.warning(f"Soft filter removed all results, returning unfiltered")
            return results
        
        logger.info(f"Soft filter: {len(results)} → {len(filtered_results)} (intent: {'positive' if wants_positive else 'negative'})")
        return filtered_results


# For backward compatibility and easy import
def create_ranker(stock_tokenizer, query_tokenizer, k1=1.5, b=0.75):
    """
    Factory function to create a ranker instance.
    
    Args:
        stock_tokenizer: StockTokenizer instance
        query_tokenizer: QueryTokenizer instance
        k1: BM25 k1 parameter (default: 1.5)
        b: BM25 b parameter (default: 0.75)
        
    Returns:
        RealTimeStockRanker instance
    """
    return RealTimeStockRanker(
        stock_tokenizer=stock_tokenizer,
        query_tokenizer=query_tokenizer,
        k1=k1,
        b=b
    )

"""
Query Filter Engine - Explicit Hard Constraint Filtering for Stock Search

DESIGN PRINCIPLES:
1. Filters enforce correctness (AND logic) - BM25 ranks relevance (OR logic)
2. Hard filters are MANDATORY constraints extracted from user intent
3. Extensible architecture - new filter types can be added without refactoring
4. Deterministic mapping - user keywords → internal filter tokens

WHY THIS EXISTS:
- "tech stocks" MUST return only technology sector stocks
- BM25 would rank ANY stock matching ANY token (false positives)
- Filtering BEFORE ranking eliminates irrelevant results completely

ARCHITECTURE:
- Filter extraction: Query string → Structured hard filters
- Filter application: Stock list → Filtered stock list (AND logic)
- BM25 receives only pre-filtered stocks for relevance ranking
"""

import logging
from typing import Dict, List, Any, Set, Optional

logger = logging.getLogger(__name__)


class QueryFilterEngine:
    """
    Extracts and applies hard constraint filters from user queries.
    
    WHY: Separates mandatory constraints from relevance signals.
    This prevents false positives in category-based searches.
    """
    
    def __init__(self):
        """
        Initialize filter engine with keyword mappings.
        
        WHY: Explicit mappings make behavior predictable and debuggable.
        Each mapping defines a filter type that can be extended independently.
        """
        # SECTOR FILTERS (HARD)
        # WHY: Users expect sector searches to be strict
        self.sector_keywords = {
            'tech': 'sector_technology',
            'technology': 'sector_technology',
            'software': 'sector_technology',
            'it': 'sector_technology',
            
            'finance': 'sector_financial_services',
            'financial': 'sector_financial_services',
            'bank': 'sector_financial_services',
            'banking': 'sector_financial_services',
            
            'energy': 'sector_energy',
            'oil': 'sector_energy',
            'gas': 'sector_energy',
            
            'healthcare': 'sector_healthcare',
            'health': 'sector_healthcare',
            'pharma': 'sector_healthcare',
            'pharmaceutical': 'sector_healthcare',
            
            'automotive': 'sector_automotive',
            'auto': 'sector_automotive',
            'car': 'sector_automotive',
            'ev': 'sector_automotive',
            
            'retail': 'sector_consumer_cyclical',
            'consumer': 'sector_consumer_cyclical',
            
            'industrial': 'sector_industrials',
            'manufacturing': 'sector_industrials',
        }
        
        # TOKEN → FILTER TYPE MAPPING
        # WHY: Enables generic filter application logic
        # IMPORTANT: Only sector/industry are HARD constraints
        # Growth, market cap, etc. are SOFT signals for BM25 ranking
        self.filter_type_prefixes = {
            'sector_': 'sector',
            'industry_': 'industry',
            # NOTE: growth_, market_cap_, rsi_, etc. should be ranking signals,
            # not hard filters. They're handled by BM25, not by this filter engine.
        }
    
    def extract_hard_filters(self, query: str) -> Dict[str, str]:
        """
        Extract hard constraint filters from raw user query.
        
        WHY: Converts natural language to structured, enforceable filters.
        Hard filters represent mandatory requirements that MUST be satisfied.
        
        PHILOSOPHY: Only category membership should be hard filters
        - Sector/Industry: Binary membership (stock IS or ISN'T in tech)
        - Growth/Price/Volume: Performance metrics → BM25 ranking signals
        
        Args:
            query: Raw user query string (e.g., "tech stocks")
            
        Returns:
            Dictionary of filter_type → filter_token
            Example: {'sector': 'sector_technology'}
            
        EXTENSION POINT: Add new filter types by:
        1. Adding keyword mapping dictionary
        2. Adding extraction logic in this function
        3. Filter application automatically handles new types
        """
        query_lower = query.lower().strip()
        hard_filters = {}
        
        # EXTRACT SECTOR FILTER ONLY
        # WHY: Sector is the ONLY mandatory constraint
        # Growth, market cap, volume, etc. are ranking signals, NOT filters
        # Use word boundaries to avoid false matches (e.g., "momentum" shouldn't match "tech")
        import re
        for keyword, sector_token in self.sector_keywords.items():
            # Match keyword as a whole word only
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, query_lower):
                hard_filters['sector'] = sector_token
                logger.info(f"Extracted sector filter: {sector_token} (from keyword: '{keyword}')")
                break  # Only one sector per query
        
        if hard_filters:
            logger.info(f"Hard filters extracted from '{query}': {hard_filters}")
        else:
            logger.debug(f"No hard filters found in query: '{query}'")
        
        return hard_filters
    
    def apply_filters(
        self,
        stocks: List[Dict[str, Any]],
        hard_filters: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """
        Apply hard filters to stock list using AND logic.
        
        WHY: Enforces ALL constraints simultaneously.
        A stock passes ONLY IF it satisfies EVERY hard filter.
        
        Args:
            stocks: List of stock snapshots with 'tokens' field
            hard_filters: Dictionary of filter_type → filter_token
            
        Returns:
            Filtered list of stocks satisfying ALL constraints
            
        LOGIC:
        - If hard_filters is empty → return all stocks (no constraints)
        - If hard_filters has N entries → stock must match ALL N
        
        Example:
            hard_filters = {'sector': 'sector_tech', 'growth': 'growth_positive'}
            
            Stock A: ['sector_tech', 'growth_positive', 'price_up']
            → PASS ✅ (has both required tokens)
            
            Stock B: ['sector_tech', 'price_down']
            → FAIL ❌ (missing growth_positive)
            
            Stock C: ['sector_energy', 'growth_positive']
            → FAIL ❌ (wrong sector)
        """
        # No filters → all stocks pass
        if not hard_filters:
            logger.debug("No hard filters to apply")
            return stocks
        
        # Convert filter dict to set of required tokens
        # WHY: Set operations enable efficient AND logic checking
        required_tokens = set(hard_filters.values())
        
        logger.info(f"Applying hard filters (AND logic): {required_tokens}")
        
        filtered_stocks = []
        
        for stock in stocks:
            stock_tokens = set(stock.get('tokens', []))
            
            # Check if stock contains ALL required tokens (AND logic)
            if required_tokens.issubset(stock_tokens):
                filtered_stocks.append(stock)
        
        logger.info(
            f"Filter results: {len(stocks)} stocks → {len(filtered_stocks)} stocks "
            f"(filtered out {len(stocks) - len(filtered_stocks)})"
        )
        
        return filtered_stocks
    
    def filter_stocks(
        self,
        query: str,
        stocks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Complete filtering pipeline: query → filters → filtered stocks.
        
        WHY: Single entry point for integration into search pipeline.
        Encapsulates both extraction and application.
        
        Args:
            query: Raw user query string
            stocks: List of tokenized stock snapshots
            
        Returns:
            Filtered list of stocks satisfying hard constraints
            
        INTEGRATION:
        This is the primary function to call from the BM25 ranker:
        
        ```python
        # In BM25 ranking pipeline:
        filtered_stocks = filter_engine.filter_stocks(query, all_stocks)
        ranked_results = bm25_ranker.rank(query_tokens, filtered_stocks)
        ```
        """
        hard_filters = self.extract_hard_filters(query)
        return self.apply_filters(stocks, hard_filters)
    
    def get_filter_tokens_from_query(self, query: str) -> Set[str]:
        """
        Get the actual filter tokens that would be applied (for debugging).
        
        WHY: Useful for testing, logging, and explaining results to users.
        
        Args:
            query: Raw user query string
            
        Returns:
            Set of filter tokens that will be enforced
        """
        hard_filters = self.extract_hard_filters(query)
        return set(hard_filters.values())
    
    def classify_token(self, token: str) -> str:
        """
        Classify a token as 'hard', 'soft', or 'unknown'.
        
        WHY: Enables separation of constraints from ranking signals.
        Hard tokens → filtering (AND logic)
        Soft tokens → BM25 ranking (OR logic)
        
        Args:
            token: A single token from query or stock
            
        Returns:
            'hard' if token is a filter constraint
            'soft' if token is a ranking signal
            'unknown' if token doesn't match known patterns
            
        EXTENSION POINT: Add new prefixes to filter_type_prefixes
        """
        for prefix in self.filter_type_prefixes.keys():
            if token.startswith(prefix):
                return 'hard'
        
        # All other tokens are soft ranking signals
        # Examples: price_up, volume_high, rsi_overbought (when not filtered)
        return 'soft'
    
    def validate_stock_tokens(self, stock: Dict[str, Any]) -> bool:
        """
        Validate that a stock has required token structure.
        
        WHY: Defensive programming - ensures stock data is in expected format.
        
        Args:
            stock: Stock snapshot dictionary
            
        Returns:
            True if stock has valid 'tokens' field, False otherwise
        """
        if 'tokens' not in stock:
            logger.warning(f"Stock missing 'tokens' field: {stock.get('symbol', 'UNKNOWN')}")
            return False
        
        if not isinstance(stock['tokens'], list):
            logger.warning(f"Stock 'tokens' is not a list: {stock.get('symbol', 'UNKNOWN')}")
            return False
        
        return True


# EXTENSION GUIDE:
# ================
# To add a new filter type (e.g., RSI filters):
#
# 1. Add keyword mapping:
#    self.rsi_keywords = {
#        'overbought': 'rsi_overbought',
#        'oversold': 'rsi_oversold',
#    }
#
# 2. Add to filter_type_prefixes:
#    'rsi_': 'rsi'
#
# 3. Add extraction logic in extract_hard_filters():
#    for keyword, rsi_token in self.rsi_keywords.items():
#        if keyword in query_lower:
#            hard_filters['rsi'] = rsi_token
#            break
#
# 4. No changes needed in apply_filters() - it handles all filter types generically
#
# 5. Ensure StockTokenizer generates matching tokens (e.g., rsi_overbought)


# Global instance for easy import
query_filter_engine = QueryFilterEngine()

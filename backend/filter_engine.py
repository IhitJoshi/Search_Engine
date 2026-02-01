"""
Stock Filter Engine - Enforces Hard Constraints Before BM25 Ranking

WHY THIS MODULE EXISTS:
- BM25 uses OR logic - ranks stocks matching ANY query token
- Category/sector tokens must be MANDATORY (AND logic)
- Without filtering, "tech stocks" returns ALL stocks that happen to match other tokens

DESIGN PRINCIPLE:
- HARD tokens = mandatory constraints (sector, industry)
- SOFT tokens = ranking signals (price_up, volume_high, etc.)
- Filter BEFORE ranking to eliminate false positives

Example:
Query: "tech growing stocks"
Tokens: ["sector_technology", "price_up", "rising"]

Without filtering:
- Energy stock with price_up matches → WRONG ❌

With filtering:
- Only tech stocks pass filter
- Then BM25 ranks by price_up/rising → CORRECT ✅
"""

import logging
from typing import List, Dict, Any, Set

logger = logging.getLogger(__name__)


class StockFilter:
    """
    Filters stock snapshots based on hard constraint tokens.
    
    WHY: Ensures category/sector membership before BM25 ranking.
    BM25 should rank within the filtered set, not determine membership.
    """
    
    def __init__(self):
        """
        Initialize filter with hard token patterns.
        
        WHY: Hard tokens represent mandatory constraints.
        If query contains sector_tech, ONLY tech stocks should be considered.
        """
        # Token prefixes that represent hard constraints
        self.hard_token_prefixes = {
            'sector_',      # sector_technology, sector_financial_services, etc.
            'industry_',    # For future industry-level filtering
        }
    
    def extract_hard_tokens(self, query_tokens: List[str]) -> Set[str]:
        """
        Extract hard constraint tokens from query tokens.
        
        WHY: Separates mandatory filters from ranking signals.
        
        Args:
            query_tokens: All tokens from query (hard + soft mixed)
            
        Returns:
            Set of hard tokens that must ALL be present in eligible stocks
            
        Example:
            Input: ["sector_technology", "price_up", "volume_high"]
            Output: {"sector_technology"}
        """
        hard_tokens = set()
        
        for token in query_tokens:
            # Check if token starts with any hard constraint prefix
            for prefix in self.hard_token_prefixes:
                if token.startswith(prefix):
                    hard_tokens.add(token)
                    break
        
        if hard_tokens:
            logger.info(f"Extracted hard tokens: {hard_tokens}")
        else:
            logger.debug("No hard tokens found in query")
        
        return hard_tokens
    
    def filter_stocks(
        self,
        stock_snapshots: List[Dict[str, Any]],
        hard_tokens: Set[str]
    ) -> List[Dict[str, Any]]:
        """
        Filter stocks to only those containing ALL hard tokens.
        
        WHY: Enforces AND logic for mandatory constraints.
        A stock is eligible ONLY IF it contains EVERY hard token.
        
        Args:
            stock_snapshots: List of tokenized stock snapshots
            hard_tokens: Set of hard constraint tokens (from extract_hard_tokens)
            
        Returns:
            Filtered list of stocks that satisfy ALL hard constraints
            
        Logic:
            - If no hard tokens: return all stocks (no filtering needed)
            - If hard tokens exist: return only stocks containing ALL of them
            
        Example:
            hard_tokens = {"sector_technology"}
            
            Stock A tokens: ["sector_technology", "price_up"]
            → PASS ✅
            
            Stock B tokens: ["sector_energy", "price_up"]
            → FAIL ❌ (wrong sector)
            
            Stock C tokens: ["price_up", "volume_high"]
            → FAIL ❌ (no sector info)
        """
        # If no hard constraints, return all stocks
        if not hard_tokens:
            logger.debug("No hard tokens - skipping filter")
            return stock_snapshots
        
        # Filter stocks using AND logic
        filtered_stocks = []
        
        for stock in stock_snapshots:
            stock_tokens = set(stock.get('tokens', []))
            
            # Check if stock contains ALL hard tokens (AND logic)
            if hard_tokens.issubset(stock_tokens):
                filtered_stocks.append(stock)
        
        logger.info(
            f"Filtered {len(stock_snapshots)} stocks → {len(filtered_stocks)} "
            f"matching hard constraints {hard_tokens}"
        )
        
        return filtered_stocks
    
    def apply_filter(
        self,
        query_tokens: List[str],
        stock_snapshots: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Complete filtering pipeline: extract hard tokens → filter stocks.
        
        WHY: Single function for easy integration into ranking pipeline.
        
        Args:
            query_tokens: Tokens from user query
            stock_snapshots: Tokenized stock snapshots
            
        Returns:
            Filtered stocks that satisfy all hard constraints
        """
        hard_tokens = self.extract_hard_tokens(query_tokens)
        return self.filter_stocks(stock_snapshots, hard_tokens)


# Global instance for easy import
stock_filter = StockFilter()

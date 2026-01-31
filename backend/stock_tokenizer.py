"""
Stock Tokenizer - Converts real-time stock snapshots into symbolic tokens

CORE CONCEPT:
- A stock snapshot is NOT text - it's numerical market data
- We convert market signals (price change, volume, RSI, etc.) into TOKENS
- These tokens become the "document" that BM25 operates on
- This allows intent-based search (e.g., "high volume rising stocks")

Example:
  Input: {price_change: +2.1%, volume_change: +180%, rsi: 72}
  Output: ["price_up", "volume_high", "rsi_overbought", "sector_Technology"]
"""

import logging
from typing import Dict, List, Any, Optional
import math

logger = logging.getLogger(__name__)


class StockTokenizer:
    """
    Converts stock market data snapshots into symbolic tokens.
    These tokens represent market signals and are used for BM25 ranking.
    """
    
    def __init__(self):
        """
        Initialize tokenizer with configurable thresholds.
        These can be tuned based on market conditions.
        """
        # Price change thresholds (in percentage)
        self.price_up_threshold = 0.5
        self.price_down_threshold = -0.5
        self.price_strong_up = 2.0
        self.price_strong_down = -2.0
        
        # Volume change thresholds (percentage vs average)
        self.volume_high_threshold = 50
        self.volume_very_high_threshold = 100
        self.volume_low_threshold = -30
        
        # RSI thresholds (if available)
        self.rsi_overbought = 70
        self.rsi_oversold = 30
        
        # Market cap thresholds (in billions)
        self.large_cap = 200
        self.mid_cap = 10
        
    def tokenize_stock(self, stock_data: Dict[str, Any]) -> List[str]:
        """
        Convert a stock snapshot into a list of symbolic tokens.
        
        WHY: Each token represents a market signal or characteristic.
        These tokens form the "document" that BM25 scores against queries.
        
        Args:
            stock_data: Dictionary containing stock metrics
            
        Returns:
            List of token strings representing the stock's state
        """
        tokens = []
        
        # 1. PRICE MOVEMENT TOKENS
        # WHY: Users search for "rising stocks" or "falling stocks"
        change_percent = self._safe_float(stock_data.get('change_percent'))
        if change_percent is not None:
            if change_percent >= self.price_strong_up:
                tokens.extend(['price_up', 'price_strong_up', 'rising', 'bullish'])
            elif change_percent >= self.price_up_threshold:
                tokens.extend(['price_up', 'rising'])
            elif change_percent <= self.price_strong_down:
                tokens.extend(['price_down', 'price_strong_down', 'falling', 'bearish'])
            elif change_percent <= self.price_down_threshold:
                tokens.extend(['price_down', 'falling'])
            else:
                tokens.append('price_stable')
        
        # 2. VOLUME TOKENS
        # WHY: High volume indicates strong interest/activity
        volume = self._safe_float(stock_data.get('volume'))
        avg_volume = self._safe_float(stock_data.get('average_volume'))
        
        if volume is not None and avg_volume is not None and avg_volume > 0:
            volume_change_pct = ((volume - avg_volume) / avg_volume) * 100
            
            if volume_change_pct >= self.volume_very_high_threshold:
                tokens.extend(['volume_high', 'volume_very_high', 'high_activity'])
            elif volume_change_pct >= self.volume_high_threshold:
                tokens.extend(['volume_high', 'active'])
            elif volume_change_pct <= self.volume_low_threshold:
                tokens.extend(['volume_low', 'low_activity'])
        elif volume is not None:
            # Fallback if we don't have average volume
            if volume > 1000000:
                tokens.append('volume_high')
            elif volume < 100000:
                tokens.append('volume_low')
        
        # 3. SECTOR TOKENS
        # WHY: Users filter by sector (e.g., "tech stocks")
        sector = stock_data.get('sector', '').strip()
        if sector and sector != 'Unknown':
            # Normalize sector name and create token
            sector_token = f"sector_{sector.replace(' ', '_').lower()}"
            tokens.append(sector_token)
            # Also add the plain sector name for broader matching
            tokens.append(sector.lower())
        
        # 4. MARKET CAP TOKENS
        # WHY: Users search for "large cap" or "small cap" stocks
        market_cap = self._safe_float(stock_data.get('market_cap'))
        if market_cap is not None:
            market_cap_billions = market_cap / 1_000_000_000
            
            if market_cap_billions >= self.large_cap:
                tokens.extend(['large_cap', 'mega_cap', 'blue_chip'])
            elif market_cap_billions >= self.mid_cap:
                tokens.append('mid_cap')
            else:
                tokens.append('small_cap')
        
        # 5. PRICE LEVEL TOKENS
        # WHY: Users may search for "cheap stocks" or "expensive stocks"
        price = self._safe_float(stock_data.get('price'))
        if price is not None:
            if price < 10:
                tokens.append('low_price')
            elif price > 500:
                tokens.append('high_price')
        
        # 6. SYMBOL AND NAME TOKENS
        # WHY: Direct search by company name or ticker
        symbol = stock_data.get('symbol', '').strip().upper()
        if symbol:
            tokens.append(symbol.lower())
        
        company_name = stock_data.get('company_name', '').strip()
        if company_name:
            # Tokenize company name into words
            name_tokens = company_name.lower().replace(',', '').replace('.', '').split()
            # Filter out common words
            filtered_name_tokens = [
                t for t in name_tokens 
                if t not in {'inc', 'corp', 'corporation', 'company', 'co', 'ltd', 'limited', 'the'}
            ]
            tokens.extend(filtered_name_tokens)
        
        # 7. MOMENTUM INDICATORS (if available)
        # WHY: Technical traders search for momentum
        rsi = self._safe_float(stock_data.get('rsi'))
        if rsi is not None:
            if rsi >= self.rsi_overbought:
                tokens.extend(['rsi_overbought', 'overbought'])
            elif rsi <= self.rsi_oversold:
                tokens.extend(['rsi_oversold', 'oversold'])
        
        # 8. MOVING AVERAGES (if available)
        # WHY: Crossovers are key signals
        if stock_data.get('above_50_ma'):
            tokens.extend(['above_50ma', 'uptrend'])
        if stock_data.get('above_200_ma'):
            tokens.extend(['above_200ma', 'long_uptrend'])
        if stock_data.get('below_50_ma'):
            tokens.extend(['below_50ma', 'downtrend'])
        
        # 9. VOLATILITY TOKENS (if available)
        beta = self._safe_float(stock_data.get('beta'))
        if beta is not None:
            if beta > 1.5:
                tokens.extend(['high_volatility', 'volatile'])
            elif beta < 0.5:
                tokens.extend(['low_volatility', 'stable'])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_tokens = []
        for token in tokens:
            if token not in seen:
                seen.add(token)
                unique_tokens.append(token)
        
        logger.debug(f"Tokenized {symbol}: {len(unique_tokens)} tokens")
        return unique_tokens
    
    def _safe_float(self, value: Any) -> Optional[float]:
        """
        Safely convert value to float, handling None and invalid types.
        WHY: Market data can have missing values or unexpected types.
        """
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None


class QueryTokenizer:
    """
    Maps user natural language queries to the same token space as stocks.
    
    WHY: For BM25 to work, query tokens must match stock tokens.
    This is NOT semantic search - it's deterministic keyword mapping.
    """
    
    def __init__(self):
        """
        Initialize with keyword-to-token mappings.
        These mappings define what users can search for.
        """
        # Maps natural language phrases to stock tokens
        self.keyword_map = {
            # Price movement
            'rising': ['price_up', 'rising', 'bullish'],
            'falling': ['price_down', 'falling', 'bearish'],
            'up': ['price_up', 'rising'],
            'down': ['price_down', 'falling'],
            'gain': ['price_up', 'rising'],
            'loss': ['price_down', 'falling'],
            'surge': ['price_strong_up', 'bullish'],
            'drop': ['price_strong_down', 'bearish'],
            'bullish': ['price_up', 'bullish', 'rising'],
            'bearish': ['price_down', 'bearish', 'falling'],
            'stable': ['price_stable'],
            'flat': ['price_stable'],
            
            # Volume
            'volume': ['volume_high', 'active'],
            'high volume': ['volume_high', 'volume_very_high'],
            'active': ['volume_high', 'active', 'high_activity'],
            'liquid': ['volume_high', 'active'],
            'popular': ['volume_high', 'active'],
            
            # Market cap
            'large cap': ['large_cap', 'blue_chip'],
            'big': ['large_cap', 'mega_cap'],
            'blue chip': ['large_cap', 'blue_chip'],
            'mid cap': ['mid_cap'],
            'small cap': ['small_cap'],
            'penny': ['small_cap', 'low_price'],
            
            # Sectors (normalize to match tokenizer output)
            'tech': ['sector_technology', 'technology'],
            'technology': ['sector_technology', 'technology'],
            'finance': ['sector_financial_services', 'financial'],
            'financial': ['sector_financial_services', 'financial'],
            'bank': ['sector_financial_services', 'financial'],
            'healthcare': ['sector_healthcare', 'healthcare'],
            'health': ['sector_healthcare', 'healthcare'],
            'pharma': ['sector_healthcare', 'healthcare'],
            'energy': ['sector_energy', 'energy'],
            'oil': ['sector_energy', 'energy'],
            'automotive': ['sector_automotive', 'automotive'],
            'auto': ['sector_automotive', 'automotive'],
            'car': ['sector_automotive', 'automotive'],
            'ev': ['sector_automotive', 'automotive'],
            
            # Technical indicators
            'overbought': ['rsi_overbought', 'overbought'],
            'oversold': ['rsi_oversold', 'oversold'],
            'uptrend': ['above_50ma', 'uptrend', 'rising'],
            'downtrend': ['below_50ma', 'downtrend', 'falling'],
            'volatile': ['high_volatility', 'volatile'],
            'momentum': ['price_strong_up', 'volume_high'],
            
            # Price levels
            'cheap': ['low_price', 'small_cap'],
            'expensive': ['high_price', 'large_cap'],
            'affordable': ['low_price'],
        }
    
    def tokenize_query(self, query: str) -> List[str]:
        """
        Convert user query to stock token space.
        
        WHY: User asks "rising tech stocks" → tokens: ['price_up', 'sector_technology']
        These tokens match what stockTokenizer generates.
        
        Args:
            query: Natural language search query
            
        Returns:
            List of tokens that match stock token space
        """
        query_lower = query.lower().strip()
        tokens = []
        
        # First, try to match multi-word phrases
        for phrase, phrase_tokens in self.keyword_map.items():
            if phrase in query_lower:
                tokens.extend(phrase_tokens)
        
        # Then tokenize individual words
        words = query_lower.split()
        for word in words:
            # Direct match
            if word in self.keyword_map:
                tokens.extend(self.keyword_map[word])
            else:
                # Include the word as-is for company name matching
                # Filter out common stopwords
                if word not in {'the', 'a', 'an', 'and', 'or', 'with', 'in', 'of', 'for', 'to', 'stocks', 'stock', 'shares'}:
                    tokens.append(word)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_tokens = []
        for token in tokens:
            if token not in seen:
                seen.add(token)
                unique_tokens.append(token)
        
        logger.debug(f"Query '{query}' → tokens: {unique_tokens}")
        return unique_tokens


# Global instances for easy import
stock_tokenizer = StockTokenizer()
query_tokenizer = QueryTokenizer()

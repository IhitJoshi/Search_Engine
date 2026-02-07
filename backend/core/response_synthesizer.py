"""
Response Synthesizer - Transforms ranked stock results into structured API responses

CORE RESPONSIBILITY:
- Convert BM25-ranked stock data into JSON-ready, human-readable responses
- Map matched tokens to explanations using static mappings
- NO data fetching, NO ranking logic, NO predictions
- Pure transformation layer

INPUT: Ranked stock results from BM25 ranker
OUTPUT: Structured JSON response with metadata, results, and human-readable reasons
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


# STATIC TOKEN → EXPLANATION MAPPING
# WHY: Provides deterministic, factual explanations for matched tokens
# NO predictions, NO advice, just factual signal descriptions
TOKEN_EXPLANATIONS = {
    # Price movement signals
    'price_up': 'Price is rising',
    'price_down': 'Price is falling',
    'price_strong_up': 'Strong upward price movement',
    'price_strong_down': 'Strong downward price movement',
    'price_stable': 'Price is stable',
    'rising': 'Upward price trend detected',
    'falling': 'Downward price trend detected',
    'bullish': 'Bullish price action',
    'bearish': 'Bearish price action',
    
    # Volume signals
    'volume_high': 'High trading volume',
    'volume_very_high': 'Unusually high trading volume',
    'volume_low': 'Low trading volume',
    'active': 'Active trading activity',
    'low_activity': 'Low trading activity',
    'high_activity': 'High trading activity',
    
    # Market cap signals
    'large_cap': 'Large market capitalization',
    'mid_cap': 'Mid market capitalization',
    'small_cap': 'Small market capitalization',
    'mega_cap': 'Mega cap company',
    'blue_chip': 'Blue chip stock',
    
    # Sector matches (dynamic - will be generated)
    'sector_technology': 'Technology sector',
    'sector_financial_services': 'Financial services sector',
    'sector_healthcare': 'Healthcare sector',
    'sector_energy': 'Energy sector',
    'sector_automotive': 'Automotive sector',
    
    # Technical indicators
    'rsi_overbought': 'RSI indicates overbought conditions',
    'rsi_oversold': 'RSI indicates oversold conditions',
    'overbought': 'Overbought conditions detected',
    'oversold': 'Oversold conditions detected',
    'above_50ma': 'Price above 50-day moving average',
    'above_200ma': 'Price above 200-day moving average',
    'below_50ma': 'Price below 50-day moving average',
    'uptrend': 'In uptrend',
    'downtrend': 'In downtrend',
    'high_volatility': 'High volatility',
    'low_volatility': 'Low volatility',
    'volatile': 'Volatile price action',
    'stable': 'Stable price action',
    
    # Price level signals
    'low_price': 'Low price level',
    'high_price': 'High price level',
    
    # Generic sector/category matches
    'technology': 'Technology company',
    'financial': 'Financial company',
    'healthcare': 'Healthcare company',
    'energy': 'Energy company',
    'automotive': 'Automotive company',
}


class ResponseSynthesizer:
    """
    Pure transformation layer that converts ranked stock results
    into structured, human-readable API responses.
    
    WHY: Separates response formatting from ranking logic
    ENSURES: Deterministic, testable, maintainable code
    """
    
    def __init__(self, token_explanations: Optional[Dict[str, str]] = None):
        """
        Initialize with token explanation mappings.
        
        Args:
            token_explanations: Custom token → explanation map (optional)
                               Defaults to TOKEN_EXPLANATIONS
        """
        self.token_explanations = token_explanations or TOKEN_EXPLANATIONS
    
    def synthesize_response(
        self,
        query: str,
        ranked_results: List[Dict[str, Any]],
        ranking_method: str = 'bm25',
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Transform ranked stock results into structured API response.
        
        WHY: This is the main entry point for response synthesis.
        Takes raw ranked data and produces frontend-ready JSON.
        
        Args:
            query: Original user query
            ranked_results: List of ranked stocks from BM25 ranker
                Each item should contain:
                - symbol: Stock ticker
                - score: BM25 relevance score
                - tokens: List of matched tokens (optional)
                - Other stock data (price, volume, etc.)
            ranking_method: Algorithm used (e.g., 'bm25')
            metadata: Additional metadata (optional)
            
        Returns:
            Structured response with three parts:
            1. Query metadata
            2. Ranked results with human-readable reasons
            3. Performance/debug info (if enabled)
        """
        timestamp = datetime.utcnow().isoformat() + 'Z'
        
        # PART 1: Query Metadata
        # WHY: Frontend needs context about the search
        response_metadata = {
            'query': query,
            'timestamp': timestamp,
            'total_results': len(ranked_results),
            'ranking_method': ranking_method
        }
        
        # Add custom metadata if provided
        if metadata:
            response_metadata.update(metadata)
        
        # PART 2: Process each ranked result
        # WHY: Convert raw data + tokens into human-readable format
        processed_results = []
        
        for rank, result in enumerate(ranked_results, start=1):
            processed_result = self._process_single_result(
                result=result,
                rank=rank
            )
            processed_results.append(processed_result)
        
        # PART 3: Assemble final response
        response = {
            'metadata': response_metadata,
            'results': processed_results
        }
        
        logger.info(f"Synthesized response for query '{query}': {len(processed_results)} results")
        
        return response
    
    def _process_single_result(
        self,
        result: Dict[str, Any],
        rank: int
    ) -> Dict[str, Any]:
        """
        Process a single ranked stock result.
        
        WHY: Extracts matched tokens and generates human-readable reasons.
        Separates concerns: token matching vs. explanation generation.
        
        Args:
            result: Single stock result from ranker
            rank: Position in ranked list
            
        Returns:
            Processed result with:
            - Basic stock info
            - Rank and score
            - Human-readable reasons
            - Current metrics snapshot
        """
        # Extract matched tokens (if available)
        matched_tokens = result.get('tokens', [])
        
        # Generate human-readable reasons from matched tokens
        # WHY: Users need to understand WHY this stock was ranked here
        reasons = self._generate_reasons(matched_tokens)
        
        # Build processed result
        # WHY: Clean structure for frontend consumption
        processed = {
            # Stock identification
            'symbol': result.get('symbol'),
            'company_name': result.get('company_name'),
            'sector': result.get('sector'),
            
            # Ranking info
            'rank': rank,
            'score': round(result.get('_score', result.get('score', 0.0)), 4),
            
            # Human-readable explanations
            # WHY: Frontend displays these to users
            'reasons': reasons,
            
            # Current metrics snapshot
            # WHY: Frontend needs these for charts and display
            'metrics': {
                'price': result.get('price'),
                'volume': result.get('volume'),
                'average_volume': result.get('average_volume'),
                'market_cap': result.get('market_cap'),
                'change_percent': result.get('change_percent'),
                'last_updated': result.get('last_updated')
            },
            
            # Optional: Brief summary (if available)
            'summary': result.get('summary', '')[:200] if result.get('summary') else None
        }
        
        return processed
    
    def _generate_reasons(self, matched_tokens: List[str]) -> List[str]:
        """
        Generate human-readable reasons from matched tokens.
        
        WHY: Converts symbolic tokens into explanations users can understand.
        Uses static mapping - NO generative AI, NO hallucination.
        
        Args:
            matched_tokens: List of token strings that matched the query
            
        Returns:
            List of human-readable explanation strings
        """
        reasons = []
        seen_explanations = set()  # Deduplicate similar explanations
        
        for token in matched_tokens:
            # Look up explanation in static map
            explanation = self._get_token_explanation(token)
            
            if explanation and explanation not in seen_explanations:
                reasons.append(explanation)
                seen_explanations.add(explanation)
        
        # Sort for consistent ordering
        # WHY: Deterministic output for same input
        reasons.sort()
        
        return reasons
    
    def _get_token_explanation(self, token: str) -> Optional[str]:
        """
        Get human-readable explanation for a token.
        
        WHY: Handles exact matches and pattern-based matches
        (e.g., sector_* tokens, company names)
        
        Args:
            token: Single token string
            
        Returns:
            Human-readable explanation or None
        """
        # Direct lookup
        if token in self.token_explanations:
            return self.token_explanations[token]
        
        # Pattern matching for dynamic tokens
        # WHY: Some tokens follow patterns (e.g., sector_XXX)
        
        # Sector tokens: sector_XXX → "XXX sector"
        if token.startswith('sector_'):
            sector_name = token.replace('sector_', '').replace('_', ' ').title()
            return f"{sector_name} sector"
        
        # Company name tokens: just capitalize
        # WHY: Company names used as tokens should be recognizable
        if len(token) > 2 and token.isalpha() and token.isupper():
            # Likely a ticker symbol, don't explain
            return None
        
        # Otherwise, no explanation available
        return None
    
    def add_token_explanation(self, token: str, explanation: str):
        """
        Add or update a token explanation.
        
        WHY: Allows runtime customization of explanations
        without modifying the static map.
        
        Args:
            token: Token string
            explanation: Human-readable explanation
        """
        self.token_explanations[token] = explanation
        logger.debug(f"Added explanation for token '{token}': {explanation}")


def create_synthesizer(custom_explanations: Optional[Dict[str, str]] = None) -> ResponseSynthesizer:
    """
    Factory function to create a ResponseSynthesizer instance.
    
    WHY: Provides clean initialization and optional customization.
    
    Args:
        custom_explanations: Optional custom token explanations
                            to extend or override defaults
        
    Returns:
        ResponseSynthesizer instance
    """
    explanations = TOKEN_EXPLANATIONS.copy()
    if custom_explanations:
        explanations.update(custom_explanations)
    
    return ResponseSynthesizer(token_explanations=explanations)


# Global instance for easy import
# WHY: Most use cases don't need customization
response_synthesizer = ResponseSynthesizer()


def synthesize_search_response(
    query: str,
    ranked_results: List[Dict[str, Any]],
    ranking_method: str = 'bm25'
) -> Dict[str, Any]:
    """
    Convenience function for quick response synthesis.
    
    WHY: Provides a simple functional interface without
    needing to instantiate the class.
    
    Args:
        query: Original user query
        ranked_results: Ranked stock results from BM25
        ranking_method: Algorithm used
        
    Returns:
        Structured JSON-ready response
    """
    return response_synthesizer.synthesize_response(
        query=query,
        ranked_results=ranked_results,
        ranking_method=ranking_method
    )

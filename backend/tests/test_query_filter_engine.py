"""
Comprehensive Test Suite for Query Filter Engine

Tests the production-quality filtering system that enforces
hard constraints before BM25 ranking.

DESIGN PHILOSOPHY:
- Only CATEGORY MEMBERSHIP should be hard filters (sector, industry)
- PERFORMANCE METRICS (growth, price, volume) are BM25 ranking signals
- This prevents over-filtering (0 results) when combining constraints
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from query_filter_engine import query_filter_engine


def test_sector_filter_extraction():
    """Test sector filter extraction from various queries"""
    print("\n=== TEST 1: Sector Filter Extraction ===")
    
    test_cases = [
        ("tech stocks", {'sector': 'sector_technology'}),
        ("technology companies", {'sector': 'sector_technology'}),
        ("bank stocks", {'sector': 'sector_financial_services'}),
        ("finance sector", {'sector': 'sector_financial_services'}),
        ("energy stocks", {'sector': 'sector_energy'}),
        ("healthcare stocks", {'sector': 'sector_healthcare'}),
        ("automotive stocks", {'sector': 'sector_automotive'}),
        ("high volume stocks", {}),  # No sector keyword
    ]
    
    for query, expected in test_cases:
        result = query_filter_engine.extract_hard_filters(query)
        print(f"Query: '{query}'")
        print(f"  Expected: {expected}")
        print(f"  Got: {result}")
        assert result == expected, f"Mismatch for query: {query}"
        print("  ✅ PASS\n")
    
    print("✅ All sector filter extraction tests passed\n")


def test_growth_not_hard_filter():
    """
    Test that growth keywords do NOT create hard filters.
    
    WHY: Growth is a performance metric, not a category.
    Using growth as a hard filter causes over-filtering (0 results)
    when combined with sector filters.
    """
    print("\n=== TEST 2: Growth Keywords Are NOT Hard Filters ===")
    
    test_cases = [
        ("growing stocks", {}),  # No hard filter - growth is for BM25
        ("rising stocks", {}),
        ("stocks going up", {}),
        ("bullish stocks", {}),
        ("falling stocks", {}),
        ("declining stocks", {}),
        ("stocks going down", {}),
        ("bearish stocks", {}),
    ]
    
    for query, expected in test_cases:
        result = query_filter_engine.extract_hard_filters(query)
        print(f"Query: '{query}'")
        print(f"  Expected: {expected}")
        print(f"  Got: {result}")
        assert result == expected, f"Growth should NOT be a hard filter for: {query}"
        print("  ✅ PASS (growth is NOT a hard filter)\n")
    
    print("✅ Growth keywords correctly NOT extracted as hard filters\n")


def test_market_cap_not_hard_filter():
    """
    Test that market cap keywords do NOT create hard filters.
    
    WHY: Market cap is a metric that should influence ranking,
    not exclude stocks entirely.
    """
    print("\n=== TEST 3: Market Cap Keywords Are NOT Hard Filters ===")
    
    test_cases = [
        ("large cap stocks", {}),  # No hard filter - market cap is for BM25
        ("blue chip stocks", {}),
        ("mid cap stocks", {}),
        ("small cap stocks", {}),
        ("penny stocks", {}),
    ]
    
    for query, expected in test_cases:
        result = query_filter_engine.extract_hard_filters(query)
        print(f"Query: '{query}'")
        print(f"  Expected: {expected}")
        print(f"  Got: {result}")
        assert result == expected, f"Market cap should NOT be a hard filter for: {query}"
        print("  ✅ PASS (market cap is NOT a hard filter)\n")
    
    print("✅ Market cap keywords correctly NOT extracted as hard filters\n")


def test_combined_queries_only_extract_sector():
    """
    Test that combined queries only extract sector as hard filter.
    
    CRITICAL FIX: "tech growing stocks" should return ALL tech stocks,
    with "growing" used as a BM25 ranking signal (not a filter).
    """
    print("\n=== TEST 4: Combined Queries Only Extract Sector ===")
    
    test_cases = [
        # THE BUG FIX: "tech growing stocks" was returning 0 results
        # because growth_positive was a hard filter and no stocks had it
        ("tech growing stocks", {'sector': 'sector_technology'}),
        ("growing tech stocks", {'sector': 'sector_technology'}),
        ("large cap bank stocks", {'sector': 'sector_financial_services'}),
        ("rising energy stocks", {'sector': 'sector_energy'}),
        ("bullish healthcare companies", {'sector': 'sector_healthcare'}),
        ("small cap tech", {'sector': 'sector_technology'}),
    ]
    
    for query, expected in test_cases:
        result = query_filter_engine.extract_hard_filters(query)
        print(f"Query: '{query}'")
        print(f"  Expected: {expected}")
        print(f"  Got: {result}")
        assert result == expected, f"Only sector should be hard filter for: {query}"
        print("  ✅ PASS\n")
    
    print("✅ Combined queries correctly extract only sector as hard filter\n")


def test_filter_application():
    """Test that filters correctly include/exclude stocks"""
    print("\n=== TEST 5: Filter Application ===")
    
    # Mock stock data with tokens
    mock_stocks = [
        {
            'symbol': 'AAPL',
            'tokens': ['sector_technology', 'price_up_moderate', 'volume_high', 'market_cap_large']
        },
        {
            'symbol': 'MSFT',
            'tokens': ['sector_technology', 'price_down_slight', 'volume_normal', 'market_cap_large']
        },
        {
            'symbol': 'JPM',
            'tokens': ['sector_financial_services', 'price_up_slight', 'volume_high', 'market_cap_large']
        },
        {
            'symbol': 'XOM',
            'tokens': ['sector_energy', 'price_down_moderate', 'volume_normal', 'market_cap_large']
        }
    ]
    
    test_cases = [
        # (query, expected_symbols)
        ("tech stocks", ['AAPL', 'MSFT']),  # Only tech stocks
        ("bank stocks", ['JPM']),  # Only financial stocks
        ("energy stocks", ['XOM']),  # Only energy stocks
        ("growing stocks", ['AAPL', 'MSFT', 'JPM', 'XOM']),  # ALL stocks (no hard filter)
        ("large cap stocks", ['AAPL', 'MSFT', 'JPM', 'XOM']),  # ALL stocks (no hard filter)
        ("tech growing stocks", ['AAPL', 'MSFT']),  # Only tech (growing is for ranking)
    ]
    
    for query, expected_symbols in test_cases:
        result = query_filter_engine.filter_stocks(query, mock_stocks)
        result_symbols = [s['symbol'] for s in result]
        print(f"Query: '{query}'")
        print(f"  Expected: {expected_symbols}")
        print(f"  Got: {result_symbols}")
        assert result_symbols == expected_symbols, f"Mismatch for query: {query}"
        print("  ✅ PASS\n")
    
    print("✅ All filter application tests passed\n")


def test_no_filters():
    """Test queries with no hard filter keywords"""
    print("\n=== TEST 6: No Filters (All Stocks Should Pass) ===")
    
    test_cases = [
        "high volume stocks",
        "best performing stocks",
        "top gainers today",
        "stocks with momentum",
        "RSI oversold stocks",
    ]
    
    mock_stocks = [
        {'symbol': 'AAPL', 'tokens': ['sector_technology']},
        {'symbol': 'JPM', 'tokens': ['sector_financial_services']},
        {'symbol': 'XOM', 'tokens': ['sector_energy']},
    ]
    
    for query in test_cases:
        filters = query_filter_engine.extract_hard_filters(query)
        result = query_filter_engine.filter_stocks(query, mock_stocks)
        print(f"Query: '{query}'")
        print(f"  Filters: {filters}")
        print(f"  Stocks passing: {len(result)}/{len(mock_stocks)}")
        assert len(result) == len(mock_stocks), f"All stocks should pass for: {query}"
        print("  ✅ PASS (all stocks pass through)\n")
    
    print("✅ No-filter queries correctly return all stocks\n")


def run_all_tests():
    """Run all test functions"""
    print("=" * 60)
    print("QUERY FILTER ENGINE TEST SUITE")
    print("=" * 60)
    print("\nDESIGN PHILOSOPHY:")
    print("- Only SECTOR is a hard filter (AND logic)")
    print("- Growth/MarketCap are BM25 ranking signals (OR logic)")
    print("- This prevents over-filtering issues")
    print("=" * 60)
    
    try:
        test_sector_filter_extraction()
        test_growth_not_hard_filter()
        test_market_cap_not_hard_filter()
        test_combined_queries_only_extract_sector()
        test_filter_application()
        test_no_filters()
        
        print("=" * 60)
        print("🎉 ALL TESTS PASSED!")
        print("=" * 60)
        return True
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)

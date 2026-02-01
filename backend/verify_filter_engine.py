"""
Quick Verification Script - Demonstrates Query Filter Engine

This script shows the filter engine working correctly
without needing the full API setup.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from query_filter_engine import query_filter_engine


def verify_filter_engine():
    """Demonstrate the filter engine with realistic examples"""
    
    print("\n" + "="*70)
    print("QUERY FILTER ENGINE - VERIFICATION")
    print("="*70)
    
    # Simulate tokenized stock data
    stocks = [
        {
            'symbol': 'AAPL',
            'sector': 'Technology',
            'change_percent': 2.5,
            'market_cap': 3000000000000,
            'tokens': ['sector_technology', 'growth_positive', 'price_up', 'market_cap_large']
        },
        {
            'symbol': 'GOOGL',
            'sector': 'Technology',
            'change_percent': 1.8,
            'market_cap': 2000000000000,
            'tokens': ['sector_technology', 'growth_positive', 'price_up', 'market_cap_large']
        },
        {
            'symbol': 'MSFT',
            'sector': 'Technology',
            'change_percent': -0.5,
            'market_cap': 2800000000000,
            'tokens': ['sector_technology', 'growth_negative', 'price_down', 'market_cap_large']
        },
        {
            'symbol': 'XOM',
            'sector': 'Energy',
            'change_percent': 3.2,
            'market_cap': 500000000000,
            'tokens': ['sector_energy', 'growth_positive', 'price_up', 'market_cap_large']
        },
        {
            'symbol': 'JPM',
            'sector': 'Financial Services',
            'change_percent': 1.5,
            'market_cap': 600000000000,
            'tokens': ['sector_financial_services', 'growth_positive', 'price_up', 'market_cap_large']
        },
        {
            'symbol': 'TSLA',
            'sector': 'Automotive',
            'change_percent': 5.0,
            'market_cap': 800000000000,
            'tokens': ['sector_automotive', 'growth_positive', 'price_strong_up', 'market_cap_large']
        },
    ]
    
    # Test scenarios
    scenarios = [
        {
            'query': 'tech growing stocks',
            'expected': ['AAPL', 'GOOGL'],
            'description': 'Only growing tech stocks'
        },
        {
            'query': 'large cap energy stocks',
            'expected': ['XOM'],
            'description': 'Only large cap energy sector'
        },
        {
            'query': 'falling tech stocks',
            'expected': ['MSFT'],
            'description': 'Only declining tech stocks'
        },
        {
            'query': 'bank stocks',
            'expected': ['JPM'],
            'description': 'Financial services sector'
        },
        {
            'query': 'growing stocks',
            'expected': ['AAPL', 'GOOGL', 'XOM', 'JPM', 'TSLA'],
            'description': 'Any sector with positive growth'
        },
        {
            'query': 'high volume stocks',
            'expected': ['AAPL', 'GOOGL', 'MSFT', 'XOM', 'JPM', 'TSLA'],
            'description': 'No filters - all stocks pass'
        },
    ]
    
    passed = 0
    failed = 0
    
    for scenario in scenarios:
        query = scenario['query']
        expected = set(scenario['expected'])
        description = scenario['description']
        
        print(f"\nTest: {description}")
        print(f"Query: '{query}'")
        
        # Extract filters
        filters = query_filter_engine.extract_hard_filters(query)
        print(f"Extracted filters: {filters}")
        
        # Apply filtering
        filtered = query_filter_engine.filter_stocks(query, stocks)
        result = set(s['symbol'] for s in filtered)
        
        print(f"Expected: {sorted(expected)}")
        print(f"Got:      {sorted(result)}")
        
        if result == expected:
            print("Result: PASS")
            passed += 1
        else:
            print("Result: FAIL")
            failed += 1
    
    print("\n" + "="*70)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("="*70)
    
    if failed == 0:
        print("\nSUCCESS: Filter engine working correctly")
        print("Ready for production use")
        return True
    else:
        print("\nERROR: Some tests failed")
        return False


if __name__ == "__main__":
    success = verify_filter_engine()
    sys.exit(0 if success else 1)

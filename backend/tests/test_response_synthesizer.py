"""
Test Response Synthesizer - Validates response synthesis layer

Tests:
1. Token to explanation mapping
2. Response structure validation
3. Reasons generation
4. Edge cases (empty tokens, unknown tokens)
"""

import sys
import logging
from response_synthesizer import (
    ResponseSynthesizer,
    synthesize_search_response,
    TOKEN_EXPLANATIONS
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_mock_ranked_results():
    """
    Create mock ranked results from BM25 ranker.
    Simulates the output after ranking.
    """
    return [
        {
            'symbol': 'AAPL',
            'company_name': 'Apple Inc.',
            'sector': 'Technology',
            'price': 175.50,
            'volume': 55000000,
            'average_volume': 50000000,
            'market_cap': 2800000000000,
            'change_percent': 2.5,
            'last_updated': '2026-02-01 14:30:00',
            'summary': 'Apple Inc. designs, manufactures, and markets smartphones...',
            '_score': 12.4567,
            'tokens': ['price_up', 'rising', 'bullish', 'sector_technology', 'technology', 'large_cap', 'aapl']
        },
        {
            'symbol': 'NVDA',
            'company_name': 'NVIDIA Corporation',
            'sector': 'Technology',
            'price': 495.00,
            'volume': 45000000,
            'average_volume': 40000000,
            'market_cap': 1200000000000,
            'change_percent': 3.8,
            'last_updated': '2026-02-01 14:30:00',
            'summary': 'NVIDIA Corporation designs graphics processing units...',
            '_score': 11.2345,
            'tokens': ['price_up', 'price_strong_up', 'rising', 'sector_technology', 'volume_high', 'large_cap']
        },
        {
            'symbol': 'TSLA',
            'company_name': 'Tesla Inc.',
            'sector': 'Automotive',
            'price': 245.00,
            'volume': 120000000,
            'average_volume': 80000000,
            'market_cap': 780000000000,
            'change_percent': 5.2,
            'last_updated': '2026-02-01 14:30:00',
            'summary': 'Tesla, Inc. designs, develops, manufactures, and sells...',
            '_score': 8.9876,
            'tokens': ['price_strong_up', 'volume_very_high', 'active', 'sector_automotive', 'bullish']
        }
    ]


def test_token_explanations():
    """Test that all common tokens have explanations"""
    print("\n" + "="*60)
    print("TEST 1: Token Explanation Mappings")
    print("="*60)
    
    test_tokens = [
        'price_up', 'price_down', 'volume_high', 'large_cap',
        'sector_technology', 'rsi_overbought', 'bullish', 'bearish'
    ]
    
    synthesizer = ResponseSynthesizer()
    
    print("\nTesting token mappings:")
    all_passed = True
    for token in test_tokens:
        explanation = synthesizer._get_token_explanation(token)
        has_explanation = explanation is not None
        status = "✓" if has_explanation else "✗"
        print(f"  {status} {token:20} → {explanation}")
        if not has_explanation:
            all_passed = False
    
    print(f"\nTotal explanations available: {len(TOKEN_EXPLANATIONS)}")
    return all_passed


def test_response_structure():
    """Test the structure of synthesized responses"""
    print("\n" + "="*60)
    print("TEST 2: Response Structure Validation")
    print("="*60)
    
    synthesizer = ResponseSynthesizer()
    mock_results = create_mock_ranked_results()
    
    response = synthesizer.synthesize_response(
        query="rising tech stocks",
        ranked_results=mock_results,
        ranking_method='bm25'
    )
    
    print("\nValidating response structure:")
    
    # Check top-level keys
    required_keys = ['metadata', 'results']
    all_passed = True
    
    for key in required_keys:
        exists = key in response
        status = "✓" if exists else "✗"
        print(f"  {status} Top-level key '{key}' present")
        all_passed = all_passed and exists
    
    # Check metadata structure
    if 'metadata' in response:
        metadata_keys = ['query', 'timestamp', 'total_results', 'ranking_method']
        print("\n  Metadata fields:")
        for key in metadata_keys:
            exists = key in response['metadata']
            status = "✓" if exists else "✗"
            print(f"    {status} {key}")
            all_passed = all_passed and exists
    
    # Check results structure
    if 'results' in response and len(response['results']) > 0:
        result = response['results'][0]
        result_keys = ['symbol', 'company_name', 'sector', 'rank', 'score', 'reasons', 'metrics']
        print("\n  Result fields:")
        for key in result_keys:
            exists = key in result
            status = "✓" if exists else "✗"
            print(f"    {status} {key}")
            all_passed = all_passed and exists
        
        # Check metrics structure
        if 'metrics' in result:
            metrics_keys = ['price', 'volume', 'change_percent']
            print("\n  Metrics fields:")
            for key in metrics_keys:
                exists = key in result['metrics']
                status = "✓" if exists else "✗"
                print(f"    {status} {key}")
                all_passed = all_passed and exists
    
    return all_passed


def test_reasons_generation():
    """Test generation of human-readable reasons"""
    print("\n" + "="*60)
    print("TEST 3: Reasons Generation")
    print("="*60)
    
    synthesizer = ResponseSynthesizer()
    mock_results = create_mock_ranked_results()
    
    response = synthesizer.synthesize_response(
        query="rising tech stocks",
        ranked_results=mock_results,
        ranking_method='bm25'
    )
    
    print("\nGenerated reasons for each result:")
    all_have_reasons = True
    
    for result in response['results']:
        symbol = result['symbol']
        reasons = result['reasons']
        has_reasons = len(reasons) > 0
        status = "✓" if has_reasons else "✗"
        
        print(f"\n  {status} {symbol}:")
        if reasons:
            for reason in reasons:
                print(f"      - {reason}")
        else:
            print("      (No reasons generated)")
            all_have_reasons = False
    
    return all_have_reasons


def test_edge_cases():
    """Test edge cases and error handling"""
    print("\n" + "="*60)
    print("TEST 4: Edge Cases")
    print("="*60)
    
    synthesizer = ResponseSynthesizer()
    all_passed = True
    
    # Test 1: Empty results
    print("\n1. Empty results list:")
    response = synthesizer.synthesize_response(
        query="test query",
        ranked_results=[],
        ranking_method='bm25'
    )
    passed = len(response['results']) == 0 and response['metadata']['total_results'] == 0
    status = "✓" if passed else "✗"
    print(f"   {status} Returns valid structure with 0 results")
    all_passed = all_passed and passed
    
    # Test 2: Results with no tokens
    print("\n2. Results with empty token list:")
    result_no_tokens = {
        'symbol': 'TEST',
        'company_name': 'Test Company',
        'sector': 'Technology',
        'price': 100.0,
        'volume': 1000000,
        'change_percent': 0.0,
        '_score': 5.0,
        'tokens': []  # Empty tokens
    }
    response = synthesizer.synthesize_response(
        query="test",
        ranked_results=[result_no_tokens],
        ranking_method='bm25'
    )
    passed = len(response['results'][0]['reasons']) == 0
    status = "✓" if passed else "✗"
    print(f"   {status} Handles empty tokens gracefully (empty reasons list)")
    all_passed = all_passed and passed
    
    # Test 3: Unknown tokens
    print("\n3. Results with unknown tokens:")
    result_unknown_tokens = {
        'symbol': 'TEST',
        'company_name': 'Test Company',
        'sector': 'Technology',
        'price': 100.0,
        'volume': 1000000,
        'change_percent': 0.0,
        '_score': 5.0,
        'tokens': ['unknown_token_xyz', 'another_unknown']
    }
    response = synthesizer.synthesize_response(
        query="test",
        ranked_results=[result_unknown_tokens],
        ranking_method='bm25'
    )
    # Should have empty reasons since tokens are unknown
    passed = len(response['results'][0]['reasons']) == 0
    status = "✓" if passed else "✗"
    print(f"   {status} Handles unknown tokens (no crash, empty reasons)")
    all_passed = all_passed and passed
    
    # Test 4: Sector pattern tokens
    print("\n4. Dynamic sector token pattern:")
    result_sector = {
        'symbol': 'TEST',
        'company_name': 'Test Company',
        'sector': 'Custom Sector',
        'price': 100.0,
        'volume': 1000000,
        'change_percent': 0.0,
        '_score': 5.0,
        'tokens': ['sector_custom_sector']
    }
    response = synthesizer.synthesize_response(
        query="test",
        ranked_results=[result_sector],
        ranking_method='bm25'
    )
    reasons = response['results'][0]['reasons']
    passed = len(reasons) > 0 and 'Custom Sector sector' in reasons[0]
    status = "✓" if passed else "✗"
    print(f"   {status} Generates explanation for dynamic sector tokens")
    if passed:
        print(f"      Generated: {reasons[0]}")
    all_passed = all_passed and passed
    
    return all_passed


def test_full_integration():
    """Test full integration with realistic data"""
    print("\n" + "="*60)
    print("TEST 5: Full Integration Test")
    print("="*60)
    
    mock_results = create_mock_ranked_results()
    
    # Use convenience function
    response = synthesize_search_response(
        query="rising tech stocks with high volume",
        ranked_results=mock_results,
        ranking_method='bm25'
    )
    
    print("\nFull response structure:")
    print(f"  Query: {response['metadata']['query']}")
    print(f"  Total results: {response['metadata']['total_results']}")
    print(f"  Ranking method: {response['metadata']['ranking_method']}")
    print(f"  Timestamp: {response['metadata']['timestamp']}")
    
    print("\n  Results:")
    for result in response['results']:
        print(f"\n    Rank {result['rank']}: {result['symbol']} (score: {result['score']})")
        print(f"      Company: {result['company_name']}")
        print(f"      Sector: {result['sector']}")
        print(f"      Reasons ({len(result['reasons'])}):")
        for reason in result['reasons']:
            print(f"        - {reason}")
        print(f"      Metrics: Price=${result['metrics']['price']}, " +
              f"Change={result['metrics']['change_percent']}%")
    
    # Validate
    all_passed = True
    all_passed = all_passed and response['metadata']['total_results'] == 3
    all_passed = all_passed and len(response['results']) == 3
    all_passed = all_passed and all(len(r['reasons']) > 0 for r in response['results'])
    
    return all_passed


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("RESPONSE SYNTHESIZER - TEST SUITE")
    print("="*60)
    
    tests = [
        ("Token Explanations", test_token_explanations),
        ("Response Structure", test_response_structure),
        ("Reasons Generation", test_reasons_generation),
        ("Edge Cases", test_edge_cases),
        ("Full Integration", test_full_integration),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            logger.error(f"{test_name} failed with exception: {e}", exc_info=True)
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status}: {test_name}")
    
    all_passed = all(passed for _, passed in results)
    
    print("\n" + "="*60)
    if all_passed:
        print("✓ ALL TESTS PASSED")
    else:
        print("✗ SOME TESTS FAILED")
    print("="*60 + "\n")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

"""
Test BM25 Stock Ranking System

This script tests the complete pipeline:
1. Stock tokenization
2. Query tokenization
3. BM25 ranking
4. Results validation
"""

import sys
import logging
from stock_tokenizer import stock_tokenizer, query_tokenizer
from bm25_stock_ranker import create_ranker

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_mock_stocks():
    """
    Create mock stock data for testing.
    Simulates real-time stock snapshots.
    """
    return [
        {
            'symbol': 'AAPL',
            'company_name': 'Apple Inc.',
            'sector': 'Technology',
            'price': 175.50,
            'volume': 55000000,
            'average_volume': 50000000,
            'change_percent': 2.5,
            'market_cap': 2800000000000,
        },
        {
            'symbol': 'TSLA',
            'company_name': 'Tesla Inc.',
            'sector': 'Automotive',
            'price': 245.00,
            'volume': 120000000,
            'average_volume': 80000000,
            'change_percent': 5.2,
            'market_cap': 780000000000,
        },
        {
            'symbol': 'JPM',
            'company_name': 'JPMorgan Chase & Co.',
            'sector': 'Financial Services',
            'price': 155.25,
            'volume': 8000000,
            'average_volume': 10000000,
            'change_percent': -0.8,
            'market_cap': 450000000000,
        },
        {
            'symbol': 'PFE',
            'company_name': 'Pfizer Inc.',
            'sector': 'Healthcare',
            'price': 28.50,
            'volume': 25000000,
            'average_volume': 30000000,
            'change_percent': -1.2,
            'market_cap': 160000000000,
        },
        {
            'symbol': 'NVDA',
            'company_name': 'NVIDIA Corporation',
            'sector': 'Technology',
            'price': 495.00,
            'volume': 45000000,
            'average_volume': 40000000,
            'change_percent': 3.8,
            'market_cap': 1200000000000,
        },
        {
            'symbol': 'XOM',
            'company_name': 'Exxon Mobil Corporation',
            'sector': 'Energy',
            'price': 105.75,
            'volume': 15000000,
            'average_volume': 20000000,
            'change_percent': -0.5,
            'market_cap': 420000000000,
        },
    ]


def test_stock_tokenization():
    """Test stock tokenization"""
    print("\n" + "="*60)
    print("TEST 1: Stock Tokenization")
    print("="*60)
    
    stocks = create_mock_stocks()
    
    for stock in stocks[:3]:  # Test first 3
        tokens = stock_tokenizer.tokenize_stock(stock)
        print(f"\n{stock['symbol']} ({stock['company_name']})")
        print(f"  Price Change: {stock['change_percent']}%")
        print(f"  Volume: {stock['volume']:,}")
        print(f"  Tokens: {tokens}")


def test_query_tokenization():
    """Test query tokenization"""
    print("\n" + "="*60)
    print("TEST 2: Query Tokenization")
    print("="*60)
    
    queries = [
        "rising tech stocks",
        "high volume stocks",
        "falling financial stocks",
        "large cap technology",
        "apple",
        "stocks with momentum",
        "bullish automotive",
    ]
    
    for query in queries:
        tokens = query_tokenizer.tokenize_query(query)
        print(f"\nQuery: '{query}'")
        print(f"  Tokens: {tokens}")


def test_bm25_ranking():
    """Test BM25 ranking"""
    print("\n" + "="*60)
    print("TEST 3: BM25 Ranking")
    print("="*60)
    
    # Create ranker
    ranker = create_ranker(stock_tokenizer, query_tokenizer)
    
    # Get mock data
    stocks = create_mock_stocks()
    
    # Test queries
    test_queries = [
        "rising tech stocks",
        "high volume",
        "falling stocks",
        "apple",
        "large cap technology",
        "automotive with momentum",
    ]
    
    for query in test_queries:
        print(f"\n{'─'*60}")
        print(f"Query: '{query}'")
        print(f"{'─'*60}")
        
        results = ranker.rank_live_stocks(
            query=query,
            live_stocks=stocks,
            top_k=5
        )
        
        if results:
            print(f"\nTop {len(results)} Results:")
            for rank, (symbol, score, stock_data) in enumerate(results, 1):
                print(f"  {rank}. {symbol} ({stock_data['company_name']})")
                print(f"     Score: {score:.4f}")
                print(f"     Sector: {stock_data['sector']}")
                print(f"     Change: {stock_data['change_percent']}%")
        else:
            print("\n  No results found")


def test_edge_cases():
    """Test edge cases"""
    print("\n" + "="*60)
    print("TEST 4: Edge Cases")
    print("="*60)
    
    ranker = create_ranker(stock_tokenizer, query_tokenizer)
    stocks = create_mock_stocks()
    
    # Empty query
    print("\n1. Empty query:")
    results = ranker.rank_live_stocks("", stocks, top_k=3)
    print(f"   Results: {len(results)}")
    
    # Very specific query with no matches
    print("\n2. No matching tokens:")
    results = ranker.rank_live_stocks("xyzabc123", stocks, top_k=3)
    print(f"   Results: {len(results)}")
    
    # Query all stocks
    print("\n3. Broad query:")
    results = ranker.rank_live_stocks("stocks", stocks, top_k=3)
    print(f"   Results: {len(results)}")
    if results:
        for symbol, score, _ in results[:3]:
            print(f"     - {symbol}: {score:.4f}")


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("BM25 STOCK RANKING SYSTEM - TEST SUITE")
    print("="*60)
    
    try:
        test_stock_tokenization()
        test_query_tokenization()
        test_bm25_ranking()
        test_edge_cases()
        
        print("\n" + "="*60)
        print("✓ ALL TESTS COMPLETED")
        print("="*60 + "\n")
        
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

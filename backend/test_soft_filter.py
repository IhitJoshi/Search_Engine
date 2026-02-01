"""
Test soft filter functionality for growth-based queries.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from bm25_stock_ranker import create_ranker
from stock_tokenizer import stock_tokenizer, query_tokenizer

# Create mock stocks with realistic data
mock_stocks = [
    {'symbol': 'AAPL', 'company_name': 'Apple', 'sector': 'Technology', 'price': 200, 'change_percent': 2.5, 'volume': 100000, 'average_volume': 90000, 'market_cap': 3000000000000},
    {'symbol': 'MSFT', 'company_name': 'Microsoft', 'sector': 'Technology', 'price': 400, 'change_percent': -1.5, 'volume': 80000, 'average_volume': 75000, 'market_cap': 2800000000000},
    {'symbol': 'TSLA', 'company_name': 'Tesla', 'sector': 'Technology', 'price': 300, 'change_percent': 5.2, 'volume': 150000, 'average_volume': 120000, 'market_cap': 800000000000},
    {'symbol': 'NVDA', 'company_name': 'NVIDIA', 'sector': 'Technology', 'price': 500, 'change_percent': -2.0, 'volume': 200000, 'average_volume': 180000, 'market_cap': 1200000000000},
    {'symbol': 'GOOGL', 'company_name': 'Alphabet', 'sector': 'Technology', 'price': 140, 'change_percent': 0.3, 'volume': 50000, 'average_volume': 55000, 'market_cap': 1800000000000},
    {'symbol': 'JPM', 'company_name': 'JPMorgan', 'sector': 'Financial Services', 'price': 180, 'change_percent': 1.2, 'volume': 60000, 'average_volume': 55000, 'market_cap': 500000000000},
]

ranker = create_ranker(stock_tokenizer, query_tokenizer)

print("=" * 60)
print("TEST: tech growing stocks")
print("EXPECTED: Only tech stocks with POSITIVE change_percent")
print("=" * 60)

results = ranker.rank_live_stocks('tech growing stocks', mock_stocks, top_k=10)

print(f"\nResults ({len(results)} stocks):")
all_positive = True
all_tech = True
for symbol, score, data in results:
    change = data.get('change_percent', 0)
    sector = data.get('sector', 'Unknown')
    status = "✅" if change > 0 else "❌"
    print(f"  {status} {symbol}: {change}% change, sector: {sector}")
    if change <= 0:
        all_positive = False
    if sector != 'Technology':
        all_tech = False

print()
if all_positive and all_tech and len(results) > 0:
    print("✅ PASS: All results are growing tech stocks!")
else:
    if not all_tech:
        print("❌ FAIL: Non-tech stocks in results")
    if not all_positive:
        print("❌ FAIL: Falling stocks in results")
    if len(results) == 0:
        print("❌ FAIL: No results returned")

print("\n" + "=" * 60)
print("TEST: tech falling stocks")
print("EXPECTED: Only tech stocks with NEGATIVE change_percent")
print("=" * 60)

results2 = ranker.rank_live_stocks('tech falling stocks', mock_stocks, top_k=10)

print(f"\nResults ({len(results2)} stocks):")
all_negative = True
all_tech2 = True
for symbol, score, data in results2:
    change = data.get('change_percent', 0)
    sector = data.get('sector', 'Unknown')
    status = "✅" if change < 0 else "❌"
    print(f"  {status} {symbol}: {change}% change, sector: {sector}")
    if change >= 0:
        all_negative = False
    if sector != 'Technology':
        all_tech2 = False

print()
if all_negative and all_tech2 and len(results2) > 0:
    print("✅ PASS: All results are falling tech stocks!")
else:
    if not all_tech2:
        print("❌ FAIL: Non-tech stocks in results")
    if not all_negative:
        print("❌ FAIL: Growing stocks in results")
    if len(results2) == 0:
        print("❌ FAIL: No results returned")

print("\n" + "=" * 60)
print("TEST: tech stocks (no growth keyword)")
print("EXPECTED: All tech stocks regardless of growth")
print("=" * 60)

results3 = ranker.rank_live_stocks('tech stocks', mock_stocks, top_k=10)

print(f"\nResults ({len(results3)} stocks):")
for symbol, score, data in results3:
    change = data.get('change_percent', 0)
    sector = data.get('sector', 'Unknown')
    print(f"  {symbol}: {change}% change, sector: {sector}")

print()
# Should have both positive and negative tech stocks
tech_count = sum(1 for _, _, d in results3 if d.get('sector') == 'Technology')
if tech_count == 5:  # We have 5 tech stocks in mock data
    print("✅ PASS: All tech stocks returned (no growth filter applied)")
else:
    print(f"❌ FAIL: Expected 5 tech stocks, got {tech_count}")

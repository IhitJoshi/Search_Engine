"""
Test soft filter with REAL database data (49 stocks across 5 sectors).
"""
import sys
import os
import sqlite3
sys.path.insert(0, os.path.dirname(__file__))

from bm25_stock_ranker import create_ranker
from stock_tokenizer import stock_tokenizer, query_tokenizer

# Load real stocks from database
conn = sqlite3.connect('stocks.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()
cursor.execute('''
    SELECT s1.* FROM stocks s1
    JOIN (
        SELECT symbol, MAX(last_updated) as latest 
        FROM stocks 
        GROUP BY symbol
    ) s2 ON s1.symbol = s2.symbol AND s1.last_updated = s2.latest
''')
real_stocks = [dict(row) for row in cursor.fetchall()]
conn.close()

print(f"Loaded {len(real_stocks)} stocks from database\n")

# Count by sector
sectors = {}
for s in real_stocks:
    sec = s.get('sector', 'Unknown')
    sectors[sec] = sectors.get(sec, 0) + 1
print("Stocks by sector:")
for sec, count in sorted(sectors.items()):
    print(f"  {sec}: {count}")

ranker = create_ranker(stock_tokenizer, query_tokenizer)

print("\n" + "=" * 60)
print("TEST: 'tech growing stocks'")
print("EXPECTED: Only Technology stocks with POSITIVE change_percent")
print("=" * 60)

results = ranker.rank_live_stocks('tech growing stocks', real_stocks, top_k=20)

print(f"\nResults ({len(results)} stocks):")
all_positive = True
all_tech = True
for symbol, score, data in results:
    change = data.get('change_percent', 0) or 0
    sector = data.get('sector', 'Unknown')
    status = "✅" if change > 0 else "❌"
    print(f"  {status} {symbol}: {change:+.2f}% change, sector: {sector}")
    if change <= 0:
        all_positive = False
    if sector != 'Technology':
        all_tech = False

print()
if all_positive and all_tech and len(results) > 0:
    print("✅ PASS: All results are growing tech stocks!")
elif len(results) == 0:
    print("⚠️ No growing tech stocks found (all tech stocks may be falling)")
else:
    if not all_tech:
        print("❌ FAIL: Non-tech stocks in results")
    if not all_positive:
        print("❌ FAIL: Falling stocks in results")

print("\n" + "=" * 60)
print("TEST: 'tech falling stocks'")
print("EXPECTED: Only Technology stocks with NEGATIVE change_percent")
print("=" * 60)

results = ranker.rank_live_stocks('tech falling stocks', real_stocks, top_k=20)

print(f"\nResults ({len(results)} stocks):")
all_negative = True
all_tech = True
for symbol, score, data in results:
    change = data.get('change_percent', 0) or 0
    sector = data.get('sector', 'Unknown')
    status = "✅" if change < 0 else "❌"
    print(f"  {status} {symbol}: {change:+.2f}% change, sector: {sector}")
    if change >= 0:
        all_negative = False
    if sector != 'Technology':
        all_tech = False

print()
if all_negative and all_tech and len(results) > 0:
    print("✅ PASS: All results are falling tech stocks!")
elif len(results) == 0:
    print("⚠️ No falling tech stocks found (all tech stocks may be growing)")
else:
    if not all_tech:
        print("❌ FAIL: Non-tech stocks in results")
    if not all_negative:
        print("❌ FAIL: Growing stocks in results")

print("\n" + "=" * 60)
print("TEST: 'healthcare stocks'")
print("EXPECTED: Only Healthcare stocks (no growth filter)")
print("=" * 60)

results = ranker.rank_live_stocks('healthcare stocks', real_stocks, top_k=20)

print(f"\nResults ({len(results)} stocks):")
all_healthcare = True
for symbol, score, data in results:
    change = data.get('change_percent', 0) or 0
    sector = data.get('sector', 'Unknown')
    print(f"  {symbol}: {change:+.2f}% change, sector: {sector}")
    if sector != 'Healthcare':
        all_healthcare = False

print()
if all_healthcare and len(results) > 0:
    print("✅ PASS: All results are healthcare stocks!")
else:
    print("❌ FAIL: Non-healthcare stocks in results")

print("\n" + "=" * 60)
print("TEST: 'energy growing stocks'")
print("EXPECTED: Only Energy stocks with POSITIVE change_percent")
print("=" * 60)

results = ranker.rank_live_stocks('energy growing stocks', real_stocks, top_k=20)

print(f"\nResults ({len(results)} stocks):")
for symbol, score, data in results:
    change = data.get('change_percent', 0) or 0
    sector = data.get('sector', 'Unknown')
    status = "✅" if change > 0 and sector == 'Energy' else "❌"
    print(f"  {status} {symbol}: {change:+.2f}% change, sector: {sector}")

import sqlite3

conn = sqlite3.connect('stocks.db')
cursor = conn.cursor()
cursor.execute('SELECT symbol, company_name, sector FROM stocks WHERE sector IS NOT NULL GROUP BY symbol ORDER BY sector, symbol')

print("\nSTOCKS BY SECTOR:\n" + "="*80)
current_sector = None
for row in cursor.fetchall():
    sector, symbol, name = row[2], row[0], row[1]
    if sector != current_sector:
        current_sector = sector
        print(f"\n{sector}:")
        print("-"*80)
    print(f"  {symbol:10} | {name}")

conn.close()

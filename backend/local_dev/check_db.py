import sqlite3

conn = sqlite3.connect('stocks.db')
cursor = conn.cursor()

# Check all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
print("All tables:", cursor.fetchall())

# Check if stocks table exists and show some data
try:
    cursor.execute("SELECT symbol, sector, company_name FROM stocks LIMIT 30")
    rows = cursor.fetchall()
    print(f"\nFound {len(rows)} stocks:")
    for row in rows:
        print(f"  {row[0]}: {row[1]} - {row[2]}")
    
    # Count by sector
    cursor.execute("SELECT sector, COUNT(*) FROM stocks GROUP BY sector")
    sectors = cursor.fetchall()
    print(f"\nStocks by sector:")
    for sector in sectors:
        print(f"  {sector[0]}: {sector[1]} stocks")
except Exception as e:
    print(f"Error: {e}")

conn.close()

import sqlite3
conn = sqlite3.connect('stocks.db')
cursor = conn.cursor()

# Check tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
print('Tables:', cursor.fetchall())

# Check schema
cursor.execute('PRAGMA table_info(stocks)')
print('Schema:', cursor.fetchall())

# Insert test data
stocks = [
    ('AAPL', 'Apple Inc.', 'Technology', 259.48, 79605051, 46590713, 3813817974784, 0.46, 'Apple designs iPhones'),
    ('MSFT', 'Microsoft Corporation', 'Technology', 430.29, 55377986, 27213203, 3195174125568, -0.74, 'Microsoft makes Windows'),
    ('NVDA', 'NVIDIA Corporation', 'Technology', 191.13, 166207923, 181664229, 4653442400256, -0.72, 'NVIDIA makes GPUs'),
    ('GOOGL', 'Alphabet Inc.', 'Technology', 338.00, 26924773, 35328359, 4093897080832, -0.07, 'Google search'),
    ('TSLA', 'Tesla, Inc.', 'Technology', 430.41, 82299930, 74413947, 1615084257280, 3.32, 'Tesla makes EVs'),
    ('META', 'Meta Platforms, Inc.', 'Technology', 716.50, 22691755, 18298054, 1812426522624, -2.95, 'Meta owns Facebook'),
    ('AMZN', 'Amazon.com, Inc.', 'Technology', 239.30, 45765454, 41512196, 2558168662016, -1.01, 'Amazon ecommerce'),
    ('AVGO', 'Broadcom Inc.', 'Technology', 331.30, 28070188, 29914786, 1570783887360, 0.17, 'Broadcom'),
    ('TSM', 'Taiwan Semiconductor', 'Technology', 330.56, 9911047, 12589786, 1714450989056, -2.45, 'TSM chips'),
    ('TCEHY', 'Tencent Holdings', 'Technology', 77.80, 101082, 2279263, 701848616960, -1.94, 'Tencent'),
    ('JPM', 'JPMorgan Chase', 'Financial Services', 305.89, 8000000, 7500000, 500000000000, 1.2, 'JPM bank'),
    ('BAC', 'Bank of America', 'Financial Services', 53.20, 6000000, 5500000, 300000000000, 0.30, 'BAC bank'),
    ('V', 'Visa Inc.', 'Financial Services', 321.83, 5000000, 4500000, 400000000000, -2.93, 'Visa'),
]

for s in stocks:
    cursor.execute('''
        INSERT OR REPLACE INTO stocks 
        (symbol, company_name, sector, price, volume, average_volume, market_cap, change_percent, summary, last_updated)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
    ''', s)

conn.commit()
print(f'Inserted {len(stocks)} stocks')

cursor.execute('SELECT COUNT(*) FROM stocks')
print(f'Total stocks in DB: {cursor.fetchone()[0]}')

cursor.execute('SELECT symbol, sector, change_percent FROM stocks')
for row in cursor.fetchall():
    print(f'  {row[0]}: {row[1]}, {row[2]}%')

conn.close()

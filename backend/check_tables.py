import sqlite3

# Check stocks.db
print("=== stocks.db ===")
conn = sqlite3.connect('stocks.db')
print("Tables:", conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall())
conn.close()

# Check users.db
print("\n=== users.db ===")
conn = sqlite3.connect('users.db')
print("Tables:", conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall())
print("Users:", conn.execute("SELECT username, email FROM users").fetchall())
conn.close()

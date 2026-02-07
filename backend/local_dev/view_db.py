import sqlite3

# connect to db
conn = sqlite3.connect("users.db")
cur = conn.cursor()

# list all tables
cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
print("Tables:", cur.fetchall())

# check structure of users table
cur.execute("PRAGMA table_info(users);")
print("\nUsers Table Schema:")
for row in cur.fetchall():
    print(row)

# fetch all users
print("\nUsers Data:")
cur.execute("SELECT * FROM users;")
for row in cur.fetchall():
    print(row)

conn.close()

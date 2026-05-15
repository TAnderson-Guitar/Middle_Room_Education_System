import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT,
    google_id TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL,
    day TEXT NOT NULL,
    slot TEXT NOT NULL
)
""")
               
cursor.execute("ALTER TABLE users ADD COLUMN training_done INTEGER DEFAULT 0;")
cursor.execute("ALTER TABLE users ADD COLUMN test_done INTEGER DEFAULT 0;")


conn.commit()
conn.close()

print("Database created with users + bookings tables.")

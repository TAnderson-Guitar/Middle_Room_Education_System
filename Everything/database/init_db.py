import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT,
    google_id TEXT,
    training_done INTEGER DEFAULT 0,
    test_done INTEGER DEFAULT 0,
    is_admin INTEGER DEFAULT 0,
    is_superadmin INTEGER DEFAULT 0
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

cursor.execute("""
CREATE TABLE IF NOT EXISTS training_sections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    content TEXT,
    position INTEGER
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT,
    option_a TEXT,
    option_b TEXT,
    option_c TEXT,
    option_d TEXT,
    correct_option TEXT
)
""")

admins = [
    "luke.cole9@det.nsw.edu.au",
    "VALERIE.RODRIGUEZFREDES@det.nsw.edu.au",
    "McKenzie.Ward1@det.nsw.edu.au",
    "twj.anderson08@gmail.com"
]

for email in admins:
    cursor.execute("UPDATE users SET is_admin = 1 WHERE email = ?", (email,))

conn.commit()
conn.close()

print("Database initialized successfully.")

import sqlite3

conn = sqlite3.connect("database.db")
cur = conn.cursor()

cur.execute("ALTER TABLE users ADD COLUMN training_done INTEGER DEFAULT 0;")
cur.execute("ALTER TABLE users ADD COLUMN test_done INTEGER DEFAULT 0;")

conn.commit()
conn.close()

print("Columns added.")

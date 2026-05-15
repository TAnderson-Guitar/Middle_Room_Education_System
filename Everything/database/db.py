import sqlite3, time

def get_db():
    db = sqlite3.connect("database.db", check_same_thread=False)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL;")
    db.execute("PRAGMA busy_timeout = 3000;")
    return db


def execute_write(db, query, params=()):
    for _ in range(5):
        try:
            cur = db.execute(query, params)
            return cur
        except sqlite3.OperationalError as e:
            if "locked" in str(e).lower():
                time.sleep(0.1)
            else:
                raise
    raise Exception("Database locked too long")

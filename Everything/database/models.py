from database.db import get_db

def get_user_by_email(email):
    db = get_db()
    return db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()

def create_user(email, password_hash=None, google_id=None):
    db = get_db()
    db.execute(
        "INSERT INTO users (email, password_hash, google_id) VALUES (?, ?, ?)",
        (email, password_hash, google_id)
    )
    db.commit()
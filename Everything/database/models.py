from database.db import get_db
from utils.security import hash_password

def get_user_by_email(email):
    db = get_db()
    row = db.execute(
        "SELECT email, password_hash, google_id FROM users WHERE email = ?",
        (email,)
    ).fetchone()

    if row:
        return {
            "email": row[0],
            "password_hash": row[1],
            "google_id": row[2]
        }

    return None


def create_user(email, password=None, google_id=None):
    db = get_db()

    db.execute(
        """
        INSERT INTO users (email, password_hash, google_id)
        VALUES (?, ?, ?)
        """,
        (
            email,
            hash_password(password) if password else None,
            google_id
        )
    )

    db.commit()

def create_booking(email, day, slot):
    db = get_db()
    db.execute(
        "INSERT INTO bookings (email, day, slot) VALUES (?, ?, ?)",
        (email, day, slot)
    )
    db.commit()

def get_bookings_for_user(email):
    db = get_db()
    rows = db.execute(
        "SELECT id, day, slot FROM bookings WHERE email = ?",
        (email,)
    ).fetchall()
    return [{"id": r[0], "day": r[1], "slot": r[2]} for r in rows]

def booking_exists(email, day, slot):
    db = get_db()
    row = db.execute(
        "SELECT 1 FROM bookings WHERE email = ? AND day = ? AND slot = ?",
        (email, day, slot)
    ).fetchone()
    return row is not None

def delete_booking(booking_id, email):
    db = get_db()
    db.execute(
        "DELETE FROM bookings WHERE id = ? AND email = ?",
        (booking_id, email)
    )
    db.commit()

def get_all_bookings():
    db = get_db()
    return db.execute("SELECT * FROM bookings").fetchall()

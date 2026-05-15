"""Main App for everything. Handles routing, authentication, and API endpoints."""
import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from flask import Flask, render_template, request, jsonify, redirect, session
from functools import wraps
from werkzeug.utils import secure_filename
from utils.security import verify_password
from database.models import (get_user_by_email, create_user, get_db, create_booking, get_bookings_for_user, delete_booking)
from auth.oauth import google_login_url, exchange_code_for_token, get_google_user_info
from config import FLASK_SECRET_KEY


app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY


def is_logged_in():
    return "user" in session

def training_completed():
    return session.get("training_done", False)

def test_completed():
    return session.get("test_done", False)

@app.route("/")
def home():
    return render_template("index.html")

UPLOAD_FOLDER = "static/uploads/training"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("is_admin"):
            return redirect("/")
        return f(*args, **kwargs)
    return wrapper

def superadmin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("is_superadmin"):
            return redirect("/")
        return f(*args, **kwargs)
    return wrapper

@app.route("/admin")
@admin_required
def admin_dashboard():
    return render_template("admin/dashboard.html")


@app.route("/admin/training")
@admin_required
def admin_training():
    db = get_db()
    sections = db.execute("SELECT * FROM training_sections ORDER BY position").fetchall()
    return render_template("admin/admin_training.html", sections=sections)

@app.post("/admin/training/add")
@admin_required
def admin_training_add():
    title = request.form["title"]
    content = request.form["content"]
    db = get_db()
    db.execute(
        "INSERT INTO training_sections (title, content, position) VALUES (?, ?, ?)",
        (title, content, 999)
    )
    db.commit()
    return redirect("/admin/training")

@app.post("/admin/training/delete/<int:id>")
@admin_required
def admin_training_delete(id):
    db = get_db()
    db.execute("DELETE FROM training_sections WHERE id = ?", (id,))
    db.commit()
    return redirect("/admin/training")

@app.route("/admin/training/edit/<int:id>", methods=["GET", "POST"])
@admin_required
def admin_training_edit(id):
    db = get_db()

    section = db.execute(
        "SELECT * FROM training_sections WHERE id = ?", (id,)
    ).fetchone()

    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]

        image_path = section["image_path"]

        if "image" in request.files:
            file = request.files["image"]
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
                image_path = filename

        db.execute("""
            UPDATE training_sections
            SET title = ?, content = ?, image_path = ?
            WHERE id = ?
        """, (title, content, image_path, id))
        db.commit()

        return redirect("/admin/training")

    return render_template("admin/edit_training.html", section=section)


@app.route("/admin/questions/edit/<int:id>", methods=["GET", "POST"])
@admin_required
def admin_questions_edit(id):
    db = get_db()

    if request.method == "POST":
        question = request.form["question"]
        a = request.form["a"]
        b = request.form["b"]
        c = request.form["c"]
        d = request.form["d"]
        correct = request.form["correct"]

        db.execute("""
            UPDATE questions
            SET question = ?, option_a = ?, option_b = ?, option_c = ?, option_d = ?, correct_option = ?
            WHERE id = ?
        """, (question, a, b, c, d, correct, id))
        db.commit()

        return redirect("/admin/questions")

    q = db.execute(
        "SELECT * FROM questions WHERE id = ?", (id,)
    ).fetchone()

    return render_template("admin/edit_question.html", q=q)


@app.route("/admin/questions")
@admin_required
def admin_questions():
    db = get_db()
    questions = db.execute("SELECT * FROM questions ORDER BY id").fetchall()
    return render_template("admin/admin_questions.html", questions=questions)

@app.post("/admin/questions/add")
@admin_required
def admin_questions_add():
    data = request.form
    db = get_db()
    db.execute("""
        INSERT INTO questions (question, option_a, option_b, option_c, option_d, correct_option)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (data["question"], data["a"], data["b"], data["c"], data["d"], data["correct"]))
    db.commit()
    return redirect("/admin/questions")

@app.post("/admin/questions/delete/<int:id>")
@admin_required
def admin_questions_delete(id):
    db = get_db()
    db.execute("DELETE FROM questions WHERE id = ?", (id,))
    db.commit()
    return redirect("/admin/questions")


@app.route("/admin/bookings")
@admin_required
def admin_bookings():
    db = get_db()
    bookings = db.execute("SELECT * FROM bookings ORDER BY day, slot").fetchall()
    return render_template("admin/admin_bookings.html", bookings=bookings)

@app.post("/admin/bookings/delete/<int:id>")
@admin_required
def admin_booking_delete(id):
    db = get_db()
    db.execute("DELETE FROM bookings WHERE id = ?", (id,))
    db.commit()
    return redirect("/admin/bookings")


@app.route("/admin/users")
@admin_required
def admin_users():
    db = get_db()
    users = db.execute("SELECT * FROM users").fetchall()
    return render_template("admin/admin_users.html", users=users)

@app.route("/superadmin")
@superadmin_required
def superadmin_dashboard():
    db = get_db()
    users = db.execute("SELECT * FROM users").fetchall()
    return render_template("admin/superadmin_dashboard.html", users=users)




TEST_QUESTIONS = [
    {
        "id": "q1",
        "text": "Who is allowed to book the Middle Room?",
        "options": [
            "Any student at any time",
            "Only trained and approved students",
            "Parents and visitors",
            "Only the principal"
        ],
        "answer": 1
    },
    {
        "id": "q2",
        "text": "What should you do if equipment is damaged?",
        "options": [
            "Keep using it",
            "Hide it so no one sees",
            "Report it to a teacher immediately",
            "Leave it for the next person"
        ],
        "answer": 2
    },
    {
        "id": "q3",
        "text": "When should you arrive for your booking?",
        "options": [
            "Anytime during the session",
            "5–10 minutes late",
            "On time and ready to start",
            "Only if you feel like it"
        ],
        "answer": 2
    },
    {
        "id": "q4",
        "text": "How should you leave the Middle Room?",
        "options": [
            "Messy, someone else will clean",
            "Exactly how you found it or better",
            "With gear left on",
            "Chairs and cables everywhere"
        ],
        "answer": 1
    }
]


@app.route("/training", methods=["GET", "POST"])
def training():
    if not is_logged_in():
        return redirect("/login")

    db = get_db()
    sections = db.execute("SELECT * FROM training_sections ORDER BY position").fetchall()

    if request.method == "POST":
        session["training_done"] = True

        db.execute("UPDATE users SET training_done = 1 WHERE email = ?", (session["user"],))
        db.commit()

        return redirect("/test")

    return render_template("training.html", sections=sections)


@app.route("/test", methods=["GET", "POST"])
def test():
    if not is_logged_in():
        return redirect("/login")

    if not training_completed():
        return redirect("/training")

    db = get_db()
    questions = db.execute("SELECT * FROM questions ORDER BY id").fetchall()
    total = len(questions)

    if request.method == "POST":
        score = 0

        for q in questions:
            user_answer = request.form.get(str(q["id"]))
            if user_answer and user_answer.lower() == q["correct_option"].lower():
                score += 1

        passed = (score == total)

        if passed:
            session["test_done"] = True
            db.execute("UPDATE users SET test_done = 1 WHERE email = ?", (session["user"],))
            db.commit()

        return render_template("test_result.html", score=score, total=total, passed=passed)

    return render_template("test.html", questions=questions)


@app.route("/booking")
def booking():
    if not is_logged_in():
        return redirect("/login")

    if not test_completed():
        return redirect("/test")

    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    slots = ["Recess", "Lunch"]

    return render_template("booking.html", days=days, slots=slots)




@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = get_user_by_email(email)
        if not user or not verify_password(password, user["password_hash"]):
            return render_template("login.html", error="Invalid email or password")

        session["user"] = email

        db = get_db()
        progress = db.execute(
            "SELECT training_done, test_done, is_admin FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        session["training_done"] = bool(progress["training_done"])
        session["test_done"] = bool(progress["test_done"])
        session["is_admin"] = bool(progress["is_admin"])

        return redirect("/")

    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        existing_user = get_user_by_email(email)
        if existing_user:
            return render_template("register.html", error="User already exists")

        create_user(email, password)
        session["user"] = email
        return redirect("/")

    return render_template("register.html")


@app.route("/login/google")
def login_google():
    return redirect(google_login_url())


@app.route("/auth/google/callback")
def google_callback():
    code = request.args.get("code")
    token_data = exchange_code_for_token(code)
    access_token = token_data.get("access_token")

    google_user = get_google_user_info(access_token)
    email = google_user["email"]

    user = get_user_by_email(email)
    if not user:
        create_user(email, google_id=google_user["id"])
        user = get_user_by_email(email)

    session["user"] = email

    db = get_db()
    progress = db.execute(
        "SELECT training_done, test_done, is_admin FROM users WHERE email = ?",
        (email,)
    ).fetchone()

    session["training_done"] = bool(progress["training_done"])
    session["test_done"] = bool(progress["test_done"])
    session["is_admin"] = bool(progress["is_admin"])

    return redirect("/")


@app.route("/logout")
def logout():
    username = None
    if "user" in session:
        username = session["user"].split("@")[0]

    session.clear()
    return redirect(f"/logged_out?u={username}")


@app.route("/logged_out")
def logged_out():
    username = request.args.get("u", "User")
    return render_template("logged_out.html", username=username)



@app.route("/api/my_bookings")
def my_bookings():
    if not is_logged_in():
        return jsonify([])

    email = session["user"]
    bookings = get_bookings_for_user(email)
    return jsonify(bookings)


@app.route("/api/book", methods=["POST"])
def api_book():
    if not is_logged_in():
        return jsonify({"success": False, "message": "Not logged in"}), 401

    data = request.json
    day = data.get("day")
    slot = data.get("slot")
    email = session["user"]

    db = get_db()
    existing = db.execute(
        "SELECT email FROM bookings WHERE day = ? AND slot = ?",
        (day, slot)
    ).fetchone()
    db.close()

    if existing:
        username = existing["email"].split("@")[0]
        return jsonify({
            "success": False,
            "message": f"Already booked by {username}"
        })

    create_booking(email, day, slot)

    return jsonify({"success": True, "message": f"Booked {slot} on {day}!"})


@app.route("/api/cancel_booking", methods=["POST"])
def api_cancel_booking():
    if not is_logged_in():
        return jsonify({"success": False}), 401

    data = request.json
    booking_id = data.get("id")
    email = session["user"]

    db = get_db()
    booking = db.execute(
        "SELECT email FROM bookings WHERE id = ?",
        (booking_id,)
    ).fetchone()
    db.close()

    if not booking:
        return jsonify({"success": False, "message": "Booking not found"})

    if booking["email"] != email:
        return jsonify({"success": False, "message": "You cannot cancel another user's booking."})

    delete_booking(booking_id, email)

    return jsonify({"success": True})


@app.route("/api/all_bookings")
def all_bookings():
    if not is_logged_in():
        return jsonify([])

    db = get_db()
    rows = db.execute("SELECT id, email, day, slot FROM bookings").fetchall()

    bookings = []
    for r in rows:
        username = r["email"].split("@")[0]
        bookings.append({
            "id": r["id"],
            "email": r["email"],
            "username": username,
            "day": r["day"],
            "slot": r["slot"]
        })

    return jsonify(bookings)

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)

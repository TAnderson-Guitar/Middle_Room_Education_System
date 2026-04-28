import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


from flask import Flask, render_template, request, jsonify, redirect, session
from utils.security import verify_password
from database.models import get_user_by_email, create_user
from auth.oauth import google_login_url, exchange_code_for_token, get_google_user_info
from config import FLASK_SECRET_KEY, GOOGLE_REDIRECT_URI
from database.models import create_booking, get_bookings_for_user, booking_exists, delete_booking
from database.models import get_db


app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY

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


def is_logged_in():
    return "user" in session

def training_completed():
    return session.get("training_done", False)

def test_completed():
    return session.get("test_done", False)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/training", methods=["GET", "POST"])
def training():
    if not is_logged_in():
        return redirect("/login")

    if request.method == "POST":
        session["training_done"] = True

        db = get_db()
        db.execute("UPDATE users SET training_done = 1 WHERE email = ?", (session["user"],))
        db.commit()

        return redirect("/test")

    return render_template("training.html")



@app.route("/test", methods=["GET", "POST"])
def test():
    total = len(TEST_QUESTIONS)

    if not is_logged_in():
        return redirect("/login")

    if not training_completed():
        return redirect("/training")

    if request.method == "POST":
        score = 0

        for q in TEST_QUESTIONS:
            user_answer = request.form.get(q["id"])
            if user_answer and int(user_answer) == q["answer"]:
                score += 1

        passed = (score == total)

        if passed:
            session["test_done"] = True

            db = get_db()
            db.execute("UPDATE users SET test_done = 1 WHERE email = ?", (session["user"],))
            db.commit()

        return render_template("test_result.html", score=score, total=total, passed=passed)

    return render_template("test.html", questions=TEST_QUESTIONS)



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
            return "Invalid credentials", 401

        session["user"] = email

        db = get_db()
        progress = db.execute(
            "SELECT training_done, test_done FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        session["training_done"] = bool(progress["training_done"])
        session["test_done"] = bool(progress["test_done"])

        return redirect("/")

    return render_template("login.html")


@app.route("/login/local", methods=["POST"])
def login_local():
    email = request.form.get("email")
    password = request.form.get("password")

    user = get_user_by_email(email)
    if not user:
        return "User not found"

    if not verify_password(password, user["password_hash"]):
        return "Incorrect password"

    session["user"] = email

    db = get_db()
    progress = db.execute(
        "SELECT training_done, test_done FROM users WHERE email = ?",
        (email,)
    ).fetchone()

    session["training_done"] = bool(progress["training_done"])
    session["test_done"] = bool(progress["test_done"])

    return redirect("/")


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
        "SELECT training_done, test_done FROM users WHERE email = ?",
        (email,)
    ).fetchone()

    session["training_done"] = bool(progress["training_done"])
    session["test_done"] = bool(progress["test_done"])

    return redirect("/")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/api/test/submit", methods=["POST"])
def submit_test():
    data = request.json
    answers = data.get("answers", [])

    score = sum(1 for a in answers if a == "correct")
    passed = score >= 67

    return jsonify({
        "score": score,
        "passed": passed
    })

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        existing_user = get_user_by_email(email)
        if existing_user:
            return "User already exists", 400

        create_user(email, password)
        session["user"] = email
        return redirect("/")

    return render_template("register.html")

@app.route("/api/test", methods=["POST"])
def api_test():
    data = request.json
    user_input = data.get("input", "")

    return {"message": f"You sent: {user_input}"}

@app.route("/api/my_bookings")
def my_bookings():
    if not is_logged_in():
        return jsonify([])

    email = session["user"] if isinstance(session["user"], str) else session["user"]["email"]
    bookings = get_bookings_for_user(email)
    return jsonify(bookings)

@app.route("/api/book", methods=["POST"])
def api_book():
    if not is_logged_in():
        return jsonify({"success": False, "message": "Not logged in"}), 401

    data = request.json
    day = data.get("day")
    slot = data.get("slot")

    email = session["user"] if isinstance(session["user"], str) else session["user"]["email"]

    if booking_exists(email, day, slot):
        return jsonify({"success": False, "message": "You already booked this slot."})

    create_booking(email, day, slot)

    return jsonify({"success": True, "message": f"Booked {slot} on {day}!"})

@app.route("/api/cancel_booking", methods=["POST"])
def api_cancel_booking():
    if not is_logged_in():
        return jsonify({"success": False}), 401

    data = request.json
    booking_id = data.get("id")

    email = session["user"] if isinstance(session["user"], str) else session["user"]["email"]

    delete_booking(booking_id, email)

    return jsonify({"success": True})


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)

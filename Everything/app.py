from flask import Flask, render_template, request, jsonify, redirect, session
from utils.security import verify_password
from database.models import get_user_by_email, create_user
from auth.oauth import google_login_url, exchange_code_for_token, get_google_user_info
from Everything.config import FLASK_SECRET_KEY

app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY


def is_logged_in():
    return "user" in session


@app.route("/")
def home():
    return render_template("index.html")

@app.route("/training")
def training():
    if not is_logged_in():
        return redirect("/login")
    return render_template("training.html")

@app.route("/test")
def test_page():
    if not is_logged_in():
        return redirect("/login")
    return render_template("test.html")

@app.route("/booking")
def booking():
    if not is_logged_in():
        return redirect("/login")
    return render_template("booking.html")

@app.route("/login")
def login_page():
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

@app.route("/api/bookings/create", methods=["POST"])
def create_booking():
    data = request.json
    time_slot = data.get("time")

    return jsonify({
        "success": True,
        "message": f"Booking confirmed for {time_slot}"
    })

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = get_user_by_email(email)
        if not user or not verify_password(password, user["password"]):
            return "Invalid credentials", 401

        session["user"] = email
        return redirect("/")

    return render_template("login.html")


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


if __name__ == "__main__":
    app.run(debug=True)
    app.run(host="0.0.0.0", debug=True)

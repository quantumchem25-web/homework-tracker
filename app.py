import os
import sqlite3
from datetime import datetime, date, timedelta
from functools import wraps

from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, g
)
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")

DATABASE = os.path.join(os.path.dirname(__file__), "homework.db")


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DATABASE)
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS homework (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            subject TEXT NOT NULL,
            description TEXT,
            due_date TEXT NOT NULL,
            done INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        );
        """
    )
    db.commit()
    db.close()


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in first.", "info")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def get_counts(user_id):
    db = get_db()
    today = date.today().isoformat()
    done = db.execute(
        "SELECT COUNT(*) FROM homework WHERE user_id = ? AND done = 1",
        (user_id,),
    ).fetchone()[0]
    pending = db.execute(
        "SELECT COUNT(*) FROM homework WHERE user_id = ? AND done = 0 AND due_date >= ?",
        (user_id, today),
    ).fetchone()[0]
    late = db.execute(
        "SELECT COUNT(*) FROM homework WHERE user_id = ? AND done = 0 AND due_date < ?",
        (user_id, today),
    ).fetchone()[0]
    return done, pending, late


@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name or not email or not password:
            flash("Please fill in all fields.", "error")
            return redirect(url_for("signup"))

        db = get_db()
        existing = db.execute(
            "SELECT id FROM users WHERE email = ?", (email,)
        ).fetchone()
        if existing:
            flash("An account with that email already exists.", "error")
            return redirect(url_for("signup"))

        db.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, generate_password_hash(password)),
        )
        db.commit()
        flash("Account created! Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        ).fetchone()

        if user is None or not check_password_hash(user["password_hash"], password):
            flash("Invalid email or password.", "error")
            return redirect(url_for("login"))

        session.clear()
        session["user_id"] = user["id"]
        session["name"] = user["name"]
        flash(f"Welcome back, {user['name']}!", "success")
        return redirect(url_for("dashboard"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    user_id = session["user_id"]
    db = get_db()

    today = date.today()
    week_end = today + timedelta(days=7)

    due_this_week = db.execute(
        """
        SELECT * FROM homework
        WHERE user_id = ? AND done = 0
          AND due_date >= ? AND due_date <= ?
        ORDER BY due_date ASC
        """,
        (user_id, today.isoformat(), week_end.isoformat()),
    ).fetchall()

    all_homework = db.execute(
        "SELECT * FROM homework WHERE user_id = ? ORDER BY due_date ASC",
        (user_id,),
    ).fetchall()

    done, pending, late = get_counts(user_id)

    return render_template(
        "dashboard.html",
        due_this_week=due_this_week,
        all_homework=all_homework,
        done=done,
        pending=pending,
        late=late,
        today=today,
    )


@app.route("/add", methods=["POST"])
@login_required
def add_homework():
    subject = request.form.get("subject", "").strip()
    description = request.form.get("description", "").strip()
    due_date = request.form.get("due_date", "").strip()

    if not subject or not due_date:
        flash("Subject and due date are required.", "error")
        return redirect(url_for("dashboard"))

    try:
        datetime.strptime(due_date, "%Y-%m-%d")
    except ValueError:
        flash("Please enter a valid due date.", "error")
        return redirect(url_for("dashboard"))

    db = get_db()
    db.execute(
        """
        INSERT INTO homework (user_id, subject, description, due_date, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (session["user_id"], subject, description, due_date, datetime.now().isoformat()),
    )
    db.commit()
    flash("Homework added!", "success")
    return redirect(url_for("dashboard"))


@app.route("/toggle/<int:homework_id>", methods=["POST"])
@login_required
def toggle(homework_id):
    db = get_db()
    item = db.execute(
        "SELECT * FROM homework WHERE id = ? AND user_id = ?",
        (homework_id, session["user_id"]),
    ).fetchone()
    if item is None:
        flash("Homework not found.", "error")
        return redirect(url_for("dashboard"))

    new_status = 0 if item["done"] else 1
    db.execute(
        "UPDATE homework SET done = ? WHERE id = ?",
        (new_status, homework_id),
    )
    db.commit()
    return redirect(url_for("dashboard"))


@app.route("/delete/<int:homework_id>", methods=["POST"])
@login_required
def delete(homework_id):
    db = get_db()
    db.execute(
        "DELETE FROM homework WHERE id = ? AND user_id = ?",
        (homework_id, session["user_id"]),
    )
    db.commit()
    flash("Homework deleted.", "info")
    return redirect(url_for("dashboard"))


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
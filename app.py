
from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, abort, jsonify
)
from werkzeug.security import generate_password_hash, check_password_hash
import os
import sqlite3
import re
from datetime import datetime

from database import get_db_connection, init_db

app = Flask(__name__)
app.secret_key = os.environ.get(
    "SECRET_KEY", "eventease-dev-key-change-before-deployment"
)

init_db()

IMAGE_EXTENSIONS = ("jpg", "jpeg", "png", "webp", "svg")


# ---------------- TEMPLATE HELPERS ----------------

def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")


@app.context_processor
def template_helpers():
    def event_image(row):
        """URL of the poster for an event.

        Looks in static/images for <image>.<ext> (jpg, png, webp or svg),
        so a real photo named like the event overrides the drawn poster.
        """
        try:
            slug = row["image"] or slugify(row["name"])
        except (KeyError, IndexError):
            slug = slugify(row["name"])

        for extension in IMAGE_EXTENSIONS:
            filename = f"images/{slug}.{extension}"
            if os.path.exists(os.path.join(app.static_folder, filename)):
                return url_for("static", filename=filename)
        return url_for("static", filename="images/default.svg")

    def date_parts(value):
        try:
            parsed = datetime.strptime(value, "%Y-%m-%d")
            return parsed.strftime("%d"), parsed.strftime("%b").upper()
        except (TypeError, ValueError):
            return "--", "---"

    return dict(event_image=event_image, date_parts=date_parts)


@app.template_filter("pretty_date")
def pretty_date(value):
    try:
        return datetime.strptime(value, "%Y-%m-%d").strftime("%d %B %Y")
    except (TypeError, ValueError):
        return value


# ---------------- HOME AND EVENTS ----------------

@app.route("/")
def home():
    connection = get_db_connection()
    events = connection.execute(
        "SELECT * FROM events ORDER BY date"
    ).fetchall()
    connection.close()
    return render_template("index.html", events=events)


@app.route("/events")
def view_events():
    connection = get_db_connection()
    events = connection.execute(
        "SELECT * FROM events ORDER BY date"
    ).fetchall()
    connection.close()
    return render_template("events.html", events=events)


@app.route("/event/<int:event_id>")
def event_details(event_id):
    connection = get_db_connection()
    event = connection.execute(
        "SELECT * FROM events WHERE id = ?", (event_id,)
    ).fetchone()

    if event is None:
        connection.close()
        abort(404)

    booked = connection.execute(
        "SELECT COALESCE(SUM(tickets), 0) FROM bookings WHERE event_id = ?",
        (event_id,)
    ).fetchone()[0]
    connection.close()

    seats_left = max(event["capacity"] - booked, 0)

    return render_template(
        "event_details.html", event=event, seats_left=seats_left
    )


# ---------------- STUDENT REGISTRATION ----------------

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name or not email or not password:
            flash("Please fill in all fields.")
            return render_template("register.html")

        # Validate email format
        email_pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
        if not re.match(email_pattern, email):
            flash("Please enter a valid email address.")
            return render_template("register.html")

        if len(password) < 8:
            flash("Password must be at least 8 characters.")
            return render_template("register.html")

        connection = get_db_connection()

        try:
            connection.execute(
                """INSERT INTO users (name, email, password)
                   VALUES (?, ?, ?)""",
                (name, email, generate_password_hash(password))
            )
            connection.commit()

        except sqlite3.IntegrityError:
            connection.close()
            flash("This email is already registered.")
            return render_template("register.html")

        connection.close()
        flash("Account created! Please log in.")
        return redirect(url_for("login"))

    return render_template("register.html")


# ---------------- STUDENT LOGIN ----------------

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        connection = get_db_connection()
        user = connection.execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        ).fetchone()
        connection.close()

        if user and check_password_hash(user["password"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["role"] = user["role"]

            flash("Login successful!")
            return redirect(url_for("home"))

        flash("Invalid email or password.")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.")
    return redirect(url_for("home"))


# ---------------- EVENT BOOKING ----------------

@app.route("/book/<int:event_id>", methods=["POST"])
def book_event(event_id):
    if "user_id" not in session:
        flash("Please log in before booking an event.")
        return redirect(url_for("login"))

    try:
        tickets = int(request.form.get("tickets", "1"))
    except ValueError:
        flash("Enter a valid number of tickets.")
        return redirect(url_for("event_details", event_id=event_id))

    if tickets < 1 or tickets > 10:
        flash("You can book between 1 and 10 tickets at a time.")
        return redirect(url_for("event_details", event_id=event_id))

    connection = get_db_connection()

    event = connection.execute(
        "SELECT * FROM events WHERE id = ?", (event_id,)
    ).fetchone()

    if event is None:
        connection.close()
        abort(404)

    booked = connection.execute(
        "SELECT COALESCE(SUM(tickets), 0) FROM bookings WHERE event_id = ?",
        (event_id,)
    ).fetchone()[0]

    if booked + tickets > event["capacity"]:
        connection.close()
        flash("Sorry, there are not enough seats available.")
        return redirect(url_for("event_details", event_id=event_id))

    connection.execute(
        """INSERT INTO bookings (user_id, event_id, tickets)
           VALUES (?, ?, ?)""",
        (session["user_id"], event_id, tickets)
    )
    connection.commit()
    connection.close()

    flash("Your tickets have been booked successfully!")
    return redirect(url_for("my_bookings"))


@app.route("/my-bookings")
def my_bookings():
    if "user_id" not in session:
        flash("Please log in to view your bookings.")
        return redirect(url_for("login"))

    connection = get_db_connection()
    bookings = connection.execute("""
        SELECT bookings.id, bookings.tickets, events.id AS event_id,
               events.name, events.date, events.venue, events.price,
               events.image, events.organizer
        FROM bookings
        JOIN events ON bookings.event_id = events.id
        WHERE bookings.user_id = ?
        ORDER BY events.date
    """, (session["user_id"],)).fetchall()
    connection.close()

    return render_template("my_bookings.html", bookings=bookings)


# ---------------- ADMIN MANAGEMENT ----------------

def admin_required():
    return (
        "user_id" in session
        and session.get("role") == "admin"
    )


@app.route("/admin")
def admin_dashboard():
    if not admin_required():
        flash("Admin access required. Please log in as an administrator.")
        return redirect(url_for("login"))

    connection = get_db_connection()
    events = connection.execute("""
        SELECT events.*,
               COALESCE(
                   (SELECT SUM(tickets) FROM bookings
                    WHERE bookings.event_id = events.id), 0
               ) AS booked
        FROM events
        ORDER BY date
    """).fetchall()
    connection.close()

    return render_template("admin_dashboard.html", events=events)


@app.route("/admin/events/add", methods=["GET", "POST"])
def add_event():
    if not admin_required():
        flash("You must be an administrator to add events.")
        return redirect(url_for("login"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        date = request.form.get("date", "").strip()
        venue = request.form.get("venue", "").strip()
        description = request.form.get("description", "").strip()
        organizer = request.form.get("organizer", "").strip()
        category = request.form.get("category", "").strip()

        try:
            price = float(request.form.get("price", "0"))
            capacity = int(request.form.get("capacity", "0"))
        except ValueError:
            flash("Enter a valid price and capacity.")
            return render_template("add_event.html")

        if (
            not name or not date or not venue
            or price < 0 or capacity < 1
        ):
            flash("Enter valid details. Capacity must be at least 1.")
            return render_template("add_event.html")

        connection = get_db_connection()
        connection.execute(
            """
            INSERT INTO events
            (name, date, venue, price, capacity, description,
             organizer, category, image)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (name, date, venue, price, capacity, description,
             organizer, category, slugify(name))
        )
        connection.commit()
        connection.close()

        flash("Event added successfully!")
        return redirect(url_for("admin_dashboard"))

    return render_template("add_event.html")


# ---------------- HEALTH CHECK ----------------

@app.route("/health")
def health():
    try:
        connection = get_db_connection()
        connection.execute("SELECT 1").fetchone()
        connection.close()
        return jsonify(status="UP", database="CONNECTED"), 200
    except Exception:
        return jsonify(status="DOWN", database="DISCONNECTED"), 503


# ---------------- RUN APPLICATION ----------------

if __name__ == "__main__":
    app.run(debug=True)

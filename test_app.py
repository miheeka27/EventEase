import database


# ---------- helpers ----------

def register(client, name="Test Student", email="student@example.com",
             password="testpassword123"):
    return client.post(
        "/register",
        data={"name": name, "email": email, "password": password},
        follow_redirects=True,
    )


def login(client, email="student@example.com", password="testpassword123"):
    return client.post(
        "/login",
        data={"email": email, "password": password},
        follow_redirects=True,
    )


def add_event(name="Small Event", capacity=2):
    connection = database.get_db_connection()
    cursor = connection.execute(
        """INSERT INTO events (name, date, venue, price, capacity, description)
           VALUES (?, '2026-12-01', 'Hall', 0, ?, 'Test event')""",
        (name, capacity),
    )
    connection.commit()
    event_id = cursor.lastrowid
    connection.close()
    return event_id


def make_admin(email):
    connection = database.get_db_connection()
    connection.execute("UPDATE users SET role = 'admin' WHERE email = ?", (email,))
    connection.commit()
    connection.close()


# ---------- pages ----------

def test_home_page(client):
    assert client.get("/").status_code == 200


def test_registration_page(client):
    assert client.get("/register").status_code == 200


def test_login_page(client):
    assert client.get("/login").status_code == 200


def test_events_page_lists_college_events(client):
    response = client.get("/events")
    assert response.status_code == 200
    assert b"Techathon" in response.data
    assert b"Shazam: Football" in response.data


def test_event_details_and_missing_event(client):
    assert client.get("/event/1").status_code == 200
    assert client.get("/event/9999").status_code == 404


# ---------- health endpoint ----------

def test_health_check_success(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "UP", "database": "CONNECTED"}


def test_health_check_failure(client, monkeypatch):
    import app as app_module

    def broken_connection():
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(app_module, "get_db_connection", broken_connection)
    response = client.get("/health")
    assert response.status_code == 503
    assert response.get_json()["status"] == "DOWN"


# ---------- registration and login ----------

def test_invalid_email_registration(client):
    response = register(client, email="invalid-email")
    assert b"Please enter a valid email address." in response.data


def test_short_password_rejected(client):
    response = register(client, password="short")
    assert b"Password must be at least 8 characters." in response.data


def test_successful_registration_then_duplicate_email(client):
    assert b"Account created!" in register(client).data
    assert b"This email is already registered." in register(client).data


def test_login_success_and_wrong_password(client):
    register(client)
    assert b"Hi, Test Student!" in login(client).data
    client.get("/logout")
    assert b"Invalid email or password." in login(client, password="wrong-pass-1").data


# ---------- booking ----------

def test_booking_requires_login(client):
    response = client.post("/book/1", data={"tickets": "1"}, follow_redirects=True)
    assert b"Please log in before booking an event." in response.data


def test_successful_booking_appears_in_my_bookings(client):
    register(client)
    login(client)
    response = client.post("/book/1", data={"tickets": "2"}, follow_redirects=True)
    assert b"booked successfully" in response.data
    assert b"Shazam: Football" in client.get("/my-bookings").data


def test_booking_more_than_capacity_is_rejected(client):
    event_id = add_event(capacity=2)
    register(client)
    login(client)
    response = client.post(
        f"/book/{event_id}", data={"tickets": "3"}, follow_redirects=True
    )
    assert b"not enough seats available" in response.data


def test_invalid_ticket_count_is_rejected(client):
    register(client)
    login(client)
    response = client.post("/book/1", data={"tickets": "11"}, follow_redirects=True)
    assert b"between 1 and 10 tickets" in response.data


# ---------- admin ----------

def test_student_cannot_open_admin_dashboard(client):
    register(client)
    login(client)
    response = client.get("/admin", follow_redirects=True)
    assert b"Admin access required" in response.data


def test_admin_can_add_event(client):
    register(client, email="admin@example.com")
    make_admin("admin@example.com")
    login(client, email="admin@example.com")
    response = client.post(
        "/admin/events/add",
        data={
            "name": "Hackathon",
            "date": "2026-12-15",
            "venue": "Lab 1",
            "price": "50",
            "capacity": "80",
            "description": "24 hour hackathon",
        },
        follow_redirects=True,
    )
    assert b"Event added successfully!" in response.data
    assert b"Hackathon" in client.get("/events").data


# ---------- design / poster images ----------

def test_event_posters_are_served(client):
    import re
    page = client.get("/events").data.decode()
    posters = set(re.findall(r'src="(/static/images/[^"]+)"', page))
    assert len(posters) >= 9
    for url in posters:
        assert client.get(url).status_code == 200


def test_photo_overrides_drawn_poster(client):
    import os
    import app as app_module

    photo = os.path.join(app_module.app.static_folder, "images", "techathon.jpg")
    with open(photo, "wb") as handle:
        handle.write(b"fake-jpg")
    try:
        page = client.get("/events").data.decode()
        assert "/static/images/techathon.jpg" in page
    finally:
        os.remove(photo)


def test_sold_out_event_shows_message(client):
    event_id = add_event(name="Tiny Event", capacity=1)
    register(client)
    login(client)
    client.post(f"/book/{event_id}", data={"tickets": "1"})
    assert b"Sold out" in client.get(f"/event/{event_id}").data


def test_old_database_is_upgraded(tmp_path, monkeypatch):
    import sqlite3

    legacy = str(tmp_path / "legacy.db")
    connection = sqlite3.connect(legacy)
    connection.executescript("""
        CREATE TABLE events (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
            date TEXT NOT NULL, venue TEXT NOT NULL,
            price REAL NOT NULL DEFAULT 0,
            capacity INTEGER NOT NULL DEFAULT 100, description TEXT);
        CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, email TEXT UNIQUE, password TEXT,
            role TEXT NOT NULL DEFAULT 'student');
        CREATE TABLE bookings (id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER, event_id INTEGER, tickets INTEGER);
        INSERT INTO events (name, date, venue) VALUES
            ('Tech Fest 2026', '2026-10-20', 'Hall'),
            ('AI Workshop', '2026-10-25', 'Lab'),
            ('Cultural Night', '2026-11-05', 'Ground');
    """)
    connection.commit()
    connection.close()

    monkeypatch.setattr(database, "DATABASE", legacy)
    database.init_db()

    connection = database.get_db_connection()
    names = [row["name"] for row in connection.execute("SELECT name FROM events")]
    connection.close()
    assert "Techathon" in names
    assert "Tech Fest 2026" not in names

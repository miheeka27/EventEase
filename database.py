
import sqlite3

DATABASE = "database.db"


def get_db_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    connection = get_db_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            date TEXT NOT NULL,
            venue TEXT NOT NULL,
            price REAL NOT NULL DEFAULT 0,
            capacity INTEGER NOT NULL DEFAULT 100,
            description TEXT
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'student'
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            event_id INTEGER NOT NULL,
            tickets INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (event_id) REFERENCES events(id)
        )
    """)

    # Insert sample events only if the table is empty.
    count = connection.execute(
        "SELECT COUNT(*) FROM events"
    ).fetchone()[0]

    if count == 0:
        sample_events = [
            (
                "Tech Fest 2026",
                "2026-10-20",
                "College Auditorium",
                100,
                200,
                "Experience exciting technology events and competitions."
            ),
            (
                "AI Workshop",
                "2026-10-25",
                "Computer Lab 3",
                0,
                50,
                "Learn the basics of Artificial Intelligence."
            ),
            (
                "Cultural Night",
                "2026-11-05",
                "Main Ground",
                150,
                300,
                "Enjoy an evening of music, dance and performances."
            )
        ]

        connection.executemany("""
            INSERT INTO events
            (name, date, venue, price, capacity, description)
            VALUES (?, ?, ?, ?, ?, ?)
        """, sample_events)

    connection.commit()
    connection.close()


if __name__ == "__main__":
    init_db()
    print("EventEase database created successfully!")

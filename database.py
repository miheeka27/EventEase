
import os
import sqlite3

# Path can be overridden (Docker volume, automated tests).
DATABASE = os.environ.get("DATABASE_PATH", "database.db")


def get_db_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


# name, date, venue, price, capacity, description, organizer, category, image
# Edit the dates, venues and prices here to match the real events.
COLLEGE_EVENTS = [
    (
        "Shazam: Football", "2026-10-24", "College Ground", 50, 120,
        "The Shazam sports fest kicks off with football. Form a team, "
        "bring your boots and play for the Shazam trophy.",
        "Student Council", "Sports", "shazam-football"
    ),
    (
        "Shazam: Cricket", "2026-10-25", "College Ground", 50, 120,
        "Box-cricket knockouts at Shazam. Fast overs, big sixes and a lot "
        "of cheering from the stands.",
        "Student Council", "Sports", "shazam-cricket"
    ),
    (
        "Robotics Workshop", "2026-10-28", "Electronics Lab", 100, 60,
        "A hands-on workshop where you build and program a simple robot "
        "from scratch. No prior experience needed.",
        "ISTE", "Workshop", "robotics-workshop"
    ),
    (
        "Shazam: Badminton", "2026-10-31", "Indoor Sports Hall", 50, 64,
        "Singles and doubles badminton matches at Shazam. Bring your "
        "racket and your best smash.",
        "Student Council", "Sports", "shazam-badminton"
    ),
    (
        "Shazam: Pickleball", "2026-11-01", "Indoor Sports Hall", 50, 48,
        "The newest sport at Shazam. Easy to learn, quick to play and "
        "great fun with friends.",
        "Student Council", "Sports", "shazam-pickleball"
    ),
    (
        "Techathon", "2026-11-07", "Computer Lab 3", 150, 100,
        "A team hackathon: pick a problem, build a working prototype and "
        "pitch it to the judges.",
        "CSI", "Tech", "techathon"
    ),
    (
        "Beach Cleanup", "2026-11-08", "Juhu Beach", 0, 150,
        "Join us for a morning beach cleanup drive. Gloves and bags are "
        "provided. Let's leave the shore better than we found it.",
        "RCTSEC", "Community", "beach-cleanup"
    ),
    (
        "House of Lies", "2026-11-14", "Computer Lab 1", 100, 80,
        "A coding event with a twist: some of the clues and hints are "
        "lies. Debug, deduce and find the truth before time runs out.",
        "CodeTantra", "Tech", "house-of-lies"
    ),
    (
        "Blood Donation Drive", "2026-11-20", "College Auditorium", 0, 200,
        "Donate blood and save lives. A medical team will be on campus "
        "and refreshments are provided for all donors.",
        "NSS", "Community", "blood-donation-drive"
    ),
]

OLD_SAMPLE_NAMES = ("Tech Fest 2026", "AI Workshop", "Cultural Night")


def _upgrade_events_table(connection):
    """Add the newer columns to a database created by an older version."""
    existing = [
        row["name"]
        for row in connection.execute("PRAGMA table_info(events)")
    ]
    for column in ("organizer", "category", "image"):
        if column not in existing:
            connection.execute(
                f"ALTER TABLE events ADD COLUMN {column} TEXT"
            )


def _remove_legacy_sample_events(connection):
    """Delete the original placeholder events (only if nobody booked them)."""
    for name in OLD_SAMPLE_NAMES:
        connection.execute(
            """
            DELETE FROM events
            WHERE name = ?
              AND id NOT IN (SELECT event_id FROM bookings)
            """,
            (name,)
        )


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
            description TEXT,
            organizer TEXT,
            category TEXT,
            image TEXT
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

    _upgrade_events_table(connection)
    _remove_legacy_sample_events(connection)

    # Insert the college events only if the table is empty.
    count = connection.execute(
        "SELECT COUNT(*) FROM events"
    ).fetchone()[0]

    if count == 0:
        connection.executemany("""
            INSERT INTO events
            (name, date, venue, price, capacity, description,
             organizer, category, image)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, COLLEGE_EVENTS)
 
    connection.commit()
    connection.close()


if __name__ == "__main__":
    init_db()
    print("EventEase database created successfully!")

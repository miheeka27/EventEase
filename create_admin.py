
from database import get_db_connection

email = input("Enter the registered email for the admin account: ")
email = email.strip().lower()

connection = get_db_connection()

user = connection.execute(
    "SELECT id, name FROM users WHERE email = ?",
    (email,)
).fetchone()

if user is None:
    print("No account found. Register this email on EventEase first.")
else:
    connection.execute(
        "UPDATE users SET role = 'admin' WHERE id = ?",
        (user["id"],)
    )
    connection.commit()
    print(f"Admin access enabled for {user['name']}.")

connection.close()

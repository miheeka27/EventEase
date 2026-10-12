import os
import tempfile

# Point the app at a throw-away database BEFORE app.py is imported,
# so automated tests never touch the real database.db.
os.environ["DATABASE_PATH"] = os.path.join(
    tempfile.mkdtemp(prefix="eventease-test-"), "import-time.db"
)

import pytest

import database
from app import app as flask_app


@pytest.fixture
def client(tmp_path, monkeypatch):
    """A test client backed by a fresh, empty temporary database."""
    monkeypatch.setattr(database, "DATABASE", str(tmp_path / "test.db"))
    database.init_db()
    flask_app.config["TESTING"] = True

    with flask_app.test_client() as test_client:
        yield test_client

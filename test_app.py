
import pytest
from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True

    with app.test_client() as test_client:
        yield test_client


def test_home_page(client):
    response = client.get("/")
    assert response.status_code == 200


def test_registration_page(client):
    response = client.get("/register")
    assert response.status_code == 200


def test_login_page(client):
    response = client.get("/login")
    assert response.status_code == 200


def test_invalid_email_registration(client):
    response = client.post(
        "/register",
        data={
            "name": "Test Student",
            "email": "invalid-email",
            "password": "testpassword123"
        },
        follow_redirects=True
    )

    assert response.status_code == 200
    assert b"Please enter a valid email address." in response.data

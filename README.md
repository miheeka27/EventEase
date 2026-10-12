# EventEase - College Event Booking System

Flask + SQLite web app delivered through an Agile and DevOps pipeline
(Jira, Git/GitHub, Docker, Docker Compose, Jenkins, pytest, Nagios).

## Run locally
    python -m venv venv
    venv\Scripts\activate
    pip install -r requirements.txt
    python app.py            # http://127.0.0.1:5000
    python -m pytest -v      # 17 tests, use a temporary database

## Run with Docker
    docker compose up -d --build
    docker compose ps
    curl http://localhost:5000/health   # {"database":"CONNECTED","status":"UP"}

The SQLite file lives in the `eventease-data` Docker volume, so bookings
survive container restarts.

## Jenkins
`Jenkinsfile` stages: Checkout, Unit Tests (JUnit report), Docker Build,
Deploy, Smoke Test (`scripts/smoke_test.ps1`).

## Nagios
    docker compose -f docker-compose.monitoring.yml up -d
Open http://localhost:8081 (nagiosadmin / nagios). Checks live in
`nagios-config/eventease.cfg`.

## Make an admin
    python create_admin.py

## Event posters and photos
Each event shows a poster from `static/images/`. The drawn `.svg` posters are
placeholders. To use a real photo, save it in `static/images/` with the same
name and a `.jpg`, `.png` or `.webp` extension, e.g. `techathon.jpg`,
`shazam-football.jpg`, `beach-cleanup.jpg`, `robotics-workshop.jpg`,
`house-of-lies.jpg`, `blood-donation-drive.jpg`. Photos win over the `.svg`.
New events added by an admin look for `<event-name-with-dashes>.jpg` too.
Events are defined in `database.py` (`COLLEGE_EVENTS`): edit dates, venues
and prices there.

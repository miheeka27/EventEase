FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATABASE_PATH=/data/database.db

WORKDIR /app

# Install dependencies first so this layer is cached when only code changes
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run as an unprivileged user; /data holds the SQLite file (a volume)
RUN groupadd -g 1001 appgroup \
    && useradd -u 1001 -g appgroup -m appuser \
    && mkdir -p /data \
    && chown -R appuser:appgroup /app /data

USER appuser

EXPOSE 5000

# One worker: sample data is seeded at start-up, so avoid a seeding race
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--threads", "4", "app:app"]

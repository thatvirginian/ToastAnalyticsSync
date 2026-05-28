# ── Build stage ───────────────────────────────────────────────────────────────
FROM python:3.11-slim

# Keeps Python from buffering stdout/stderr so logs appear immediately
# in Azure Container Apps Log Analytics
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# 3. Install system dependencies for Postgres (needed for psycopg2-binary sometimes)
RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*

# Install dependencies first (layer-cached unless requirements.txt changes)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Azure Container Apps runs the container once and exits — no web server needed.
# The nightly schedule is configured in the Container App Job trigger (CRON).
CMD ["python", "main.py"]

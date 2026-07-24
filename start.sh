#!/usr/bin/env bash
set -e

echo "Starting Z-Agent FastAPI backend..."
python -m uvicorn main:app --host 127.0.0.1 --port 3001 &

echo "Starting Z-Agent Django frontend..."
cd /app/jobfrontend

python manage.py migrate --noinput || true

gunicorn jobfrontend.wsgi:application \
  --bind 0.0.0.0:8001 \
  --workers "${WEB_WORKERS:-2}" \
  --threads "${WEB_THREADS:-4}" \
  --timeout 360
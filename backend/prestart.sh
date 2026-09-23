#!/bin/bash
set -e

# Let the DB start
sleep 3

echo "Running migrations..."
alembic upgrade head

echo "Seeding database..."
python app/seed.py

echo "Starting server..."
exec "$@"

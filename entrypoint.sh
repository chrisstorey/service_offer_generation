#!/bin/sh

# Exit immediately if a command exits with a non-zero status.
set -e

# Wait for PostgreSQL to be ready
# PGHOST, PGPORT, PGUSER, PGPASSWORD, PGDATABASE are expected to be set as environment variables

echo "Waiting for PostgreSQL to be available at $PGHOST:$PGPORT..."
# Loop until pg_isready returns 0 (success)
# Timeout after a certain number of attempts to avoid infinite loop
attempts=0
max_attempts=30 # Approx 30 seconds if interval is 1s
until pg_isready -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" -q; do
  attempts=$((attempts+1))
  if [ "$attempts" -ge "$max_attempts" ]; then
    echo "PostgreSQL did not become available after $max_attempts attempts. Exiting."
    exit 1
  fi
  echo "PostgreSQL is unavailable - sleeping"
  sleep 1
done
echo "PostgreSQL is up - proceeding."

# Run database initialization (create tables)
echo "Running database schema initialization..."
python initialize_database.py
echo "Database schema initialization complete."

# Run data migration
echo "Running data migration..."
python migrate_json_to_postgres.py
echo "Data migration complete."

# Now, execute the main command (passed as arguments to this script)
# This will be `uvicorn main:app --host 0.0.0.0 --port 8000` from the Dockerfile CMD
echo "Starting application server..."
exec "$@"

#!/bin/sh

# Wait for the testing database
while ! nc -z db-test 5432; do
  echo "Waiting for the PostgreSQL database..."
  sleep 1
done
echo "Test database is ready."

# Run tests
# to enable logging from within the app while tests are running, add --log-cli-level=DEBUG after pytest
SQLALCHEMY_DATABASE_URI=${TEST_DATABASE_URL} python -m pytest -v tests 

# Wait for the database
while ! nc -z db 5432; do
  echo "Waiting for the PostgreSQL database..."
  sleep 1
done
echo "Prod database is ready."

# And set the database URL
export SQLALCHEMY_DATABASE_URI=${DATABASE_URL}

# # Check if the migrations directory exists
# if [ ! -d "migrations" ]; then
#     # Initialize the database and migrations
# fi
echo "Initializing database and migrations"
flask db init

# Run migrations
echo "Running migrations"
# Create a new migration script if models have changed
flask db migrate -m "New migration."
flask db upgrade

# Start the Flask application
echo "Starting the Flask application"
exec python app.py
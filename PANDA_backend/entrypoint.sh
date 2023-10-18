#!/bin/sh

# Check if the migrations directory exists
if [ ! -d "migrations" ]; then
    # Initialize the database and migrations
    echo "Initializing database and migrations"
    flask db init
fi

# Run migrations
echo "Running migrations"
# Create a new migration script if models have changed
flask db migrate -m "New migration."
flask db upgrade

# Start the Flask application
echo "Starting the Flask application"
exec python app.py

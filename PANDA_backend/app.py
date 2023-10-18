import os
from flask import Flask, render_template
import psycopg2
from psycopg2 import sql
from logging import getLogger, basicConfig, INFO, DEBUG

logger = getLogger(__name__)
basicConfig(level=DEBUG)

app = Flask(__name__)

# Fetch the DATABASE_URL environment variable
DATABASE_URL = os.environ.get('DATABASE_URL')

@app.route('/')
def home():
    try:
        # Connect to the database using the DATABASE_URL environment variable
        logger.debug(f"Connecting to database: {DATABASE_URL}")
        conn = psycopg2.connect(DATABASE_URL)
        logger.debug("Connected to database!")

        # Create a cursor object
        logger.debug("Creating cursor object...")
        cur = conn.cursor()
        logger.debug("Cursor object created!")

        # Execute SQL query
        logger.debug("Executing test SQL query...")
        cur.execute(sql.SQL("CREATE TABLE IF NOT EXISTS test (id serial PRIMARY KEY, num integer, data varchar);"))
        cur.execute(sql.SQL("SELECT table_name FROM information_schema.tables WHERE table_schema='public';"))
        logger.debug("SQL query executed!")

        # Fetch all tables
        tables = cur.fetchall()
        logger.debug("Fetched all tables!")

        # Close the cursor and connection
        cur.close()
        conn.close()

        return render_template('home.html', tables=tables)

    except Exception as e:
        return str(e)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)

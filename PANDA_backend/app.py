import os
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy import text

from logging import getLogger, basicConfig, INFO, DEBUG

logger = getLogger(__name__)
basicConfig(level=DEBUG)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')

db = SQLAlchemy(app)
migrate = Migrate(app, db)

class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nhs_number = db.Column(db.String(10), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    postcode = db.Column(db.String(10), nullable=False)


@app.route('/')
def home():
    try:
        conn = db.engine.connect()
        
        # Execute SQL query using SQLAlchemy
        logger.debug("Executing test SQL query...")
        result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public';"))
        logger.debug("SQL query executed!")

        # Fetch all tables
        tables = [row for row in result]
        logger.debug("Fetched all tables!")

        return render_template('home.html', tables=tables)

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return str(e)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)

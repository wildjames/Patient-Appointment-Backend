import os
from flask import Flask, request, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy import text

from logging import getLogger, basicConfig, INFO, DEBUG

logger = getLogger(__name__)
basicConfig(level=DEBUG)

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")

logger.info(f"Connecting to database: {app.config['SQLALCHEMY_DATABASE_URI']}")

db = SQLAlchemy(app)
migrate = Migrate(app, db)


class Patient(db.Model):
    nhs_number = db.Column(db.String(10), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    postcode = db.Column(db.String(10), nullable=False)

    def __repr__(self):
        return "<id {}>".format(self.id)

    def serialize(self):
        return {
            "nhs_number": self.nhs_number,
            "name": self.name,
            "date_of_birth": self.date_of_birth.isoformat(),
            "postcode": self.postcode,
        }


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


# POST /patients/ - Add a new patient
@app.route("/patients/", methods=["POST"])
def add_patient():
    data = request.get_json()
    new_patient = Patient(
        nhs_number=data["nhs_number"],
        name=data["name"],
        date_of_birth=data["date_of_birth"],
        postcode=data["postcode"],
    )
    db.session.add(new_patient)
    db.session.commit()
    return jsonify({"message": "Patient added successfully"}), 201


# GET /patients/<id>/ - Retrieve details of a specific patient
@app.route("/patients/<nhs_number>/", methods=["GET"])
def get_patient(nhs_number):
    patient = db.session.get(Patient, nhs_number)
    if patient:
        return (
            jsonify(
                {
                    "nhs_number": patient.nhs_number,
                    "name": patient.name,
                    "date_of_birth": patient.date_of_birth.isoformat(),
                    "postcode": patient.postcode,
                }
            ),
            200,
        )
    else:
        return jsonify({"message": "Patient not found"}), 404


# PUT /patients/<id>/ - Update details of a specific patient
@app.route("/patients/<nhs_number>/", methods=["PUT"])
def update_patient(nhs_number):
    patient = db.session.get(Patient, nhs_number)
    try:
        if patient:
            data: dict = request.get_json()

            # Can we update the NHS number?
            # patient.nhs_number = data["nhs_number"]

            # Default to the existing value if the new value is not provided
            fields = ["name", "date_of_birth", "postcode"]
            for field in fields:
                if field in data:
                    setattr(patient, field, data[field])

            db.session.commit()
            return jsonify({"message": "Patient updated successfully"}), 200
        else:
            return jsonify({"message": "Patient not found"}), 404
    except:
        return jsonify({"message": "Failed to parse data"}), 404


# DELETE /patients/<id>/ - Remove a patient
@app.route("/patients/<nhs_number>/", methods=["DELETE"])
def delete_patient(nhs_number):
    patient = db.session.get(Patient, nhs_number)
    if patient:
        db.session.delete(patient)
        db.session.commit()
        return jsonify({"message": "Patient deleted successfully"}), 200
    else:
        return jsonify({"message": "Patient not found"}), 404


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)

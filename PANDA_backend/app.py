import os
from flask import Flask, request, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy import text
from uuid import uuid4
from datetime import datetime, timezone

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


class Appointment(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    patient = db.Column(db.String(10), nullable=False)
    status = db.Column(db.String(50), nullable=False)
    time = db.Column(db.DateTime, nullable=False)
    duration = db.Column(db.String(10), nullable=False)
    clinician = db.Column(db.String(255), nullable=False)
    department = db.Column(db.String(255), nullable=False)
    postcode = db.Column(db.String(10), nullable=False)

    def serialize(self):
        return {
            "id": self.id,
            "patient": self.patient,
            "status": self.status,
            "time": self.time.isoformat(),
            "duration": self.duration,
            "clinician": self.clinician,
            "department": self.department,
            "postcode": self.postcode,
        }


@app.route("/")
def home():
    try:
        conn = db.engine.connect()

        # Execute SQL query using SQLAlchemy
        logger.debug("Executing test SQL query...")
        result = conn.execute(
            text(
                "SELECT table_name FROM information_schema.tables WHERE table_schema='public';"
            )
        )
        logger.debug("SQL query executed!")

        # Fetch all tables
        tables = [row for row in result]
        logger.debug("Fetched all tables!")

        return render_template("home.html", tables=tables)

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
            jsonify(patient.serialize()),
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


# POST /appointments/ - Add a new appointment
@app.route("/appointments/", methods=["POST"])
def add_appointment():
    data = request.get_json()
    new_appointment = Appointment(
        # If the ID is provided, use it, otherwise generate a new one
        id=data.get("id", str(uuid4())),
        patient=data["patient"],
        status=data["status"],
        # This parses timezones, from 2026-05-24T11:30:00+01:00
        time=datetime.fromisoformat(data["time"]),
        duration=data["duration"],
        clinician=data["clinician"],
        department=data["department"],
        postcode=data["postcode"],
    )
    db.session.add(new_appointment)
    db.session.commit()
    return jsonify({"message": "Appointment added successfully", "id": new_appointment.id}), 201


# GET /appointments/<id>/ - Retrieve details of a specific appointment
@app.route("/appointments/<id>/", methods=["GET"])
def get_appointment(id):
    appointment = db.session.get(Appointment, id)
    if appointment:
        return jsonify(appointment.serialize()), 200
    else:
        return jsonify({"message": "Appointment not found"}), 404


# PUT /appointments/<id>/ - Update details of a specific appointment
@app.route("/appointments/<id>/", methods=["PUT"])
def update_appointment(id):
    appointment = db.session.get(Appointment, id)
    if appointment:
        data = request.get_json()
        fields = ["patient", "status", "time", "duration", "clinician", "department", "postcode"]
        for field in fields:
            if field in data:
                if field == "time":
                    setattr(appointment, field, datetime.fromisoformat(data[field]))
                else:
                    setattr(appointment, field, data[field])
        db.session.commit()
        return jsonify({"message": "Appointment updated successfully"}), 200
    else:
        return jsonify({"message": "Appointment not found"}), 404


# DELETE /appointments/<id>/ - Remove an appointment
@app.route("/appointments/<id>/", methods=["DELETE"])
def delete_appointment(id):
    appointment = db.session.get(Appointment, id)
    if appointment:
        db.session.delete(appointment)
        db.session.commit()
        return jsonify({"message": "Appointment deleted successfully"}), 200
    else:
        return jsonify({"message": "Appointment not found"}), 404



if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)

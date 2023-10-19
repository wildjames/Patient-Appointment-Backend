import os
from flask import Flask, request, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy import text
from uuid import uuid4
from datetime import datetime

from utils.validators import (
    validate_nhs_number,
    format_postcode,
    is_valid_appointment_status,
    is_valid_state_change,
    check_if_missed_appointment,
)

from logging import getLogger, basicConfig, INFO, DEBUG

logger = getLogger(__name__)
basicConfig(level=DEBUG)

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("SQLALCHEMY_DATABASE_URI")

db = SQLAlchemy(app)
migrate = Migrate(app, db)


class Patient(db.Model):
    nhs_number = db.Column(db.String(10), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    postcode = db.Column(db.String(10), nullable=False)

    def __repr__(self):
        return "<Patient {}>".format(self.nhs_number)

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
    time = db.Column(db.DateTime(timezone=True), nullable=False)
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
    logger.info(f"Adding a patient record...")
    data = request.get_json()

    # First, check that that NHS number is not taken
    patient = db.session.get(Patient, data["nhs_number"])
    if patient:
        logger.info(
            f"Patient record with NHS number: {data['nhs_number']} already exists"
        )
        return jsonify({"message": "Patient already exists"}), 409

    # Validate the NHS number
    if not validate_nhs_number(data["nhs_number"]):
        logger.info(f"Invalid NHS number: {data['nhs_number']}")
        return jsonify({"message": "Invalid NHS number"}), 400

    # Format the postcode
    data["postcode"] = format_postcode(data["postcode"])
    if not data["postcode"]:
        logger.info(f"[{data['nhs_number']}] Invalid postcode: {data['postcode']}")
        return jsonify({"message": "Invalid postcode"}), 400

    # Create the new patient record
    new_patient = Patient(
        nhs_number=data["nhs_number"],
        name=data["name"],
        date_of_birth=data["date_of_birth"],
        postcode=data["postcode"],
    )
    logger.info(f"Adding patient record with NHS number: {new_patient.nhs_number}")
    db.session.add(new_patient)
    db.session.commit()
    logger.info(f"Patient {new_patient.nhs_number} added successfully")

    return jsonify({"message": "Patient added successfully"}), 201


# GET /patients/<id>/ - Retrieve details of a specific patient
@app.route("/patients/<nhs_number>/", methods=["GET"])
def get_patient(nhs_number):
    logger.info(f"Retrieving patient record with NHS number: {nhs_number}")
    patient = db.session.get(Patient, nhs_number)

    if not patient:
        logger.info(f"Patient record with NHS number: {nhs_number} not found")
        return jsonify({"message": "Patient not found"}), 404

    logger.debug(f"Found patient record with NHS number: {nhs_number}")

    return (
        jsonify(patient.serialize()),
        200,
    )


# PUT /patients/<id>/ - Update details of a specific patient
@app.route("/patients/<nhs_number>/", methods=["PUT"])
def update_patient(nhs_number):
    logger.info(f"Updating patient record with NHS number: {nhs_number}")
    patient = db.session.get(Patient, nhs_number)
    try:
        if not patient:
            logger.info(f"Patient record with NHS number: {nhs_number} not found")
            return jsonify({"message": "Patient not found"}), 404

        logger.info(f"Found patient record with NHS number: {nhs_number}")
        data: dict = request.get_json()

        # Can we update the NHS number?
        # patient.nhs_number = data["nhs_number"]

        # If we got a postcode, make sure it's valid
        if "postcode" in data:
            data["postcode"] = format_postcode(data["postcode"])

            # And if it's not, return an error
            if not data["postcode"]:
                logger.info(f"[{nhs_number}] Invalid postcode: {data['postcode']}")
                return jsonify({"message": "Invalid postcode"}), 400

        # Default to the existing value if the new value is not provided
        fields = ["name", "date_of_birth", "postcode"]
        for field in data.keys():
            if field not in fields:
                return jsonify({"message": "Invalid field"}), 400
        
        for field in fields:
            if field in data:
                logger.info(
                    f"Updating patient record field: {field} from {getattr(patient, field)} to {data[field]}"
                )
                setattr(patient, field, data[field])
            
        db.session.commit()
        logger.info(
            f"Database updated for patient record with NHS number: {nhs_number}"
        )
        return jsonify({"message": "Patient updated successfully"}), 200
    except:
        logger.info(
            f"Failed to parse data for patient record with NHS number: {nhs_number}"
        )
        return jsonify({"message": "Failed to parse data"}), 404


# DELETE /patients/<id>/ - Remove a patient
@app.route("/patients/<nhs_number>/", methods=["DELETE"])
def delete_patient(nhs_number):
    logger.info(f"Deleting patient record with NHS number: {nhs_number}")
    patient = db.session.get(Patient, nhs_number)
    if not patient:
        logger.info(f"Patient record with NHS number: {nhs_number} not found")
        return jsonify({"message": "Patient not found"}), 404

    logger.info(f"Found patient record with NHS number: {nhs_number}")
    db.session.delete(patient)
    db.session.commit()
    logger.info(f"Patient record with NHS number: {nhs_number} deleted successfully")
    return jsonify({"message": "Patient deleted successfully"}), 200


# POST /appointments/ - Add a new appointment
@app.route("/appointments/", methods=["POST"])
def add_appointment():
    logger.info(f"Adding a new appointment...")
    data = request.get_json()

    # First, check that that appointment ID is not taken
    if "id" in data:
        appointment = db.session.get(Appointment, data["id"])
        if appointment:
            logger.info(f"Appointment with ID: {data['id']} already exists")
            return jsonify({"message": "Appointment already exists"}), 409

    # Validate the NHS number
    if not validate_nhs_number(data["patient"]):
        logger.info(f"Invalid NHS number: {data['patient']}")
        return jsonify({"message": "Invalid NHS number"}), 400

    # Format the postcode
    data["postcode"] = format_postcode(data["postcode"])
    if not data["postcode"]:
        logger.info(f"[{data['id']}] Invalid postcode: {data['postcode']}")
        return jsonify({"message": "Invalid postcode"}), 400

    # Validate the appointment status
    if not is_valid_appointment_status(data["status"]):
        logger.info(f"Invalid appointment status: {data['status']}")
        return jsonify({"message": "Invalid appointment status"}), 400

    # Create the new appointment
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
    logger.info(f"Adding appointment with ID: {new_appointment.id}")

    # If the appointment date has passed, and the status is still "active" we need to set it to "missed"
    missed_appointment = check_if_missed_appointment(new_appointment)
    if missed_appointment:
        new_appointment.status = "missed"
        logger.info(
            f"[{new_appointment.id}] Patient did not get registered as attending their appointment before it passed, marking them as having missed it."
        )

    db.session.add(new_appointment)
    db.session.commit()
    logger.info(f"Appointment {new_appointment.id} added successfully")
    return (
        jsonify(
            {"message": "Appointment added successfully", "id": new_appointment.id}
        ),
        201,
    )


# GET /appointments/<id>/ - Retrieve details of a specific appointment
@app.route("/appointments/<id>/", methods=["GET"])
def get_appointment(id):
    logger.info(f"Retrieving appointment with ID: {id}")
    appointment = db.session.get(Appointment, id)
    if appointment:
        logger.info(f"Found appointment with ID: {id}")
        
        # check if appointment is missed
        missed_appointment = check_if_missed_appointment(appointment)
        if missed_appointment:
            appointment.status = "missed"
            logger.info(
                f"[{appointment.id}] Patient did not get registered as attending their appointment before it passed, marking them as having missed it."
            )
            db.session.commit()
            logger.info(f"Appointment {appointment.id} updated successfully")
        
        return jsonify(appointment.serialize()), 200
    else:
        logger.info(f"Appointment with ID: {id} not found")
        return jsonify({"message": "Appointment not found"}), 404


# PUT /appointments/<id>/ - Update details of a specific appointment
@app.route("/appointments/<id>/", methods=["PUT"])
def update_appointment(id):
    logger.info(f"Updating appointment with ID: {id}")
    appointment = db.session.get(Appointment, id)
    if not appointment:
        logger.info(f"Appointment with ID: {id} not found")
        return jsonify({"message": "Appointment not found"}), 404

    logger.info(f"Found appointment with ID: {id}")
    data = request.get_json()

    # Validate the appointment status
    if "status" in data:
        if not is_valid_appointment_status(data["status"]):
            logger.info(f"Invalid appointment status: {data['status']}")
            return jsonify({"message": "Invalid appointment status"}), 400

        # Validate the state change
        if not is_valid_state_change(appointment.status, data["status"]):
            logger.info(
                f"Invalid state change: {appointment.status} -> {data['status']}"
            )
            return jsonify({"message": "Invalid state change"}), 400

    # If we got a postcode, make sure it's valid
    if "postcode" in data:
        data["postcode"] = format_postcode(data["postcode"])

        # And if it's not, return an error
        if not data["postcode"]:
            logger.info(f"[{id}] Invalid postcode: {data['postcode']}")
            return jsonify({"message": "Invalid postcode"}), 400

    # TODO: Can we update the patient?
    if "patient" in data:
        # Validate the NHS number
        if not validate_nhs_number(data["patient"]):
            logger.info(f"Invalid NHS number: {data['patient']}")
            return jsonify({"message": "Invalid NHS number"}), 400

    # Build the modified appointment object
    # Default to the existing value if the new value is not provided. 
    fields = [
        "patient",
        "status",
        "time",
        "duration",
        "clinician",
        "department",
        "postcode",
    ]
    
    for field in data.keys():
        if field not in fields:
            return jsonify({"message": "Invalid field"}), 400
    
    for field in fields:
        if field in data:
            logger.info(
                f"[{id}] Updating appointment field: {field} from {getattr(appointment, field)} to {data[field]}"
            )
            if field == "time":
                logger.info(f"[{id}] This is a time field, so parsing the time")
                setattr(appointment, field, datetime.fromisoformat(data[field]))
            else:
                setattr(appointment, field, data[field])

    # If the appointment date has passed, and the status is still "active" we need to set it to "missed"
    # If the appointment date has passed, and the status is still "active" we need to set it to "missed"
    missed_appointment = check_if_missed_appointment(appointment)
    if missed_appointment:
        appointment.status = "missed"
        logger.info(
            f"[{appointment.id}] Patient did not get registered as attending their appointment before it passed, marking them as having missed it."
        )

    db.session.commit()
    logger.info(f"Appointment {id} updated successfully")
    return jsonify({"message": "Appointment updated successfully"}), 200


# DELETE /appointments/<id>/ - Remove an appointment
@app.route("/appointments/<id>/", methods=["DELETE"])
def delete_appointment(id):
    appointment = db.session.get(Appointment, id)
    if not appointment:
        return jsonify({"message": "Appointment not found"}), 404

    db.session.delete(appointment)
    db.session.commit()
    return jsonify({"message": "Appointment deleted successfully"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)

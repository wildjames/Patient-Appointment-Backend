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
    """
    Handles the POST request to add a new patient to the database.

    Endpoint: `/patients/`
    Method: POST

    Description:
    This endpoint is responsible for adding a new patient record to the database.
    It first checks whether the NHS number is already taken. If it is, a 409 Conflict
    response is returned. It then validates the NHS number and the postcode. If either
    is invalid, a 400 Bad Request response is returned. If all validations pass, a new
    patient record is created, added to the database, and a 201 Created response is returned.

    Request Body:
        - nhs_number (str): The NHS number of the patient, must be a 10-character string.
        - name (str): The name of the patient.
        - date_of_birth (str): The date of birth of the patient in YYYY-MM-DD format.
        - postcode (str): The postcode of the patient.

    Responses:
        - 201 Created: The patient record was successfully added to the database.
        - 400 Bad Request: Returned if the NHS number or postcode is invalid.
        - 409 Conflict: Returned if a patient with the provided NHS number already exists.

    Example Request Body:
    ```json
    {
        "nhs_number": "string (10 characters)",
        "name": "string",
        "date_of_birth": "YYYY-MM-DD",
        "postcode": "string"
    }
    ```

    Returns:
        - JSON response with a message indicating the result of the operation.
    """
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
    """
    Handles the GET request to retrieve details of a specific patient using the NHS number.

    Endpoint: `/patients/<nhs_number>/`
    Method: GET

    Description:
    This endpoint is responsible for retrieving and returning the details of a specific
    patient from the database using the NHS number. If the patient is found, a JSON object
    containing the patient's details is returned with a 200 OK response. If the patient is
    not found, a 404 Not Found response is returned.

    Path Parameters:
        - nhs_number (str): The NHS number of the patient to retrieve. Must be a 10-character string.

    Responses:
        - 200 OK: Successfully retrieved the patient details. The patient's details are returned
                in the response body in JSON format.
        - 404 Not Found: Returned if no patient record is found with the provided NHS number.

    Returns:
        - JSON response containing the patient's details if found.

    Example Response Body:
    ```json
    {
        "nhs_number": "string (10 characters)",
        "name": "string",
        "date_of_birth": "YYYY-MM-DD",
        "postcode": "string"
    }
    ```
    """
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
    """
    Handles the PUT request to update details of a specific patient using the NHS number.

    Endpoint: `/patients/<nhs_number>/`
    Method: PUT

    Description:
    This endpoint is responsible for updating the details of a specific patient in the
    database using the NHS number. All fields in the request body are optional. If the
    patient is found and the provided data is valid, the patient's details are updated,
    and a 200 OK response is returned. If the patient is not found or if any provided
    data is invalid, appropriate error responses are returned.

    Path Parameters:
        - nhs_number (str): The NHS number of the patient to update. Must be a 10-character string.

    Request Body:
        - name (str, optional): The new name of the patient.
        - date_of_birth (str, optional): The new date of birth of the patient in YYYY-MM-DD format.
        - postcode (str, optional): The new postcode of the patient.

    Responses:
        - 200 OK: Successfully updated the patient details. A success message is returned in the response body.
        - 400 Bad Request: Returned if any provided field is invalid, or the date of birth or postcode is invalid.
        - 404 Not Found: Returned if no patient record is found with the provided NHS number.

    Returns:
        - JSON response with a message indicating the result of the operation.

    Example Request Body (all fields are optional):
    ```json
    {
        "name": "string",
        "date_of_birth": "YYYY-MM-DD",
        "postcode": "string"
    }
    ```
    """

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
    """
    Handles the DELETE request to remove a specific patient using the NHS number.

    Endpoint: `/patients/<nhs_number>/`
    Method: DELETE

    Description:
    This endpoint is responsible for deleting a specific patient record from the database
    using the NHS number. If the patient is found, the record is deleted, and a 200 OK
    response along with a success message is returned. If the patient is not found, a
    404 Not Found response is returned.

    Path Parameters:
        - nhs_number (str): The NHS number of the patient to delete. Must be a 10-character string.

    Responses:
        - 200 OK: Successfully deleted the patient record. A success message is returned in the response body.
        - 404 Not Found: Returned if no patient record is found with the provided NHS number.

    Returns:
        - JSON response with a message indicating the result of the operation.
        - HTTP status code indicating the result of the operation.

    """
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
    """
    Handles the POST request to add a new appointment to the database.

    Endpoint: `/appointments/`
    Method: POST

    Description:
    This endpoint is responsible for adding a new appointment record to the database.
    It performs various validations such as checking whether the appointment ID, if provided,
    is already taken, validating the NHS number, formatting and validating the postcode, and
    validating the appointment status. If all validations pass, a new appointment record is
    created, added to the database, and a 201 Created response is returned.

    Request Body:
        - id (str, optional): The ID of the appointment. If not provided, a new one is generated.
        - patient (str): The NHS number of the patient.
        - status (str): The status of the appointment.
        - time (str): The date and time of the appointment in YYYY-MM-DDTHH:MM:SS+TZ format.
        - duration (str): The duration of the appointment.
        - clinician (str): The clinician for the appointment.
        - department (str): The department where the appointment is scheduled.
        - postcode (str): The postcode for the appointment location.

    Responses:
        - 201 Created: The appointment record was successfully added to the database.
        - 400 Bad Request: Returned if there is an invalid NHS number, postcode, or appointment status.
        - 409 Conflict: Returned if an appointment with the provided ID already exists.

    Returns:
        - JSON response with a message indicating the result of the operation and the ID of the created appointment.
        - HTTP status code indicating the result of the operation.

    Example Request Body:
    ```json
    {
        "id": "string (optional)",
        "patient": "string (NHS number)",
        "status": "string",
        "time": "YYYY-MM-DDTHH:MM:SS+TZ",
        "duration": "string",
        "clinician": "string",
        "department": "string",
        "postcode": "string"
    }
    ```
    """
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
    """
    Handles the GET request to retrieve details of a specific appointment using the appointment ID.

    Endpoint: `/appointments/<id>/`
    Method: GET

    Description:
    This endpoint is responsible for retrieving and returning the details of a specific
    appointment from the database using the appointment ID. If the appointment is found,
    a JSON object containing the appointment's details is returned with a 200 OK response.
    If the appointment is not found, a 404 Not Found response is returned. Additionally,
    it checks whether an active appointment is missed and updates the status if necessary.

    Path Parameters:
        - id (str): The ID of the appointment to retrieve.

    Responses:
        - 200 OK: Successfully retrieved the appointment details. The appointment's details
                are returned in the response body in JSON format.
        - 404 Not Found: Returned if no appointment record is found with the provided ID.

    Returns:
        - JSON response containing the appointment's details if found.
        - HTTP status code indicating the result of the operation.

    Example Response Body:
    ```json
    {
        "id": "string",
        "patient": "string (NHS number)",
        "status": "string",
        "time": "YYYY-MM-DDTHH:MM:SS+TZ",
        "duration": "string",
        "clinician": "string",
        "department": "string",
        "postcode": "string"
    }
    ```
    """
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
    """
    Handles the PUT request to update details of a specific appointment using the appointment ID.

    Endpoint: `/appointments/<id>/`
    Method: PUT

    Description:
    This endpoint is responsible for updating the details of a specific appointment in the
    database using the appointment ID. It performs various validations such as checking
    whether the appointment ID exists, validating the NHS number, formatting and validating
    the postcode, and validating the appointment status and state change. If all validations
    pass, the appointment details are updated, and a 200 OK response is returned.

    Path Parameters:
        - id (str): The ID of the appointment to update.

    Request Body:
        - patient (str, optional): The NHS number of the patient.
        - status (str, optional): The status of the appointment.
        - time (str, optional): The date and time of the appointment in YYYY-MM-DDTHH:MM:SS+TZ format.
        - duration (str, optional): The duration of the appointment, e.g. 1h30m, or 1h, or 30m.
        - clinician (str, optional): The clinician for the appointment.
        - department (str, optional): The department where the appointment is scheduled.
        - postcode (str, optional): The postcode for the appointment location.

    Responses:
        - 200 OK: Successfully updated the appointment details. A success message is returned in the response body.
        - 400 Bad Request: Returned if there is an invalid field, NHS number, postcode, appointment status, or state change.
        - 404 Not Found: Returned if no appointment record is found with the provided ID.

    Returns:
        - JSON response with a message indicating the result of the operation.

    Example Request Body:
    ```json
    {
        "patient": "string (NHS number)",
        "status": "string",
        "time": "YYYY-MM-DDTHH:MM:SS+TZ",
        "duration": "HHhMMm",
        "clinician": "string",
        "department": "string",
        "postcode": "string"
    }
    ```
    """
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
            f"[{id}] Patient did not get registered as attending their appointment before it passed, marking them as having missed it."
        )

    db.session.commit()
    logger.info(f"Appointment {id} updated successfully")
    return jsonify({"message": "Appointment updated successfully"}), 200


# DELETE /appointments/<id>/ - Remove an appointment
@app.route("/appointments/<id>/", methods=["DELETE"])
def delete_appointment(id):
    """
    Handles the DELETE request to remove a specific appointment using the appointment ID.

    Endpoint: `/appointments/<id>/`
    Method: DELETE

    Description:
    This endpoint is responsible for deleting a specific appointment record from the database
    using the appointment ID. If the appointment is found, the record is deleted, and a 200 OK
    response along with a success message is returned. If the appointment is not found, a
    404 Not Found response is returned.

    Path Parameters:
        - id (str): The ID of the appointment to delete.

    Responses:
        - 200 OK: Successfully deleted the appointment record. A success message is returned in the response body.
        - 404 Not Found: Returned if no appointment record is found with the provided ID.

    Returns:
        - JSON response with a message indicating the result of the operation.
    """
    appointment = db.session.get(Appointment, id)
    if not appointment:
        return jsonify({"message": "Appointment not found"}), 404

    db.session.delete(appointment)
    db.session.commit()
    return jsonify({"message": "Appointment deleted successfully"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)

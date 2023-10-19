import pytest
from datetime import datetime
import os
import json

from ..app import app, db, Appointment


# Setup Flask's test client
@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("SQLALCHEMY_DATABASE_URI")
    client = app.test_client()

    # Setup the application and database for testing
    with app.app_context():
        db.create_all()

    yield client

    # Teardown the database after testing
    with app.app_context():
        db.drop_all()


def test_add_appointment(client):
    with open("tests/example-appointments.json", "r") as f:
        example_appointments = json.load(f)

    for example_appointment in example_appointments:
        with app.app_context():
            response = client.post("/appointments/", json=example_appointment)
            assert response.status_code == 201
            assert response.get_json()["message"] == "Appointment added successfully"

            # Check that the appointment was added to the database
            appointment = db.session.get(Appointment, example_appointment["id"])
            assert appointment is not None
            assert appointment.id == example_appointment["id"]
            assert appointment.patient == example_appointment["patient"]
            assert appointment.status == example_appointment["status"]
            assert appointment.time == datetime.fromisoformat(
                example_appointment["time"]
            )
            assert appointment.duration == example_appointment["duration"]
            assert appointment.clinician == example_appointment["clinician"]
            assert appointment.department == example_appointment["department"]
            assert appointment.postcode == example_appointment["postcode"]

def test_add_appointment_no_id(client):
    with open("tests/example-appointments.json", "r") as f:
        example_appointments = json.load(f)

    for example_appointment in example_appointments:
        with app.app_context():
            example_appointment.pop("id")
            response = client.post("/appointments/", json=example_appointment)
            assert response.status_code == 201
            assert response.get_json()["message"] == "Appointment added successfully"
            assert response.get_json()["id"] is not None
            
            appt_id = response.get_json()["id"]

            # Check that the appointment was added to the database
            appointment = db.session.get(Appointment, appt_id)
            assert appointment is not None
            assert appointment.patient == example_appointment["patient"]
            assert appointment.status == example_appointment["status"]
            assert appointment.time == datetime.fromisoformat(
                example_appointment["time"]
            )
            assert appointment.duration == example_appointment["duration"]
            assert appointment.clinician == example_appointment["clinician"]
            assert appointment.department == example_appointment["department"]
            assert appointment.postcode == example_appointment["postcode"]


def test_get_appointment(client):
    with open("tests/example-appointments.json", "r") as f:
        example_appointments = json.load(f)

    for example_appointment in example_appointments:
        with app.app_context():
            # Add an appointment to the database
            appointment = Appointment(**example_appointment)

            db.session.add(appointment)
            db.session.commit()

            response = client.get(f'/appointments/{example_appointment["id"]}/')
            assert response.status_code == 200
            assert response.get_json()["id"] == example_appointment["id"]


def test_update_appointment(client):
    with open("tests/example-appointments.json", "r") as f:
        example_appointments = json.load(f)

    for example_appointment in example_appointments:
        with app.app_context():
            # Add an appointment to the database
            appointment = Appointment(**example_appointment)

            db.session.add(appointment)
            db.session.commit()

            # Partial update: Only update the status
            response = client.put(
                f"/appointments/{appointment.id}/",
                json={
                    "status": "Updated Status",
                },
            )
            assert response.status_code == 200
            assert response.get_json()["message"] == "Appointment updated successfully"


def test_bad_update_appointment(client):
    with open("tests/example-appointments.json", "r") as f:
        example_appointments = json.load(f)

    for example_appointment in example_appointments:
        with app.app_context():
            # Non-existent appointment update
            response = client.put(
                f"/appointments/non_existent_id/",
                json={
                    "status": "Non-Existent Appointment",
                },
            )
            assert response.status_code == 404


def test_delete_appointment(client):
    with open("tests/example-appointments.json", "r") as f:
        example_appointments = json.load(f)

    for example_appointment in example_appointments:
        with app.app_context():
            # Add an appointment to the database
            appointment = Appointment(**example_appointment)

            db.session.add(appointment)
            db.session.commit()

            # Delete the appointment
            response = client.delete(f"/appointments/{appointment.id}/")
            assert response.status_code == 200
            assert response.get_json()["message"] == "Appointment deleted successfully"

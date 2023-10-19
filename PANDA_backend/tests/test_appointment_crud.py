import pytest
from datetime import datetime
import os
import json
import ukpostcodeparser

from ..app import app, db, Appointment


def format_postcode(postcode):
    """Leverage the ukpostcodeparser library to coerce a postcode into the correct format.

    Returns the postcode in the format "AA11 1AA" or None if the postcode is invalid.
    
    I know this works, and I mirror it here so that if the validators change, we are not propagating
    a bug to the tests.
    """
    try:
        postcode_chunks = ukpostcodeparser.parse_uk_postcode(postcode, False, True)
    except:
        return None

    return " ".join(postcode_chunks)


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
            # assert appointment.status == example_appointment["status"]
            assert appointment.time == datetime.fromisoformat(
                example_appointment["time"]
            )
            assert appointment.duration == example_appointment["duration"]
            assert appointment.clinician == example_appointment["clinician"]
            assert appointment.department == example_appointment["department"]
            assert appointment.postcode == format_postcode(
                example_appointment["postcode"]
            )


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
            # assert appointment.status == example_appointment["status"]
            assert appointment.time == datetime.fromisoformat(
                example_appointment["time"]
            )
            assert appointment.duration == example_appointment["duration"]
            assert appointment.clinician == example_appointment["clinician"]
            assert appointment.department == example_appointment["department"]
            assert appointment.postcode == format_postcode(example_appointment["postcode"])


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

            assert response.get_json() is not None

            fetched_appointment = response.get_json()
            assert fetched_appointment["id"] == example_appointment["id"]
            assert fetched_appointment["patient"] == example_appointment["patient"]
            # assert fetched_appointment["status"] == example_appointment["status"]
            assert datetime.fromisoformat(fetched_appointment["time"]) == datetime.fromisoformat(example_appointment["time"])
            assert fetched_appointment["duration"] == example_appointment["duration"]
            assert fetched_appointment["clinician"] == example_appointment["clinician"]
            assert (
                fetched_appointment["department"] == example_appointment["department"]
            )
            assert fetched_appointment["postcode"] == example_appointment["postcode"]


def test_get_missed_appointment(client):
    example_appointment = {
        "patient": "1953262716",
        "status": "active",  # The appointment is uploaded as active
        "time": "2015-06-04T16:30:00+01:00",  # Some time in the past
        "duration": "1h",
        "clinician": "Bethany Rice-Hammond",
        "department": "oncology",
        "postcode": "IM2N 4LG",
        "id": "01542f70-929f-4c9a-b4fa-e672310d7e78",
    }

    with app.app_context():
        # Add an appointment to the database
        appointment = Appointment(**example_appointment)

        db.session.add(appointment)
        db.session.commit()

        response = client.get(f'/appointments/{example_appointment["id"]}/')
        assert response.status_code == 200
        assert response.get_json()["id"] == example_appointment["id"]
        assert response.get_json()["status"] == "missed"


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
                    "status": "attended",
                },
            )
            assert response.status_code == 200
            assert response.get_json()["message"] == "Appointment updated successfully"

            # Test that the status was updated
            appointment = db.session.get(Appointment, appointment.id)
            assert appointment.status == "attended"


def test_bad_update_appointment(client):
    example_appointment = {
        "patient": "1953262716",
        "status": "active",
        "time": "2025-06-04T16:30:00+01:00",
        "duration": "1h",
        "clinician": "Bethany Rice-Hammond",
        "department": "oncology",
        "postcode": "IM2N 4LG",
        "id": "01542f70-929f-4c9a-b4fa-e672310d7e78",
    }

    with app.app_context():

        # Add the example appointment to the database
        appointment = Appointment(**example_appointment)
        db.session.add(appointment)
        db.session.commit()

        # Non-existent appointment update
        response = client.put(
            f"/appointments/non_existent_id/",
            json={
                "status": "Bad Status",
            },
        )
        assert response.status_code == 404

        # Bad status update
        response = client.put(
            f"/appointments/{example_appointment['id']}/",
            json={
                "status": "Bad Status",
            },
        )
        assert response.status_code == 400

        # Invalid state change
        # first the client misses their appointment
        response = client.put(
            f"/appointments/{appointment.id}/",
            json={
                "status": "cancelled",
            },
        )
        assert response.status_code == 200
        # Then, they try to update their status to active
        response = client.put(
            f"/appointments/{appointment.id}/",
            json={
                "status": "active",
            },
        )
        assert response.status_code == 400


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

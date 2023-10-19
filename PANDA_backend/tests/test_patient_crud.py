import pytest
from datetime import date
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os
import json

from ..app import app, db, Patient
from ..utils.validators import format_postcode

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


def test_add_patient(client):
    with open("tests/example-patients.json", "r") as f:
        example_patients = json.load(f)

    for example_patient in example_patients:
        with app.app_context():
            response = client.post("/patients/", json=example_patient)
            assert response.status_code == 201
            assert response.get_json()["message"] == "Patient added successfully"

            # Check that the patient was added to the database
            patient = db.session.get(Patient, example_patient["nhs_number"])
            assert patient is not None
            assert patient.nhs_number == example_patient["nhs_number"]
            assert patient.name == example_patient["name"]
            assert patient.date_of_birth == date.fromisoformat(
                example_patient["date_of_birth"]
            )
            assert patient.postcode == format_postcode(example_patient["postcode"])


def test_get_patient(client):
    with open("tests/example-patients.json", "r") as f:
        example_patients = json.load(f)

    # # Pick a random patient from the example patients
    # example_patient = random.choice(example_patients)

    for example_patient in example_patients:
        with app.app_context():
            # Add a patient to the database
            patient = Patient(**example_patient)

            db.session.add(patient)
            db.session.commit()

            response = client.get(f'/patients/{example_patient["nhs_number"]}/')
            assert response.status_code == 200
            assert response.get_json()["nhs_number"] == example_patient["nhs_number"]
            assert response.get_json()["name"] == example_patient["name"]
            assert (
                response.get_json()["date_of_birth"] == example_patient["date_of_birth"]
            )
            assert response.get_json()["postcode"] == format_postcode(example_patient["postcode"])


def test_update_patient(client):
    with open("tests/example-patients.json", "r") as f:
        example_patients = json.load(f)

    for example_patient in example_patients:
        with app.app_context():
            # Add a patient to the database
            patient = Patient(**example_patient)

            db.session.add(patient)
            db.session.commit()

            # Partial update: Only update the name
            response = client.put(
                f"/patients/{patient.nhs_number}/",
                json={
                    "name": "Updated Name",
                },
            )
            assert response.status_code == 200, patient.nhs_number
            assert response.get_json()["message"] == "Patient updated successfully"
            
            updated_patient = db.session.get(Patient, patient.nhs_number)
            assert updated_patient.name == "Updated Name"

            # Update the patient details
            response = client.put(
                f"/patients/{patient.nhs_number}/",
                json={
                    "name": "Another Name",
                    "date_of_birth": "1971-06-02",
                    "postcode": "AB123CD", # Should be formatted to "AB12 3CD"
                },
            )
            assert response.status_code == 200
            assert response.get_json()["message"] == "Patient updated successfully"
            
            # Check actual update in the database
            updated_patient = db.session.get(Patient, patient.nhs_number)
            assert updated_patient.name == "Another Name"
            assert updated_patient.date_of_birth == date.fromisoformat("1971-06-02")
            assert updated_patient.postcode == "AB12 3CD"


def test_bad_update_patient(client):
    with open("tests/example-patients.json", "r") as f:
        example_patients = json.load(f)

    for example_patient in example_patients:
        with app.app_context():
            # Add a patient to the database
            patient = Patient(**example_patient)

            db.session.add(patient)
            db.session.commit()

            # Non-existent patient update
            response = client.put(
                f"/patients/non_existent_nhs_number/",
                json={
                    "name": "Non-Existent Patient",
                },
            )
            assert (
                response.status_code == 404
            )


def test_delete_patient(client):
    with open("tests/example-patients.json", "r") as f:
        example_patients = json.load(f)

    for example_patient in example_patients:
        with app.app_context():
            # Add a patient to the database
            patient = Patient(**example_patient)

            db.session.add(patient)
            db.session.commit()

            # Delete the patient
            response = client.delete(f"/patients/{patient.nhs_number}/")
            assert response.status_code == 200
            assert response.get_json()["message"] == "Patient deleted successfully"

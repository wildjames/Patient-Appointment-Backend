import requests
import json
import random

BASE_URL = "http://127.0.0.1:5000/"  # Adjust the URL if your app is hosted elsewhere


def load_example_data(filename):
    with open(filename, "r") as file:
        return json.load(file)


def get_random_data(data_list):
    return random.choice(data_list)


### Patients ###


def get_patient_details():
    fields = ["nhs_number", "name", "date_of_birth", "postcode"]
    patient_data = {}
    for field in fields:
        patient_data[field] = input(f"Enter {field.replace('_', ' ')}: ")
    return patient_data


def add_patient(patient_data):
    response = requests.post(f"{BASE_URL}patients/", json=patient_data)
    print(response)
    print(response.json())


def get_patient(nhs_number):
    response = requests.get(f"{BASE_URL}patients/{nhs_number}/")
    print(response.json())


def update_patient(nhs_number):
    field = input("Which field do you want to update (name, date_of_birth, postcode)? ")
    value = input(f"Enter new value for {field}: ")
    response = requests.put(f"{BASE_URL}patients/{nhs_number}/", json={field: value})
    print(response.json())


def delete_patient(nhs_number):
    response = requests.delete(f"{BASE_URL}patients/{nhs_number}/")
    print(response.json())


### Appointments ###


def get_appointment_details():
    fields = [
        "patient",
        "status",
        "time",
        "duration",
        "clinician",
        "department",
        "postcode",
    ]
    appointment_data = {}
    for field in fields:
        appointment_data[field] = input(f"Enter {field.replace('_', ' ')}: ")
    return appointment_data


def add_appointment(appointment_data):
    response = requests.post(f"{BASE_URL}appointments/", json=appointment_data)
    print(response)
    print(response.json())


def get_appointment(appointment_id):
    response = requests.get(f"{BASE_URL}appointments/{appointment_id}/")
    print(response.json())


def update_appointment(appointment_id):
    field = input(
        "Which field do you want to update (patient, status, time, duration, clinician, department, postcode)? "
    )
    value = input(f"Enter new value for {field}: ")
    response = requests.put(
        f"{BASE_URL}appointments/{appointment_id}/", json={field: value}
    )
    print(response.json())


def delete_appointment(appointment_id):
    response = requests.delete(f"{BASE_URL}appointments/{appointment_id}/")
    print(response.json())


### Main ###

if __name__ == "__main__":
    while True:
        entity = input(
            "Do you want to manage (1) Patients or (2) Appointments? (Anything else to exit) "
        )

        # Choose which functions are relevant
        if entity in ["1", "2"]:
            action = input(
                "Do you want to (1) Fetch, (2) Create, (3) Update, or (4) Delete? (Anything else to exit) "
            )

            if entity == "1":
                entity_name, example_file = (
                    "patient",
                    "PANDA_backend/tests/example-patients.json",
                )
                get_func, add_func, update_func, delete_func = (
                    get_patient,
                    add_patient,
                    update_patient,
                    delete_patient,
                )
            else:
                entity_name, example_file = (
                    "appointment",
                    "PANDA_backend/tests/example-appointments.json",
                )
                get_func, add_func, update_func, delete_func = (
                    get_appointment,
                    add_appointment,
                    update_appointment,
                    delete_appointment,
                )

            # Choose which function to run
            if action == "1":
                entity_id = input(f"Enter ID of {entity_name} to fetch: ")
                get_func(entity_id)

            elif action == "2":
                choice = input(
                    f"Do you want to (1) Load random example, or (2) Manually define {entity_name}? "
                )

                if choice == "1":
                    entity_data = get_random_data(load_example_data(example_file))
                    print(f"Loaded {entity_name}: ")
                    for key, value in entity_data.items():
                        print(f"  {key.capitalize()}: {value}")
                    print("")

                elif choice == "2":
                    entity_data = (
                        get_patient_details()
                        if entity == "1"
                        else get_appointment_details()
                    )

                add_func(entity_data)

            elif action == "3":
                entity_id = input(f"Enter ID of {entity_name} to update: ")
                update_func(entity_id)

            elif action == "4":
                entity_id = input(f"Enter ID of {entity_name} to delete: ")
                delete_func(entity_id)

            else:
                exit()

            print("")
            print("")
            print("")
        else: 
            exit()

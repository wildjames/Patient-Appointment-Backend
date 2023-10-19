import requests
import json
import random

BASE_URL = "http://127.0.0.1:5000/patients/"  # Adjust the URL if your app is hosted elsewhere


def load_example_patients():
    with open("PANDA_backend/tests/example-patients.json", "r") as file:
        return json.load(file)


def get_random_patient(example_patients):
    return random.choice(example_patients)


def get_patient_details():
    fields = ["nhs_number", "name", "date_of_birth", "postcode"]
    patient_data = {}
    for field in fields:
        patient_data[field] = input(f"Enter {field.replace('_', ' ')}: ")
    return patient_data


def add_patient(patient_data):
    response = requests.post(BASE_URL, json=patient_data)
    print(response)
    print(response.json())


def get_patient(nhs_number):
    response = requests.get(f"{BASE_URL}{nhs_number}/")
    print(response.json())


def update_patient(nhs_number):
    field = input("Which field do you want to update (name, date_of_birth, postcode)? ")
    value = input(f"Enter new value for {field}: ")
    response = requests.put(f"{BASE_URL}{nhs_number}/", json={field: value})
    print(response.json())


def delete_patient(nhs_number):
    response = requests.delete(f"{BASE_URL}{nhs_number}/")
    print(response.json())


if __name__ == "__main__":
    while True:
        action = input("Do you want to (1) Fetch, (2) Create, (3) Update, or (4) Delete the patient? (Anything else to exit) ")

        if action == "1":
            nhs_number = input("Enter NHS number of patient to fetch: ")
            get_patient(nhs_number)

        elif action == "2":
            example_patients = load_example_patients()

            choice = input("Do you want to (1) Load random example, or (2) Manually define patient? ")

            if choice == "1":
                patient_data = get_random_patient(example_patients)
                print("Loaded patient: ")
                print(f"  NHS number: {patient_data['nhs_number']}")
                print(f"  Name: {patient_data['name']}")
                print(f"  Date of birth: {patient_data['date_of_birth']}")
                print(f"  Postcode: {patient_data['postcode']}")
                print("")
                
            elif choice == "2":
                patient_data = get_patient_details()
                
            add_patient(patient_data)
            
        elif action == "3":
            nhs_number = input("Enter NHS number of patient to update: ")
            update_patient(nhs_number)
        
        elif action == "4":
            nhs_number = input("Enter NHS number of patient to delete: ")
            delete_patient(nhs_number)
            
        else:
            exit()
            
        print("")
        print("")
        print("")

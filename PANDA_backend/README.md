# PANDA backend

This is a simple Flask app, which provides the following operations:

### Patients

- **POST** `/patients/`: Add a new patient.
- **GET** `/patients/<id>/`: Retrieve details of a specific patient.
- **PUT** `/patients/<id>/`: Update details of a specific patient.
- **DELETE** `/patients/<id>/`: Remove a patient.

### Appointments

- **POST** `/appointments/`: Schedule a new appointment.
- **GET** `/appointments/<id>/`: Retrieve details of a specific appointment.
- **PUT** `/appointments/<id>/`: Update details of a specific appointment.
- **DELETE** `/appointments/<id>/`: Cancel an appointment.

Detailed information on how to interact with these endpoints is given [below](#api-usage)

# PANDA Application Installation and Configuration Guide

This guide gives steps for how to set up and run the PANDA (Patient Appointment Network Data Application) Flask application, ensuring it communicates effectively with a PostgreSQL database.

## **1. Setting Up the Flask Application**

The application requires some Python packages to run. Install these packages:

```bash
pip install -r requirements.txt
```

## **2. Running the Flask Application**

### **Development Mode**

You can run the flask server in development mode using the command:

```bash
python3 app.py
```

**Note**: Running the application in development mode is suitable for testing and debugging, but lacks the kind of scaling features one would need for a production environment.

### **Production Mode**

For a production environment, it is generally recommended to use a WSGI server like `Gunicorn` or `uWSGI`. For example, using Gunicorn (**untested**):

```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## **3. Database Configuration**

The application requires access to a PostgreSQL database, the credentials of which are provided using the `DATABASE_URL` environment variable.
Create `SQLALCHEMY_DATABASE_URI` and assign the database connection string to it, for example:

```bash
export SQLALCHEMY_DATABASE_URI=postgresql://panda_user:panda_pass@db/panda_db
```

Or, define it in-line

```bash
SQLALCHEMY_DATABASE_URI=postgresql://panda_user:panda_pass@db/panda_db python3 app.py
```

This environment variable allows the application to connect to the PostgreSQL database using the provided username, password, and database name.

## **4. Testing**

There are pytests for this codebase. Currently, these are designed to run before the app starts within the docker compose stack. However, running them outside the stack messes with the imports. To hack around this, you will need to add the repository to your `PYTHONPATH`.

```bash
export PYTHONPATH="${PYTHONPATH}:/path/to/PANDA/PANDA/backend"
```

Then, ensure that the `SQLALCHEMY_DATABASE_URI` environment variable is set, and points to a valid database, and run:

```bash
pytest -v tests
```

# API usage

Note that whenever an interaction with an appointment occurs, the server will check if the appointment as finished. If the patient is not marked as having attended the appointment by the end of the booking, they are automatically marked as having missed it.

The API responds with JSON formatted data, and expects requests that supply data to give it as JSON as well.

## 1. **Home Page**

- **Endpoint:** `/`
- **Method:** `GET`
- **Description:** Retrieves and displays all the tables in the database. This is solely for testing purposes, to check that a proper database connection is being made.
- **Responses:**
  - **200 OK:** Successfully retrieved the tables.
  - **Error:** An error message is returned.

## 2. **Patients**

### a. **Add a New Patient**

      - **Endpoint:** `/patients/`
      - **Method:** `POST`
      - **Description:** Adds a new patient to the database.
      - **Request Body:**
        ```json
        {
            "nhs_number": "string (10 characters)",
            "name": "string",
            "date_of_birth": "YYYY-MM-DD",
            "postcode": "string"
        }
        ```
      - **Responses:**
        - **201 Created:** Patient added successfully.
        - **400 Bad Request:** Invalid NHS number or postcode.
        - **409 Conflict:** Patient already exists.

### b. **Retrieve a Specific Patient**

      - **Endpoint:** `/patients/<nhs_number>/`
      - **Method:** `GET`
      - **Description:** Retrieves details of a specific patient using the NHS number. Returns JSON data.
      - **Response Body:**
        ```json
        {
            "nhs_number": "string (10 characters)",
            "name": "string",
            "date_of_birth": "YYYY-MM-DD",
            "postcode": "string"
        }
        ```
      - **Responses:**
        - **200 OK:** Successfully retrieved the patient details.
        - **404 Not Found:** Patient not found.

### c. **Update a Specific Patient**

      - **Endpoint:** `/patients/<nhs_number>/`
      - **Method:** `PUT`
      - **Description:** Updates details of a specific patient using the NHS number. Note that all fields are optional.
      - **Request Body:**
        ```json
        {
            "name": "string",
            "date_of_birth": "YYYY-MM-DD",
            "postcode": "string"
        }
        ```
      - **Responses:**
        - **200 OK:** Patient updated successfully.
        - **400 Bad Request:** Invalid field, date of birth, or postcode.
        - **404 Not Found:** Patient not found.

### d. **Delete a Specific Patient**

      - **Endpoint:** `/patients/<nhs_number>/`
      - **Method:** `DELETE`
      - **Description:** Deletes a specific patient using the NHS number.
      - **Responses:**
        - **200 OK:** Patient deleted successfully.
        - **404 Not Found:** Patient not found.

## 3. **Appointments**

### a. **Add a New Appointment**

      - **Endpoint:** `/appointments/`
      - **Method:** `POST`
      - **Description:** Adds a new appointment to the database.
      - **Request Body:**
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
      - **Responses:**
        - **201 Created:** Appointment added successfully.
        - **400 Bad Request:** Invalid NHS number, postcode, or appointment status.
        - **409 Conflict:** Appointment already exists.

### b. **Retrieve a Specific Appointment**

      - **Endpoint:** `/appointments/<id>/`
      - **Method:** `GET`
      - **Description:** Retrieves details of a specific appointment using the appointment ID.
      - **Response Body:**
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
      - **Responses:**
        - **200 OK:** Successfully retrieved the appointment details.
        - **404 Not Found:** Appointment not found.

### c. **Update a Specific Appointment**

      - **Endpoint:** `/appointments/<id>/`
      - **Method:** `PUT`
      - **Description:** Updates details of a specific appointment using the appointment ID. Note that all fields are optional.
      - **Request Body:**
        ```json
        {
            "patient": "string (NHS number)",
            "status": "string",
            "time": "YYYY-MM-DDTHH:MM:SS+TZ",
            "duration": "string",
            "clinician": "string",
            "department": "string",
            "postcode": "string"
        }
        ```
      - **Responses:**
        - **200 OK:** Appointment updated successfully.
        - **400 Bad Request:** Invalid field, NHS number, postcode, or appointment status.
        - **404 Not Found:** Appointment not found.

### d. **Delete a Specific Appointment**

      - **Endpoint:** `/appointments/<id>/`
      - **Method:** `DELETE`
      - **Description:** Deletes a specific appointment using the appointment ID.
      - **Responses:**
        - **200 OK:** Appointment deleted successfully.
        - **404 Not Found:** Appointment not found.

## Error Handling

- **NHS Number:** Must be a valid 10-character string, and conform to the [checksum](https://www.datadictionary.nhs.uk/attributes/nhs_number.html). Invalid NHS numbers will result in a 400 Bad Request.
- **Postcode:** Must be a valid string. Invalid postcodes will be rejected, resulting in a 400 Bad Request.
- **Appointment Status:** Must be a valid string representing the appointment status. Invalid statuses will result in a 400 Bad Request.
- **Date and Time:** Must follow the format `YYYY-MM-DDTHH:MM:SS+TZ`. Incorrect formats will result in errors.
- **Duplicate Entries:** Attempting to add a patient or appointment with duplicate identifiers (NHS number or appointment ID) will result in a 409 Conflict.

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

# PANDA Application Installation and Configuration Guide

This guide provides detailed steps on how to set up and run the PANDA (Patient Appointment Network Data Application) Flask application, ensuring it communicates effectively with a PostgreSQL database.

## **1. Setting Up the Flask Application**

The application requires some Python packages to run. Install these packages:

```bash
pip install -r requirements.txt
```

This installs all necessary packages listed in the `requirements.txt` file, such as Flask and psycopg2-binary.

## **2. Running the Flask Application**

### **Development Mode**

You can run the flask server in development mode using the command:

```bash
python3 app.py
```

**Note**: Running the application in development mode is suitable for testing and debugging. However, it is not optimized for production as it lacks load balancing and worker processes.

### **Production Mode**

For a production environment, it is recommended to use a WSGI server like `Gunicorn` or `uWSGI`. This approach allows the application to handle more users by providing load balancing and worker processes.

Example using Gunicorn:

```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## **3. Database Configuration**

The application requires access to a PostgreSQL database, the credentials of which are provided using the `DATABASE_URL` environment variable.
Create `DATABASE_URL` and assign the database connection string to it:

```bash
export DATABASE_URL=postgresql://panda_user:panda_pass@db/panda_db
```

Or, define it in-line

```bash
DATABASE_URL=postgresql://panda_user:panda_pass@db/panda_db python3 app.py
```

This environment variable allows the application to connect to the PostgreSQL database using the provided username, password, and database name.

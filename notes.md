# PANDA

Broadly speaking, I'll go through the following steps:

1. Project Setup and Configuration
2. Database Design
   - Tables for Patients, Appointments, and Clinicians.
3. API Endpoints Design
   - This is just a CRUD (Create, Read, Update, Delete) API, so:
     - **Patients**
       - POST `/patients/`: Add a new patient.
       - GET `/patients/<id>/`: Retrieve details of a specific patient.
       - PUT `/patients/<id>/`: Update details of a specific patient.
       - DELETE `/patients/<id>/`: Remove a patient.
     - **Appointments**
       - POST `/appointments/`: Schedule a new appointment.
       - GET `/appointments/<id>/`: Retrieve details of a specific appointment.
       - PUT `/appointments/<id>/`: Update details of a specific appointment.
       - DELETE `/appointments/<id>/`: Cancel an appointment.
4. Data Validation
   - Implement NHS number checksum validation.
   - Implement postcode formatting and validation.
   - Implement patient name validation in line with GDPR.

6. Testing
   - Write unit tests to ensure business logic is correctly implemented.
   - Write integration tests to ensure the API endpoints work as expected.

7. **Documentation**
   - Document how to set up and run the API.
   - Document how to interact with the API, including example requests and responses.

I will do my best to document as I go, 

## Framework - Flask

The client wants to use the most lightweight framework they can. Whilst I would prefer Django for an API like this, for nice admin panels, database management, and extremely easy CRUD views out of the box, Flask is the clear choice for this requirement. This does come with the caveat of my having to handle database things myself, but that's not so bad.

## Encapsulation - Docker

This will need a database. I'm going with POSTGRES, but not for any particular reason. I'll use a docker-compose stack to bundle this together. 

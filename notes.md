# PANDA

### Hard requirements:
- [x] It should be possible to add patients to and remove them from the PANDA.
- [x] It should be possible to check and update patient details in the PANDA.
- [x] It should be possible to add new appointments to the PANDA, and check and update appointment details.
- [x] The PANDA may need to be restarted for maintenance, and the data should be persisted.
- [x] The PANDA backend should communicate with the frontend via some sort of HTTP API.
- [x] The PANDA API does not need to handle authentication because it is used within a trusted environment.
- [x] Errors should be reported to the user.
  
### Data validation:

- [x] Appointments can be cancelled, but cancelled appointments cannot be reinstated.
- [x] Appointments should be considered 'missed' if they are not set to 'attended' by the end of the appointment.
- [x] Ensure that all NHS numbers are checksum validated.
- [x] Ensure that all postcodes can be coerced into the correct format.



### Soft requirements:

- [x] The client has been burned by vendor lock-in in the past, and prefers working with smaller frameworks.
  - We've gone with Flask to meet this.
- [x] The client highly values automated tests, particularly those which ensure their business logic is implemented correctly.
  - A test suite is in progress, using `pytest`.
- [x] The client is in negotiation with several database vendors, and is interested in being database-agnostic if possible.
  - The current implementation uses `postgres`, but via `SQLAlchemy`. This should make transitioning to another database provider relatively easy.
- [ ] The client is somewhat concerned that missed appointments waste significant amounts of clinicians' time, and is interested in tracking the impact this has over time on a per-clinician and per-department basis.
- [ ] The PANDA currently doesn't contain much data about clinicians, but will eventually track data about the specific organisations they currently work for and where they work from.
  - This should be easily added using another database model.
- [ ] The client is interested in branching out into foreign markets, it would be useful if error messages could be localised.
  - Rather than having the strings for error messages encoded in the app as they are now, an Enum could be used to hold the feedback messages instead. Then, the relevant enum attribute could be formatted and returned to the user.
- [x] The client would like to ensure that patient names can be represented correctly, in line with GDPR.
  - The test cases contain names like "महावीर, जगन्नाथ", which I believe covers this kind of thing.



## Plan

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
   - Store and report names in such a way that non-latin characters (and those with accents) can be displayed.

5. Testing
   - Write unit tests to ensure business logic is correctly implemented.
   - Write integration tests to ensure the API endpoints work as expected.

6. **Documentation**
   - Document how to set up and run the API.
   - Document how to interact with the API, including example requests and responses.

I will do my best to document as I go.

## Framework - Flask

The client wants to use the most lightweight framework they can. Whilst I would prefer Django for an API like this, for nice admin panels, database management, and extremely easy CRUD views out of the box, Flask is the clear choice for this requirement. This does come with the caveat of my having to handle database things myself, but that's not so bad.

## Encapsulation - Docker

This will need a database. I'm going with POSTGRES, but not for any particular reason. I'll use a docker-compose stack to bundle this together. 


# Build logs

Defined a model - patients seem simple, so I'll start there. No validation yet, but I'll add it later. I want tests from the beginning, so I've written a reasonable test suite, which runs through all the example names - I looked through them, and I see some styles of names that I might not have thought to check myself. Very useful.

The tests pass, but I had a bit of a hitch with testing. I wanted to have the docker stack test the app when the container is built, but the test I wrote tears down the database when it's done. I need to fix that. In the meantime, I'll just deal with tests resetting the database - we have no prod data yet, so for the time being that's okay.

Wrote a lot of code so far, faster than I'd like. I worry that I've not been careful enough, so I'll make a note to do a code review ASAP. However, I've still not got to the input validation... My TODO list (in order) currently looks like this:
- Patient input validation
- Document what inputs are valid for Patients
- Fix the tests to not nuke the database
- Implement the appointments

Honestly, the appointments seem more complex so may take some time. There is a chance that I may need to sacrifice some rigour in the patients side, to get the appointments functioning.

I've added in the appointments, and written some very basic tests for the endpoints. 

Added some data validation functions. I tend to use Django more than flask (I only really use flask when something needs to be lightweight), so I have less experience with some of the tooling, and I've not done data validation in this framework before. Some basic research tells me that I could use tools like WTForms and Marshmallow, but I don't have time to learn a new tool right now so I'll just do it by hand. There's only a small number of checks I need, anyway.

Note that my validation actually breaks the tests - some of the example postcodes are given in "wrong-ish" formats, like "AB123CD" rather than "AB12 3CD". I'll need to update them to account for that.

TODO: It's just occurred to me that I didn't think to make the endpoints async. This is fine for now, but needs to be fixed later!

I've been neglecting detailed docs for the API - namely, the structure of the data needs to be defined, and which actions are allowed needs to be specified. I'll do that next.

I've run out of time, and the utils don't have good tests for them. Unfortunately, that's going to have to go in "future work", and whilst I'm fairly confident in the logic I doubt they're bug-free. 


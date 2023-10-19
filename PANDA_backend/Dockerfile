# Use an official Python runtime as a parent image
FROM python:3.10-buster

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the local package directories to the container
COPY . .

# Install netcat to wait for the database to be ready
RUN apt-get update && apt-get install -y netcat

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Use the entrypoint script to run migrations and start the app
ENTRYPOINT ["./entrypoint.sh"]

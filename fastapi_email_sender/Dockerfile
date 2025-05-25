# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /usr/src/app

# Install system dependencies that might be needed by some Python packages
# (e.g., for cryptography, if it were a direct or indirect dependency)
# For a basic FastAPI app with smtplib, this might not be strictly necessary,
# but it's good practice for more complex applications.
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     build-essential \
#     # Add any other system dependencies here
#  && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container at /usr/src/app
COPY requirements.txt ./

# Install any needed packages specified in requirements.txt
# --no-cache-dir: Disables the pip cache, reducing image size.
# --trusted-host pypi.python.org: Can be useful if there are issues with SSL certs for PyPI.
RUN pip install --no-cache-dir --trusted-host pypi.python.org -r requirements.txt

# Copy the application code into the container
# This copies the content of the ./app directory on the host
# to the /usr/src/app/app directory in the container.
COPY ./app /usr/src/app/app

# Expose the port the app runs on
# This informs Docker that the container listens on the specified network ports at runtime.
# This does not actually publish the port. That's done with `docker run -p` or docker-compose.
EXPOSE 8000

# Define the command to run your application
# This will start the Uvicorn server.
# --host 0.0.0.0 makes the server accessible from outside the container.
# --port 8000 matches the EXPOSE instruction.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# --- Notes on .env file ---
# This Dockerfile does NOT copy the .env file.
# Environment variables should be passed to the container at runtime:
# 1. Using `docker run -e VAR=value ...`
# 2. Using `docker run --env-file ./path/to/.env ...`
# 3. Using a docker-compose.yml file with an `env_file` or `environment` section.
# This is more secure and flexible than baking secrets into the image.
# Ensure your application (e.g., app/config.py) is set up to read these
# environment variables.
#
# If you absolutely needed to bake it in (NOT RECOMMENDED FOR SECRETS):
# COPY .env .env
# But then ensure .env is appropriately populated at build time and be aware of security implications.

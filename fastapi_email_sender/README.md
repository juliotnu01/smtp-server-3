# FastAPI Email Sender API

This FastAPI application provides an endpoint to send emails via an SMTP server.
It's designed to be containerized with Docker.

## Project Structure

```
fastapi_email_sender/
├── app/
│   ├── __init__.py
│   ├── main.py         # FastAPI app, endpoint, SMTP logic
│   ├── schemas.py      # Pydantic models for request/response
│   └── config.py       # Configuration loading
├── .env.example        # Example environment variables
├── Dockerfile          # Docker configuration
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

## Prerequisites

*   Docker installed.
*   An SMTP server accessible to this API (e.g., the `docker-mailserver` setup from the previous guide).
*   An email account on the SMTP server that can be used for sending emails.

## Setup and Configuration

1.  **Environment Variables:**
    *   Copy the `.env.example` file to a new file named `.env` in the `fastapi_email_sender` directory:
        ```bash
        cp .env.example .env
        ```
    *   **Edit `.env`** and fill in your actual SMTP server details and credentials:
        *   `MAIL_SERVER_HOST`: Hostname or IP of your SMTP server. If using `docker-mailserver` on the same Docker network, this can be the service name (e.g., `mailserver`).
        *   `MAIL_SERVER_PORT`: SMTP server port (e.g., `587`).
        *   `MAIL_USERNAME`: Username for SMTP authentication (e.g., `api-user@yourdomain.com`).
        *   `MAIL_PASSWORD`: Password for the SMTP user.
        *   `DEFAULT_FROM_EMAIL`: Default sender email address.
        *   `API_KEY` (Optional): If you want to use API key authentication, generate a secure key (e.g., `openssl rand -hex 32`) and set it here.

    *   **IMPORTANT:** Add `.env` to your `.gitignore` file to prevent committing sensitive credentials to version control:
        ```bash
        echo ".env" >> .gitignore
        ```
        (If you are in a Git repository. If not, just be mindful not to share it.)

## Building the Docker Image

Navigate to the `fastapi_email_sender` directory (where the `Dockerfile` is located) and run:

```bash
docker build -t fastapi-email-api .
```
This will build a Docker image named `fastapi-email-api`.

## Running the Docker Container (Standalone for Testing)

To run the container locally for testing, you need to pass the environment variables.
The most straightforward way without `docker-compose` is to use an environment file.

1.  **Ensure your `.env` file is correctly populated.**
2.  Run the Docker container:
    ```bash
    docker run -d --name email-api-container -p 8000:8000 --env-file ./.env fastapi-email-api
    ```
    *   `-d`: Run in detached mode (background).
    *   `--name email-api-container`: Assigns a name to the container for easier management.
    *   `-p 8000:8000`: Maps port 8000 on your host to port 8000 in the container.
    *   `--env-file ./.env`: Loads environment variables from your `.env` file.

    **Alternative (passing individual environment variables):**
    If you prefer not to use `--env-file`, you can pass variables individually (less convenient for many variables):
    ```bash
    docker run -d --name email-api-container -p 8000:8000 \
      -e MAIL_SERVER_HOST="your_mail_server_host" \
      -e MAIL_SERVER_PORT="587" \
      -e MAIL_USERNAME="api-user@yourdomain.com" \
      -e MAIL_PASSWORD="your_password" \
      -e DEFAULT_FROM_EMAIL="api-user@yourdomain.com" \
      # -e API_KEY="your_api_key" # Optional
      fastapi-email-api
    ```

## Accessing the API

*   **API Docs (Swagger UI):** Once running, open your browser to `http://localhost:8000/docs`
*   **Root Endpoint:** `http://localhost:8000/`
*   **Send Email Endpoint:** `POST http://localhost:8000/send-email/`

**Using API Key Authentication (if enabled):**
If you have set an `API_KEY` in your environment, you must include it in the `X-API-Key` header of your requests to the `/send-email/` endpoint.

## Example `curl` request to `/send-email/`:

Assuming no API key is set:
```bash
curl -X 'POST' \
  'http://localhost:8000/send-email/' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "to_recipients": ["recipient1@example.com", "recipient2@example.com"],
  "subject": "Hello from FastAPI Email API",
  "html_body": "<h1>Test Email</h1><p>This is a test email sent via the FastAPI application.</p>",
  "from_email": "sender@yourdomain.com"
}'
```

If `API_KEY` is set in your `.env` file (e.g., to `mysecretkey`):
```bash
curl -X 'POST' \
  'http://localhost:8000/send-email/' \
  -H 'accept: application/json' \
  -H 'X-API-Key: mysecretkey' \
  -H 'Content-Type: application/json' \
  -d '{
  "to_recipients": ["recipient1@example.com"],
  "subject": "Hello from Secure FastAPI Email API",
  "html_body": "<h1>Test Email</h1><p>This is a test email sent via the FastAPI application with API key.</p>"
}'
```

## Next Steps (Integration with Docker Compose)

For a more robust setup, especially when running alongside the `docker-mailserver`, you will typically use `docker-compose`. The next step in the overall guide will likely cover creating a `docker-compose.yml` that links this API service with the mail server service on a shared Docker network. This simplifies configuration (e.g., using service names like `mailserver` for `MAIL_SERVER_HOST`) and management.
```

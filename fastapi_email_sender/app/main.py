import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security.api_key import APIKeyHeader

from .schemas import EmailSchema, EmailResponse, EmailResponseDetail
from .config import settings
from typing import List, Optional

app = FastAPI(
    title="FastAPI Email Sender",
    description="An API to send emails using SMTP.",
    version="0.1.0"
)

# --- API Key Security (Optional) ---
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def get_api_key(key: str = Security(api_key_header)):
    if settings.API_KEY: # Only enforce if API_KEY is set in config
        if key == settings.API_KEY:
            return key
        else:
            raise HTTPException(
                status_code=403, detail="Could not validate credentials"
            )
    return None # No API key needed if not configured

# --- Root Endpoint ---
@app.get("/", tags=["General"])
async def read_root():
    return {"message": "Email API is running. Visit /docs for API documentation."}

# --- Send Email Endpoint ---
@app.post("/send-email/", response_model=EmailResponse, tags=["Email"])
async def send_email_route(
    email_data: EmailSchema,
    api_key: Optional[str] = Depends(get_api_key) # Optional API Key check
):
    """
    Sends an email to one or more recipients.

    - **to_recipients**: A list of email addresses to send the email to.
    - **subject**: The subject of the email.
    - **html_body**: The HTML content of the email.
    - **from_email** (optional): The sender's email address. If not provided,
      the default configured in `DEFAULT_FROM_EMAIL` will be used.
    """
    response_details: List[EmailResponseDetail] = []
    overall_success = True

    from_address = email_data.from_email or settings.DEFAULT_FROM_EMAIL

    # Validate that from_address is set
    if not from_address:
        raise HTTPException(
            status_code=400,
            detail="Sender email ('from_email') is not provided and no default is configured."
        )

    try:
        context = ssl.create_default_context()
        server = smtplib.SMTP(settings.MAIL_SERVER_HOST, settings.MAIL_SERVER_PORT, timeout=10)
        server.ehlo()
        server.starttls(context=context)
        server.ehlo()
        server.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)

        for recipient in email_data.to_recipients:
            message = MIMEMultipart("alternative")
            message["From"] = from_address
            message["To"] = recipient
            message["Subject"] = email_data.subject

            # Attach HTML body
            message.attach(MIMEText(email_data.html_body, "html"))

            try:
                server.sendmail(from_address, recipient, message.as_string())
                response_details.append(EmailResponseDetail(recipient=recipient, status="sent"))
            except smtplib.SMTPRecipientsRefused as e:
                # This error is specific to one recipient being refused
                response_details.append(EmailResponseDetail(recipient=recipient, status="failed", error_message=f"Recipient refused: {str(e.recipients)}"))
                overall_success = False
            except smtplib.SMTPHeloError as e:
                response_details.append(EmailResponseDetail(recipient=recipient, status="failed", error_message=f"Server didn't reply properly to HELO: {str(e)}"))
                overall_success = False
            except smtplib.SMTPSenderRefused as e:
                # This error is more general, sender refused for this recipient
                response_details.append(EmailResponseDetail(recipient=recipient, status="failed", error_message=f"Sender refused: {str(e)}"))
                overall_success = False
            except smtplib.SMTPDataError as e:
                response_details.append(EmailResponseDetail(recipient=recipient, status="failed", error_message=f"Server replied with an unexpected error code to DATA: {str(e)}"))
                overall_success = False
            except Exception as e_recipient: # Catch other exceptions during sendmail for a specific recipient
                response_details.append(EmailResponseDetail(recipient=recipient, status="failed", error_message=f"An unexpected error occurred for this recipient: {str(e_recipient)}"))
                overall_success = False

        server.quit()

    except smtplib.SMTPAuthenticationError as e:
        # This is a critical error for all recipients
        error_msg = f"SMTP Authentication Error: {str(e)}. Check MAIL_USERNAME and MAIL_PASSWORD."
        for r in email_data.to_recipients:
            if not any(d.recipient == r for d in response_details):
                response_details.append(EmailResponseDetail(recipient=r, status="failed", error_message=error_msg))
        overall_success = False
        # Return immediately as this is a configuration/auth issue affecting all.
        raise HTTPException(status_code=500, detail={"message": "Failed to send email(s) due to server authentication error.", "details": response_details})
    except (smtplib.SMTPConnectError, ConnectionRefusedError, smtplib.SMTPServerDisconnected) as e:
        error_msg = f"SMTP Connection Error: {str(e)}. Check MAIL_SERVER_HOST and MAIL_SERVER_PORT."
        for r in email_data.to_recipients:
            if not any(d.recipient == r for d in response_details):
                response_details.append(EmailResponseDetail(recipient=r, status="failed", error_message=error_msg))
        overall_success = False
        raise HTTPException(status_code=500, detail={"message": "Failed to send email(s) due to server connection error.", "details": response_details})
    except ssl.SSLError as e:
        error_msg = f"SSL Error: {str(e)}. This might be due to self-signed certificates or SSL configuration issues."
        for r in email_data.to_recipients:
             if not any(d.recipient == r for d in response_details):
                response_details.append(EmailResponseDetail(recipient=r, status="failed", error_message=error_msg))
        overall_success = False
        raise HTTPException(status_code=500, detail={"message": "Failed to send email(s) due to SSL error.", "details": response_details})
    except Exception as e_global: # Catch-all for other unexpected errors during setup/quit
        error_msg = f"An unexpected global error occurred: {str(e_global)}"
        # Add this error to any recipients not already processed
        for r in email_data.to_recipients:
            if not any(d.recipient == r for d in response_details): # if recipient not already in details
                response_details.append(EmailResponseDetail(recipient=r, status="failed", error_message=error_msg))
        overall_success = False
        # Consider re-raising as HTTPException if no details were populated, or if it's a setup issue
        if not response_details: # if list is empty, means error was very early
             raise HTTPException(status_code=500, detail={"message": error_msg, "details": []})


    if overall_success:
        return EmailResponse(message="Email(s) processed successfully.", details=response_details)
    else:
        # Even if some emails failed, we return a 200 OK with detailed statuses
        # The client can then inspect the 'details' array.
        # Alternatively, one could choose to return a 207 Multi-Status or a 500 if any failure is critical.
        # For now, a 200 with details seems appropriate for partial success.
        return EmailResponse(message="Some email(s) could not be sent.", details=response_details)

# To run the app (for local development without Docker):
# uvicorn app.main:app --reload
#
# Ensure .env file is present in the fastapi_email_sender directory with correct values.
# Example:
# MAIL_SERVER_HOST=localhost
# MAIL_SERVER_PORT=1025 # (if using a local debug server like 'python -m smtpd -c DebuggingServer -n localhost:1025')
# MAIL_USERNAME=your_email@example.com
# MAIL_PASSWORD=your_password
# DEFAULT_FROM_EMAIL=your_email@example.com
# # API_KEY=your_secret_api_key (optional)

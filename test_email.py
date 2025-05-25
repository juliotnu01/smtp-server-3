# ----------------------------------------------------------------------------------------------------------------------
# test_email.py - Simple script to test docker-mailserver setup
#
# This script uses smtplib to send an email via the local mail server.
# It's intended for verifying that the mail server is operational, can authenticate users,
# and relay emails to external addresses.
#
# Before running:
# 1. Ensure your docker-mailserver container is running.
# 2. Replace placeholder values below (MAIL_SERVER, PORT, SENDER_EMAIL, SENDER_PASSWORD, RECIPIENT_EMAIL).
# 3. If running this script from outside the Docker host, replace 'localhost' with the
#    Docker host's public IP address.
# ----------------------------------------------------------------------------------------------------------------------

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- Configuration ---
# These should match the details of the account created in your mail server
# and the server's address.

# Replace with your mail server's address.
# If running this script on the same machine as the Docker container, 'localhost' or '127.0.0.1' should work.
# If running from another machine, use the Docker host's IP address or resolvable hostname.
MAIL_SERVER = 'localhost' # Or your Docker host IP if run remotely

PORT = 587  # Port for STARTTLS (recommended)
            # Use 465 for SMTPS (older, but still common) if 587 doesn't work.

# Replace with the email account created in your mailserver
SENDER_EMAIL = 'api-user@yourdomain.com'
# Replace with the password for the SENDER_EMAIL account
SENDER_PASSWORD = 'strongpassword123'

# Replace with an external email address you have access to, for receiving the test email.
RECIPIENT_EMAIL = 'your-personal-email@example.com'

# --- Email Content ---
SUBJECT = 'Test Email from Docker Mail Server'
BODY_TEXT = """Hello,

This is a test email sent from the Python script (test_email.py)
to verify the docker-mailserver setup.

If you received this, your mail server is likely configured correctly for sending email!

Regards,
Your Mail Server Test Script
"""
BODY_HTML = """<html>
<head></head>
<body>
  <h1>Hello,</h1>
  <p>This is a test email sent from the Python script (<code>test_email.py</code>)
     to verify the <strong>docker-mailserver</strong> setup.</p>
  <p>If you received this, your mail server is likely configured correctly for sending email!</p>
  <p>Regards,<br>
     Your Mail Server Test Script</p>
</body>
</html>
"""

def send_test_email():
    """
    Connects to the mail server and sends a test email.
    """
    print(f"Attempting to send an email from {SENDER_EMAIL} to {RECIPIENT_EMAIL} via {MAIL_SERVER}:{PORT}...")

    # Create a multipart message and set headers
    message = MIMEMultipart("alternative")
    message["From"] = SENDER_EMAIL
    message["To"] = RECIPIENT_EMAIL
    message["Subject"] = SUBJECT

    # Attach parts
    part1 = MIMEText(BODY_TEXT, "plain")
    part2 = MIMEText(BODY_HTML, "html")
    message.attach(part1)
    message.attach(part2)

    try:
        # Create a secure SSL context
        # For STARTTLS on port 587, we connect in plaintext first, then upgrade.
        # For SMTPS on port 465, the connection is SSL from the start.
        context = ssl.create_default_context()

        if PORT == 587:
            # Connect to server and start TLS
            server = smtplib.SMTP(MAIL_SERVER, PORT, timeout=10) # 10 second timeout
            print("Connected to server, attempting to start TLS...")
            server.ehlo()  # Extended Hello
            server.starttls(context=context) # Secure the connection
            server.ehlo()  # Re-identify ourselves over TLS connection
        elif PORT == 465:
            # Connect to server using SSL
            server = smtplib.SMTP_SSL(MAIL_SERVER, PORT, context=context, timeout=10)
            print("Connected to server using SSL...")
        else:
            print(f"Unsupported port: {PORT}. Please use 587 for STARTTLS or 465 for SMTPS.")
            return

        # Login
        print(f"Attempting to log in as {SENDER_EMAIL}...")
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        print("Logged in successfully.")

        # Send email
        print(f"Sending email to {RECIPIENT_EMAIL}...")
        server.sendmail(SENDER_EMAIL, RECIPIENT_EMAIL, message.as_string())
        print("Email sent successfully!")

    except smtplib.SMTPAuthenticationError as e:
        print(f"SMTP Authentication Error: {e}")
        print("Please check your SENDER_EMAIL and SENDER_PASSWORD, and ensure the user exists on the mail server.")
    except smtplib.SMTPServerDisconnected as e:
        print(f"Server disconnected unexpectedly: {e}")
        print("This could be due to a network issue or the mail server container stopping.")
    except smtplib.SMTPConnectError as e:
        print(f"Failed to connect to the server ({MAIL_SERVER}:{PORT}): {e}")
        print("Ensure the mail server is running and accessible, and the MAIL_SERVER/PORT are correct.")
        print("If running script outside Docker host, ensure MAIL_SERVER is the host's public IP and port is open.")
    except ConnectionRefusedError as e:
        print(f"Connection refused by the server ({MAIL_SERVER}:{PORT}): {e}")
        print("Ensure the mail server container is running and the port mapping is correct in docker-compose.yml.")
    except ssl.SSLError as e:
        print(f"SSL Error: {e}")
        print("This might be due to self-signed certificates if SSL_TYPE=self-signed. "
              "For testing, you might need to adjust SSL context or temporarily trust the cert. "
              "For production, ensure valid certificates (e.g., Let's Encrypt).")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if 'server' in locals() and server:
            try:
                print("Quitting server connection...")
                server.quit()
            except Exception as e:
                print(f"Error quitting server connection: {e}")

if __name__ == "__main__":
    print("--- Mail Server Test Script ---")
    print("IMPORTANT: Make sure you have updated the placeholder values in this script (MAIL_SERVER, SENDER_EMAIL, etc.).")
    send_test_email()
    print("-----------------------------")

# --- How to Run ---
# 1. Save this script as test_email.py.
# 2. Modify the placeholder variables (MAIL_SERVER, PORT, SENDER_EMAIL, SENDER_PASSWORD, RECIPIENT_EMAIL).
# 3. Ensure your docker-mailserver is running and the api-user@yourdomain.com is created.
# 4. Run from your terminal: python test_email.py
#
# --- Troubleshooting ---
# - Connection Errors:
#   - Verify `MAIL_SERVER` IP/hostname and `PORT`.
#   - Check Docker container is running: `docker ps`
#   - Check container logs: `docker logs mailserver` (or your container name)
#   - Ensure firewall/security groups allow traffic on the specified port (e.g., 587 or 465).
# - Authentication Errors:
#   - Double-check `SENDER_EMAIL` and `SENDER_PASSWORD`.
#   - Ensure the user was correctly added to docker-mailserver:
#     `docker exec -ti mailserver setup email list`
# - SSL Errors with self-signed certs:
#   - For initial testing with `SSL_TYPE=self-signed`, email clients (and this script) will complain.
#     The script attempts to use a default SSL context which might fail.
#     You might need to temporarily disable hostname verification or add the self-signed CA to your trust store,
#     but this is not recommended for production.
#   - Prefer `SSL_TYPE=letsencrypt` for valid certificates.
# - Email not received:
#   - Check spam/junk folders in the recipient's mailbox.
#   - Check mail server logs (`docker logs mailserver`) for clues about delivery issues.
#   - Ensure your server's IP has a good reputation and that you have PTR (reverse DNS) records set up,
#     especially for production.
#   - DKIM and SPF records are crucial for deliverability.
# ----------------------------------------------------------------------------------------------------------------------

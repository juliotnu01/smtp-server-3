# End-to-End Deployment and Testing Guide

This guide provides a checklist and instructions to deploy your `docker-mailserver` and FastAPI email API using Docker Compose on your EC2 instance (or other Docker host). It also covers how to test the entire solution.

**Assumptions:**

*   You are on your EC2 instance or Docker host.
*   Your project directory is set up with the main `docker-compose.yml`, `mailserver.env`, and the `fastapi_email_sender` subdirectory (which includes its own `.env` file, `Dockerfile`, and application code).
*   All previous setup steps (DNS, `docker-mailserver` user creation, FastAPI app code, `docker-compose.yml` contents) have been completed.

---

## 1. Pre-flight Checks

Before launching, ensure the following:

*   **Stop Previous Containers:** If you were running a standalone `docker-mailserver` container (e.g., from earlier testing), stop and remove it to avoid port conflicts or data inconsistencies.
    ```bash
    docker stop dms_container # Or your mailserver container name if different
    docker rm dms_container
    ```
    (If you used `docker-compose up` for a standalone mailserver previously, use `docker-compose down` in that directory.)

*   **Verify `fastapi_email_sender/.env`:**
    *   Open `fastapi_email_sender/.env`.
    *   Confirm `MAIL_SERVER_HOST=mailserver` (this allows the API container to find the mailserver container on the shared Docker network).
    *   Ensure `MAIL_USERNAME` and `MAIL_PASSWORD` are the correct credentials for the email account you created in `docker-mailserver` (e.g., `api-user@yourdomain.com`).
    *   Ensure `DEFAULT_FROM_EMAIL` is set correctly.
    *   If you've configured an `API_KEY` for the FastAPI app, note it down for testing.

*   **Verify Mail Server Hostname (`DMS_HOSTNAME`):**
    *   The `docker-compose.yml` file uses `hostname: ${DMS_HOSTNAME:-mail.example.com}` for the `mailserver` service.
    *   Ensure `DMS_HOSTNAME` is correctly set to your mail server's fully qualified domain name (e.g., `mail.yourdomain.com`). You can do this by:
        *   Creating a `.env` file in the same directory as your `docker-compose.yml` with the line: `DMS_HOSTNAME=mail.yourdomain.com`
        *   OR by directly replacing `${DMS_HOSTNAME:-mail.example.com}` in `docker-compose.yml` with your actual hostname (less flexible).

*   **Ensure Necessary Directories Exist:**
    The volume mappings in `docker-compose.yml` point to local directories (e.g., `./docker-data/dms/...`). Ensure these directories have been created on your host:
    ```bash
    mkdir -p ./docker-data/dms/mail-data/
    mkdir -p ./docker-data/dms/mail-state/
    mkdir -p ./docker-data/dms/mail-logs/
    mkdir -p ./docker-data/dms/config/
    mkdir -p ./docker-data/dms/letsencrypt/
    ```

---

## 2. Deploy with Docker Compose

Navigate to the directory containing your main `docker-compose.yml` file.

*   **Command:**
    ```bash
    docker-compose up --build -d
    ```
*   **Explanation:**
    *   `docker-compose up`: This command starts and runs your multi-container application.
    *   `--build`: This flag tells Docker Compose to build the image for the `api` service (as defined in `fastapi_email_sender/Dockerfile`) before starting the service. It will also rebuild if the Dockerfile or context has changed.
    *   `-d`: Runs the containers in detached mode (in the background), so your terminal is free.

---

## 3. Monitor Logs

It's crucial to check the logs, especially on the first run, to ensure both services start correctly.

*   **Mail Server Logs:**
    ```bash
    docker-compose logs -f mailserver
    ```
    *   Look for messages indicating successful startup, user account loading, and any errors related to SSL, DKIM, or network configuration.
    *   If using Let's Encrypt (`SSL_TYPE=letsencrypt`), monitor for successful certificate acquisition.

*   **API Logs:**
    ```bash
    docker-compose logs -f api
    ```
    *   Look for Uvicorn startup messages (e.g., `Uvicorn running on http://0.0.0.0:8000`).
    *   Check for any errors related to loading configuration or connecting to the mail server (though connection attempts will likely only happen when you hit the endpoint).

Press `Ctrl+C` to stop following the logs for each service.

---

## 4. API Testing Steps

Replace `YOUR_EC2_INSTANCE_IP` with your EC2 instance's public IP address. If testing directly on the EC2 instance (e.g., via SSH), you can often use `localhost` or `127.0.0.1`.
Replace `yourdomain.com` and `api-user@yourdomain.com` with your actual domain and sender email.
Replace `recipient@example.com` with an external email address you can access.

*   **A. Test Root Endpoint:**
    ```bash
    curl http://YOUR_EC2_INSTANCE_IP:8000/
    ```
    *   **Expected Output:**
        ```json
        {"message":"Email API is running. Visit /docs for API documentation."}
        ```

*   **B. Test Send Email Endpoint:**
    Adjust the `curl` command based on whether you set an `API_KEY` in your `fastapi_email_sender/.env`.

    ```bash
    curl -X POST "http://YOUR_EC2_INSTANCE_IP:8000/send-email/" \
    -H "Content-Type: application/json" \
    # If you set an API_KEY in fastapi_email_sender/.env, uncomment and set the next line:
    # -H "X-API-Key: your-actual-api-key-here" \
    -d '{
          "to_recipients": ["test-recipient@example.com", "another-test@example.org"],
          "from_email": "api-user@yourdomain.com",
          "subject": "Test Email from FastAPI via Docker Compose",
          "html_body": "<h1>Hello from Your Mail Server!</h1><p>This is a test email sent successfully using the full Docker Compose setup. If you received this, your API and mailserver are communicating correctly.</p>"
        }'
    ```
    *   **Check API Response:**
        *   A successful response might look like:
            ```json
            {
              "message": "Email(s) processed successfully.",
              "details": [
                { "recipient": "test-recipient@example.com", "status": "sent", "error_message": null },
                { "recipient": "another-test@example.org", "status": "sent", "error_message": null }
              ]
            }
            ```
        *   If there are errors, the `details` array or the main error message from the API will provide clues.
    *   **Check Recipient's Inbox:**
        *   Verify the email arrives at `test-recipient@example.com` and `another-test@example.org`.
        *   Check the **spam/junk folder** as well, especially during initial testing.

---

## 5. Email Header Verification

Once you receive the test email, check its headers to verify your SPF, DKIM, and DMARC setup. How to do this varies by email client:

*   **Gmail:** Open the email, click the three vertical dots (More) next to the reply button, and select "Show original."
*   **Outlook.com:** Open the email, click the three dots (...) in the email pane, go to "View" -> "View message details."
*   **Thunderbird:** Open the email, click "More" -> "View Source."

**What to look for:**

*   **`Authentication-Results` Header:** This is often added by the receiving server (like Gmail).
    *   `spf=pass`
    *   `dkim=pass`
    *   `dmarc=pass` (or `dmarc=bestguesspass` etc., depending on the receiver and your policy)
*   **`Received-SPF` Header:** Should indicate a `pass` status.
*   **`DKIM-Signature` Header:** Presence of this header indicates your mail server signed the email.

A "pass" for all three (SPF, DKIM, DMARC) is ideal for deliverability.

---

## 6. Troubleshooting Guide

*   **API Errors (e.g., 500 Internal Server Error, 403 Forbidden):**
    *   Check API logs: `docker-compose logs -f api`. Look for Python tracebacks or error messages.
    *   Verify `fastapi_email_sender/.env`:
        *   Is `MAIL_SERVER_HOST=mailserver` correct?
        *   Are `MAIL_USERNAME` and `MAIL_PASSWORD` correct for the mail server account?
        *   Is `MAIL_SERVER_PORT` correct (usually 587)?
        *   If using `API_KEY`, is it correct in the request header?
    *   Ensure the `api` service can reach the `mailserver` service on the Docker network.

*   **Mail Server / Email Sending Errors:**
    *   Check mail server logs: `docker-compose logs -f mailserver`.
        *   Look for connection attempts from the API container's IP address (Docker internal IP).
        *   Look for authentication errors, relay denials, or issues connecting to external mail servers.
    *   **Security Groups (AWS EC2):** Ensure your EC2 instance's security group allows **outbound** traffic on TCP port 25. Some cloud providers restrict this by default to prevent spam. You might need to request removal of this restriction for your Elastic IP.
    *   **ISP/AWS Port Blocking:** Besides security groups, AWS (and other ISPs/VPS providers) may block or throttle outbound port 25 on new accounts or IPs with no reputation. Contact AWS support if you suspect this.
    *   **Incorrect `OVERRIDE_HOSTNAME` or `DMS_HOSTNAME`:** Ensure the mail server identifies itself with the correct FQDN.

*   **Emails Land in Spam:**
    *   **DNS Records:** Use tools like [MXToolbox](https://mxtoolbox.com/) to verify your A, MX, SPF, DKIM, and DMARC records are correctly configured and propagated.
    *   **PTR Record (Reverse DNS):** This is crucial. Ensure your server's IP address has a PTR record that points back to your mail server's hostname (e.g., `mail.yourdomain.com`). For AWS Elastic IPs, this is configured via AWS support or the EC2 console.
    *   **IP Address Reputation:** If your server's IP address is new or has a poor reputation (e.g., listed on blacklists like Spamhaus), emails are more likely to be marked as spam. Building a good sending reputation takes time.
    *   **Email Content:** Avoid spammy content (excessive capitalization, misleading subjects, too many links to untrusted domains).
    *   **Missing DMARC `p=reject` or `p=quarantine`:** While `p=none` is good for starting, gradually moving to a stricter policy can improve trust.

*   **Port Conflicts on Host:**
    *   If `docker-compose up` fails with errors about ports being already allocated, ensure no other services are using ports 25, 587, 8000, etc., on your Docker host.
    *   Use `sudo netstat -tulnp | grep LISTEN` or `sudo ss -tulnp` to check listening ports.

*   **Docker Network Issues:**
    *   Rarely, Docker networking might have issues. `docker-compose down` and then `docker-compose up` can sometimes resolve transient issues.
    *   Ensure `email_network` is correctly defined in `docker-compose.yml` and both services are part of it.

---

By following these steps, you should be able to deploy your email solution and effectively test its functionality from end to end. Good luck!

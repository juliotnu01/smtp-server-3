# Setting up Your Dockerized Email Server with docker-mailserver

This guide will walk you through setting up a personal/small-business email server using `docker-mailserver`. This setup is intended to be run on a server like an AWS EC2 instance.

**IMPORTANT PRELIMINARIES:**

1.  **Domain Name:** You **must** own a domain name (e.g., `yourdomain.com`). Replace all instances of `yourdomain.com` in the configuration files with your actual domain.
2.  **Server IP Address:** You will need a server (e.g., an AWS EC2 instance) with a **static public IP address** (Elastic IP in AWS terms). This is crucial for DNS records (MX, A, SPF, DKIM, DMARC) to point correctly to your mail server.
3.  **DNS Management:** You need access to your domain's DNS settings to add various records (A, MX, TXT for SPF/DKIM/DMARC).
4.  **Firewall/Security Groups:** Ensure the following ports are open for inbound traffic on your server:
    *   **25 (SMTP):** For receiving email from other mail servers.
    *   **587 (SMTP Submission with STARTTLS):** For your email clients (and your future API) to send email.
    *   **465 (SMTPS):** Legacy port for SMTP over SSL, still used by some clients.
    *   **143 (IMAP with STARTTLS):** For your email clients to read email.
    *   **993 (IMAPS):** For secure IMAP.
    *   **80/443 (HTTP/HTTPS):** Temporarily needed if you use `SSL_TYPE=letsencrypt` for Let's Encrypt to perform domain validation via HTTP-01 or TLS-ALPN-01 challenges. `docker-mailserver` handles this internally if it can bind to these ports.

**Placeholder Values:**
Throughout the configuration, you'll see these placeholders. **Change them!**
*   `yourdomain.com`: Replace with your actual domain.
*   `mail.yourdomain.com`: This will be your mail server's hostname (Fully Qualified Domain Name - FQDN).
*   `api-user@yourdomain.com`: The email account you'll create for sending emails via your API.
*   `strongpassword123`: The password for `api-user@yourdomain.com`. **CHOOSE A STRONG, UNIQUE PASSWORD.**

---

## Step 1: Prepare Configuration Files

Three main files are provided:

1.  `mailserver.env`: Environment variables for `docker-mailserver`.
2.  `docker-compose.yml`: Defines the mail server Docker service.
3.  `test_email.py`: A Python script to test your mail server setup.

**Action:**
*   Download or copy the content of `mailserver.env`, `docker-compose.yml`, and `test_email.py` into a directory on your server (e.g., `/opt/email_server/`).
*   **Customize `mailserver.env`:**
    *   Change `OVERRIDE_HOSTNAME=mail.yourdomain.com` to your mail server's FQDN.
    *   If using `SSL_TYPE=letsencrypt` (recommended for production), uncomment and set `LETSENCRYPT_EMAIL=your-email@yourdomain.com` for renewal notices.
    *   Review other settings. The defaults are for a lightweight setup.
*   **Customize `docker-compose.yml`:**
    *   Change `hostname: mail.yourdomain.com` to your mail server's FQDN.
*   **Customize `test_email.py`:**
    *   Update `MAIL_SERVER`: If running the script on the same server as Docker, `'localhost'` is fine. If from another machine, use your server's public IP or `mail.yourdomain.com`.
    *   Update `SENDER_EMAIL` to `api-user@youractualdomain.com`.
    *   Update `SENDER_PASSWORD` to the strong password you chose.
    *   Update `RECIPIENT_EMAIL` to an external email address you can access to verify email sending.

---

## Step 2: Create Directory Structure on Docker Host

`docker-mailserver` requires persistent storage for mail data, state, logs, and configuration. The `docker-compose.yml` file maps these to local directories on your server.

**Action:**
On your server, create the following directory structure (assuming you placed your config files in `/opt/email_server/`):

```bash
sudo mkdir -p /opt/email_server/docker-data/dms/mail-data/
sudo mkdir -p /opt/email_server/docker-data/dms/mail-state/
sudo mkdir -p /opt/email_server/docker-data/dms/mail-logs/
sudo mkdir -p /opt/email_server/docker-data/dms/config/
sudo mkdir -p /opt/email_server/docker-data/dms/letsencrypt/ # If you plan to use the Let's Encrypt volume mapping

# Optional: Set permissions if you encounter issues, though Docker usually handles this.
# sudo chown -R <your_user>:<your_group> /opt/email_server/docker-data/
# Be careful with broad permissions. Docker might manage these fine on its own.
```
**Note:** Ensure these paths in your `docker-compose.yml` file under `volumes:` match the directories you create (e.g., `./docker-data/...` assumes `docker-compose` is run from `/opt/email_server/`).

---

## Step 3: Configure DNS Records

This step is crucial and done via your DNS provider (e.g., AWS Route 53, GoDaddy, Cloudflare).

1.  **A Record:**
    *   Name: `mail` (or whatever subdomain you chose for `OVERRIDE_HOSTNAME`)
    *   Value: Your server's static public IP address.
    *   Example: `mail.yourdomain.com  A  123.45.67.89`

2.  **MX Record:**
    *   Name: `@` or `yourdomain.com` (represents the root domain)
    *   Value: `mail.yourdomain.com` (your mail server's FQDN)
    *   Priority: `10` (a common default, lower numbers are higher priority)
    *   Example: `yourdomain.com  MX  10 mail.yourdomain.com`

3.  **PTR Record (Reverse DNS):**
    *   This record maps your server's IP address back to its hostname (e.g., `mail.yourdomain.com`).
    *   **How to set this up depends on your IP provider (e.g., your ISP, AWS for EC2).**
        *   For AWS EC2 with an Elastic IP, you need to request this. See AWS documentation.
    *   A missing or incorrect PTR record can severely impact email deliverability.

---

## Step 4: Launch the Mail Server

Navigate to the directory where you saved `docker-compose.yml` and `mailserver.env`.

**Action:**

```bash
cd /opt/email_server/ # Or wherever your files are
docker-compose up -d mailserver
```

*   `docker-compose up -d mailserver`: Starts the mail server in detached mode.
*   To check logs: `docker-compose logs -f mailserver` or `docker logs -f mailserver` (if you used `container_name: mailserver`).
*   It might take a few minutes for the server to initialize, especially on the first run and if generating SSL certificates.

---

## Step 5: Create the API Email User

Once the container is running, you need to create the email account that your API will use.

**Action:**

1.  Find your container name or ID: `docker ps` (look for `mailserver/docker-mailserver`).
2.  Execute the setup command (replace `<container_name_or_id>`, `api-user@yourdomain.com`, and `strongpassword123` as needed):

    ```bash
    docker exec -ti <container_name_or_id> setup email add api-user@yourdomain.com strongpassword123
    ```
    For example, if your container is named `mailserver`:
    ```bash
    docker exec -ti mailserver setup email add api-user@yourdomain.com YourChosenStrongPassword!
    ```

---

## Step 6: Generate DKIM Keys and Configure DNS

DomainKeys Identified Mail (DKIM) helps prevent email spoofing and improves deliverability.

**Action:**

1.  Generate DKIM keys for your domain (replace `<container_name_or_id>` and `yourdomain.com`):
    ```bash
    docker exec -ti <container_name_or_id> setup config dkim keysize 2048 domain yourdomain.com
    ```
    Example:
    ```bash
    docker exec -ti mailserver setup config dkim keysize 2048 domain yourdomain.com
    ```

2.  **Locate the DKIM Public Key:** The command will output the public key. It will also be saved on your Docker host inside the `config` volume you mapped. The typical location for the DNS record content is:
    *   `./docker-data/dms/config/opendkim/keys/yourdomain.com/mail.txt`
    *   (Inside the container: `/tmp/docker-mailserver/opendkim/keys/yourdomain.com/mail.txt`)

    Open this `mail.txt` file (e.g., `cat /opt/email_server/docker-data/dms/config/opendkim/keys/yourdomain.com/mail.txt`). You will see something like:
    ```
    mail._domainkey IN TXT ( "v=DKIM1; h=sha256; k=rsa; "
      "p=MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAyourPublicKeyString..."
      "..."
    ) ; ----- DKIM key mail for yourdomain.com
    ```

3.  **Add DKIM TXT Record to DNS:**
    *   Name: `mail._domainkey` (the `mail` part is the "selector", specified by `docker-mailserver`)
    *   Type: `TXT`
    *   Value: The entire content within the parentheses, joined into a single string. Remove quotes and newlines.
        Example: `v=DKIM1; h=sha256; k=rsa; p=MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAyourPublicKeyString...`

---

## Step 7: Configure SPF Record

Sender Policy Framework (SPF) specifies which mail servers are authorized to send email for your domain.

**Action:**

1.  **Add SPF TXT Record to DNS:**
    *   Name: `@` or `yourdomain.com`
    *   Type: `TXT`
    *   Value: `v=spf1 mx -all`
        *   `v=spf1`: SPF version 1.
        *   `mx`: Allows servers listed in your MX records to send mail.
        *   `-all`: Mails from servers not listed are explicitly unauthorized (you can use `~all` for a softer fail, but `-all` is generally recommended).
    *   If you send email for your domain from other services (e.g., a newsletter service), you'll need to include them in your SPF record (e.g., `v=spf1 mx include:sendgrid.net -all`).

---

## Step 8: (Recommended) Configure DMARC Record

DMARC (Domain-based Message Authentication, Reporting & Conformance) tells receiving mail servers what to do if an email fails SPF and/or DKIM checks.

**Action:**

1.  **Add DMARC TXT Record to DNS:**
    *   Name: `_dmarc`
    *   Type: `TXT`
    *   Value (start with a simple monitoring policy): `v=DMARC1; p=none; rua=mailto:dmarc-reports@yourdomain.com; ruf=mailto:dmarc-reports@yourdomain.com; fo=1`
        *   `p=none`: Take no action on failing emails, just report. You can later change to `quarantine` or `reject`.
        *   `rua=mailto:dmarc-reports@yourdomain.com`: Where to send aggregate reports. Create this email address in your mail server or use a third-party DMARC reporting service.
        *   `ruf=mailto:dmarc-reports@yourdomain.com`: Where to send forensic reports.
    *   You'll need to create the `dmarc-reports@yourdomain.com` user/alias in your mail server or use an external service to receive these reports.
        ```bash
        docker exec -ti mailserver setup email add dmarc-reports@yourdomain.com YourPasswordForDmarcReports
        # Or alias it:
        # docker exec -ti mailserver setup alias add dmarc-reports@yourdomain.com postmaster@yourdomain.com
        ```

---

## Step 9: Test Email Sending with `test_email.py`

Now, use the provided Python script to send a test email.

**Action:**

1.  Ensure `test_email.py` is customized with your server details, sender email, password, and recipient email (as per Step 1).
2.  Make sure Python 3 is installed on the machine where you're running the script.
3.  Run the script:
    ```bash
    python3 test_email.py
    ```
4.  **Check the output:**
    *   Look for "Email sent successfully!"
    *   If there are errors, the script provides some common troubleshooting tips.
    *   Check the recipient's inbox (and spam folder).
5.  **Check Mail Server Logs:**
    *   `docker-compose logs -f mailserver` or `docker logs -f mailserver`
    *   These logs are invaluable for diagnosing issues.

**Troubleshooting `test_email.py`:**
*   **Connection Refused:**
    *   Is `MAIL_SERVER` in the script correct? (e.g., `localhost` if on the same machine, or the server's public IP).
    *   Is the `docker-mailserver` container running? (`docker ps`)
    *   Is the port correct (`587`) and is the Docker port mapping correct in `docker-compose.yml`?
    *   Is your server's firewall blocking the connection?
*   **Authentication Error:**
    *   Are `SENDER_EMAIL` and `SENDER_PASSWORD` in the script correct?
    *   Did you successfully create the user with `docker exec ... setup email add ...`?
*   **SSL Errors:**
    *   If using `SSL_TYPE=self-signed`, clients will issue warnings. The script uses `ssl.create_default_context()`, which might struggle with self-signed certs without further configuration. For testing, you might temporarily need to use a less strict context (not recommended for production).
    *   `SSL_TYPE=letsencrypt` should resolve this if the certificate was obtained successfully. Check the mail server logs for Let's Encrypt status.
*   **Timeout:** Server might be slow, network issue, or firewall dropping packets.

---

## Step 10: Final Checks and Next Steps

*   **DNS Propagation:** DNS changes can take time to propagate (minutes to 48 hours). Use tools like `nslookup`, `dig`, or online DNS checkers (e.g., mxtoolbox.com) to verify your A, MX, TXT (SPF, DKIM, DMARC) records are correct.
*   **Email Deliverability:**
    *   Send test emails to various providers (Gmail, Outlook, Yahoo) and check if they land in the inbox or spam.
    *   Use tools like `mail-tester.com` to analyze your email setup and get a score. This will help identify issues with SPF, DKIM, PTR, blacklists, etc.
*   **Security:**
    *   **Change `strongpassword123`!**
    *   Keep your `docker-mailserver` image updated: `docker-compose pull mailserver` then `docker-compose up -d mailserver`.
    *   Consider enabling `ENABLE_FAIL2BAN=1` in `mailserver.env` for production to block IPs that try to brute-force logins.
    *   Regularly review logs: `docker logs mailserver`.

---

You now have a basic `docker-mailserver` setup. You can proceed to integrate email sending capabilities into your Python API, using `api-user@yourdomain.com` to authenticate with the mail server.
Remember that running a mail server comes with responsibilities regarding security, maintenance, and ensuring good sending practices to avoid being blacklisted.

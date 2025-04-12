# Jureli - SMTP Testing Tool 🐦

<p align="center">
  <i>(Jureli is a common bird found in Nepal🇳🇵)</i>
</p>

A simple, web-based SMTP testing tool built with Flask and packaged with Docker. Jureli allows you to easily test connectivity and authentication with any SMTP server and send test emails by providing all configuration details directly through the web interface.

## Features

*   Test SMTP connections: Specify server, port, username, password, and connection security (None/TLS/SSL) directly in the form.
*   Send test emails: Define Sender (Email & optional Display Name), Recipient(s), Subject, and Body.
*   Multiple Recipients: Send to several email addresses at once (comma-separated).
*   File Attachments: Attach one or multiple files to your test emails.
*   Web-Based Interface: All configuration and email details are entered via the browser, ideal for quick tests without managing environment files for credentials.
*   Flask & Gunicorn: Built with the Flask microframework and served using the robust Gunicorn WSGI server.
*   Dockerized: Easy to set up and run using Docker and Docker Compose.

## Prerequisites

Before you begin, ensure you have the following installed on your system:

*   [Docker](https://docs.docker.com/get-docker/)
*   [Docker Compose](https://docs.docker.com/compose/install/) (v1.28.0+ recommended. Often included with Docker Desktop).

## Setup

1.  **Get the Project Files:**
    Clone the repository or download the project files (`Dockerfile`, `docker-compose.yml`, `app.py`, `requirements.txt`, `templates/index.html`). Navigate to the root directory of the project in your terminal.

2.  **Configure Flask Secret Key (Optional but Recommended):**
    This application uses Flask's session mechanism for displaying success/error messages (`flash()`). For this to work securely, a secret key is needed. Create a file named `.env` in the project root directory. Add the following line, replacing the placeholder with a strong, random key:

    ```dotenv
    # --- .env file contents ---
    # A strong, random secret key for Flask session security.
    # Generate one using: python -c 'import secrets; print(secrets.token_hex(16))'
    FLASK_SECRET_KEY=replace_with_a_strong_random_secret_key
    # --- End of .env file ---
    ```
    *   **Important:** Only the `FLASK_SECRET_KEY` goes in this file. All SMTP details are entered via the web UI.
    *   If you skip creating the `.env` file, a default (less secure) key within `app.py` will be used.
    *   **Do not commit `.env` to version control.** Add it to your `.gitignore` file if applicable.

## Running the Application

1.  **Build and Start:**
    Open your terminal in the project root directory (where `docker-compose.yml` resides) and run:
    ```bash
    docker-compose up --build -d
    ```
    *   `--build`: Builds the Docker image based on the `Dockerfile`. This is necessary the first time or if you modify application code (`app.py`, `index.html`), `requirements.txt`, or `Dockerfile`.
    *   `-d`: Runs the container in detached mode (in the background).

2.  **Start (If image already built):**
    If the image exists from a previous build and no relevant files have changed, you can simply start the application using:
    ```bash
    docker-compose up -d
    ```

## Accessing the Application

Once the container is running successfully, open your web browser and navigate to:

[http://localhost:6001](http://localhost:6001)

*(This assumes you are using the default port mapping `6001:5000` specified in the `docker-compose.yml` file. If you changed the host port (the first number), adjust the URL accordingly.)*

## Usage

1.  Navigate to the Jureli application URL in your browser.
2.  Fill in the **SMTP Configuration** section:
    *   **SMTP Server:** The address of the mail server (e.g., `smtp.gmail.com`).
    *   **Port:** The connection port (e.g., `587`, `465`, `25`).
    *   **Connection Security:** Choose `Use STARTTLS`, `Use SSL`, or `None` based on the server's requirements for the chosen port.
    *   **SMTP Username:** Your login username for the mail server.
    *   **SMTP Password:** Your login password. Use an **App Password** if required by your provider (e.g., Gmail, Microsoft 365).
3.  Fill in the **Email Details** section:
    *   **Sender Display Name:** (Optional) The name recipients will see.
    *   **Sender Email Address:** The email address the message will appear to be from. Ensure this address is allowed to send via the provided SMTP credentials/server configuration.
    *   **To Recipient(s):** One or more email addresses, separated by commas.
    *   **Subject:** The subject line of the email.
    *   **Body:** The main content of the email.
4.  Optionally, use the **Attachments** field to upload one or more files.
5.  Click the **Send Test Email** button.
6.  A success or error message will appear at the top of the page indicating the result of the sending attempt.

**Note:** SMTP configuration details are **not stored** by the application and must be entered each time you wish to send a test email.

## Stopping the Application

To stop and remove the containers, network, and volumes defined in `docker-compose.yml`, run the following command in the project root directory:

```bash
docker-compose down
```
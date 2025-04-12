# --- START OF FILE app.py ---

import os
import smtplib
from email.utils import formataddr, encode_rfc2231
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from flask import Flask, render_template, request, flash, redirect, url_for
from dotenv import load_dotenv
import logging

# Load environment variables from .env file (primarily for FLASK_SECRET_KEY now)
load_dotenv()

app = Flask(__name__)
# FLASK_SECRET_KEY is still needed for session management (flash messages)
# Use env var or provide a fallback (change fallback for production/sharing)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'you-really-should-set-a-secret-key-in-env')

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Helper Function for Formatting SMTP Errors ---
# (Keep this function as it's useful for displaying errors)
def format_smtp_error_message(error_data):
    """Decodes SMTP error data (bytes or str) and cleans it for display."""
    message = ""
    if isinstance(error_data, bytes):
        try:
            message = error_data.decode('utf-8', errors='replace')
        except Exception as decode_error:
            app.logger.warning(f"Could not decode SMTP error bytes: {decode_error}. Falling back to str(). Error data: {error_data}")
            message = str(error_data)
    elif isinstance(error_data, str):
        message = error_data
    else:
        message = str(error_data)
    return message.replace('\n', ' ').strip()

# --- Input Validation Helper ---
def is_valid_email_list(email_string):
    """Basic check for comma-separated emails."""
    # This function remains the same as it validates the 'To' and 'From' fields
    if not email_string:
        return False, "Email address field cannot be empty." # Generic message
    emails = [e.strip() for e in email_string.split(',') if e.strip()]
    if not emails:
        return False, "No valid email addresses provided after parsing."
    invalid_emails = []
    for email in emails:
        parts = email.split('@')
        if len(parts) != 2 or not parts[0] or not parts[1] or '.' not in parts[1]:
             invalid_emails.append(email)
    if invalid_emails:
        return False, f"Invalid email format detected for: {', '.join(invalid_emails)}"
    return True, emails

# --- Routes ---
@app.route('/')
def index():
    """Displays the SMTP testing form."""
    # No config validation needed here anymore
    return render_template('index.html')

@app.route('/send', methods=['POST'])
def send_email():
    """Handles email sending logic using parameters from the form."""

    # --- Get SMTP Configuration from Form ---
    smtp_server = request.form.get('smtp_server')
    smtp_port_str = request.form.get('smtp_port')
    smtp_username = request.form.get('smtp_username')
    smtp_password = request.form.get('smtp_password')
    connection_security = request.form.get('connection_security') # 'tls', 'ssl', or 'none'

    # --- Get Email Details from Form ---
    display_name = request.form.get('display_name', '').strip()
    from_email_addr = request.form.get('from_email')
    to_email_str = request.form.get('to_email')
    subject = request.form.get('subject')
    body = request.form.get('body')
    attachments = request.files.getlist('attachments')

    # --- Basic Input Validation ---
    required_fields = {
        'SMTP Server': smtp_server,
        'SMTP Port': smtp_port_str,
        'SMTP Username': smtp_username,
        'SMTP Password': smtp_password, # Password presence check only
        'Connection Security': connection_security,
        'Sender Email Address': from_email_addr,
        'To Recipient(s)': to_email_str,
        'Subject': subject,
        'Body': body
    }
    missing = [name for name, value in required_fields.items() if not value]
    if missing:
        flash(f"Missing required fields: {', '.join(missing)}. Please fill in all required fields.", "error")
        return redirect(url_for('index'))

    # Validate Port
    try:
        smtp_port = int(smtp_port_str)
        if not 1 <= smtp_port <= 65535:
            raise ValueError("Port out of range")
    except ValueError:
        flash(f"Invalid SMTP Port specified: '{smtp_port_str}'. Must be a number between 1 and 65535.", "error")
        return redirect(url_for('index'))

    # Validate To Emails
    is_to_valid, to_result = is_valid_email_list(to_email_str)
    if not is_to_valid:
        flash(f"Error in 'To Recipient(s)': {to_result}", 'error')
        return redirect(url_for('index'))
    to_emails_list = to_result

    # Validate From Email
    is_from_valid, from_result = is_valid_email_list(from_email_addr)
    if not is_from_valid:
        flash(f"Error in 'Sender Email Address': {from_result}", 'error')
        return redirect(url_for('index'))
    # --- End Validation ---


    # --- Determine Connection Settings ---
    use_ssl = (connection_security == 'ssl')
    use_tls = (connection_security == 'tls')
    # Note: 'none' means use_ssl=False and use_tls=False


    # --- Construct Email Message ---
    # (This part remains largely the same)
    msg = MIMEMultipart()
    if display_name:
        msg['From'] = formataddr((display_name, from_email_addr))
    else:
        msg['From'] = from_email_addr
    msg['To'] = ", ".join(to_emails_list)
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    # Attach files
    for f in attachments:
        if f and f.filename:
            try:
                part = MIMEBase('application', 'octet-stream')
                payload = f.read()
                part.set_payload(payload)
                encoders.encode_base64(part)
                filename_for_header = f.filename
                try:
                    filename_for_header.encode('ascii')
                    filename_header = f'attachment; filename="{filename_for_header}"'
                except UnicodeEncodeError:
                    filename_header = f"attachment; filename*={encode_rfc2231(filename_for_header, charset='utf-8')}"
                part.add_header('Content-Disposition', filename_header)
                msg.attach(part)
                app.logger.info(f"Successfully attached file: {filename_for_header}")
            except Exception as e:
                 app.logger.error(f"Error attaching file '{f.filename}': {e}", exc_info=True)
                 flash(f"Error attaching file '{f.filename}'. Please try again or skip the file.", "error")
                 return redirect(url_for('index'))


    # --- Send Email via SMTP (using form parameters) ---
    server = None
    try:
        if use_ssl:
            app.logger.info(f"Connecting via SMTP_SSL to {smtp_server}:{smtp_port}")
            server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=20)
        else:
            app.logger.info(f"Connecting via SMTP to {smtp_server}:{smtp_port}")
            server = smtplib.SMTP(smtp_server, smtp_port, timeout=20)
            if use_tls:
                app.logger.info("Starting TLS...")
                server.starttls()
                app.logger.info("TLS started.")

        # Login using credentials from the form
        app.logger.info(f"Attempting login as {smtp_username}...")
        server.login(smtp_username, smtp_password)
        app.logger.info("Login successful.")

        # Send the email
        # Envelope sender might need to match smtp_username for many servers
        # Using from_email_addr allows testing 'Send As' functionality
        envelope_sender = from_email_addr
        app.logger.info(f"Sending email. From (envelope): {envelope_sender}, To: {to_emails_list}")
        server.sendmail(envelope_sender, to_emails_list, msg.as_string())
        app.logger.info("Email sent successfully.")

        flash(f"Test email successfully sent via {smtp_server} to: {', '.join(to_emails_list)}!", "success")

    # --- Exception Handling (using format_smtp_error_message) ---
    # (This part remains largely the same, but error messages don't mention .env)
    except smtplib.SMTPAuthenticationError:
        app.logger.error("SMTP Authentication Error.", exc_info=False)
        flash(f"SMTP Authentication Error: Incorrect username ('{smtp_username}') or password provided. Please check credentials.", "error")
    except smtplib.SMTPServerDisconnected:
        app.logger.error("SMTP Server Disconnected.", exc_info=True)
        flash("SMTP Server Disconnected unexpectedly. Please check server status.", "error")
    except smtplib.SMTPConnectError as e:
        app.logger.error(f"SMTP Connection Error: {e}", exc_info=True)
        flash(f"SMTP Connection Error: Could not connect to {smtp_server}:{smtp_port}. Check server address, port, and security setting. Also check firewalls.", "error")
    except smtplib.SMTPRecipientsRefused as e:
        app.logger.error(f"SMTP Recipient Refused: {e.recipients}", exc_info=False)
        refused_dict = {email: f"{code} {format_smtp_error_message(msg_bytes)}" for email, (code, msg_bytes) in e.recipients.items()}
        refused_str = ", ".join([f"{email}: {reason}" for email, reason in refused_dict.items()])
        flash(f"Recipient(s) refused by server: {refused_str}. Check email addresses.", "error")
    except smtplib.SMTPHeloError as e:
        app.logger.error(f"SMTP HELO/EHLO Error: {e}", exc_info=True)
        server_message = format_smtp_error_message(e.smtp_error)
        flash(f"Server HELO/EHLO Error ({e.smtp_code}): {server_message}.", "error")
    except smtplib.SMTPSenderRefused as e:
        app.logger.error(f"SMTP Sender Refused: {e.sender}", exc_info=False)
        server_message = format_smtp_error_message(e.smtp_error)
        flash(f"Sender address '{e.sender}' refused by server ({e.smtp_code}): '{server_message}'. Check 'Sender Email Address' or server permissions (envelope sender might need to match authenticated user '{smtp_username}').", "error")
    except smtplib.SMTPDataError as e:
         app.logger.error(f"SMTP Data Error: Code={e.smtp_code}, Msg={e.smtp_error}", exc_info=False)
         server_message = format_smtp_error_message(e.smtp_error)
         flash_msg = f"Server Data Error ({e.smtp_code}): The server refused the message data."
         if server_message:
              flash_msg += f" Reason: '{server_message}'"
         lower_server_msg = server_message.lower()
         if "domain not verified" in lower_server_msg or "sender verification" in lower_server_msg or "sender address rejected" in lower_server_msg:
              flash_msg += f" Ensure the 'Sender Email Address' ('{from_email_addr}') or its domain is verified/permitted by the SMTP provider."
         flash(flash_msg, "error")
    except TimeoutError:
        app.logger.error(f"SMTP Timeout Error connecting/sending to {smtp_server}:{smtp_port}", exc_info=True)
        flash("SMTP Timeout Error: The connection timed out. Check server address, port, and network connectivity.", "error")
    except OSError as e:
        app.logger.error(f"Network/OS Error: {e}", exc_info=True)
        flash(f"Network Error: Could not communicate with the server ({e}). Check network connection.", "error")
    except Exception as e:
        app.logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        flash(f"An unexpected error occurred: {type(e).__name__}. Please check the application logs for details.", "error")
    finally:
        if server:
            try:
                app.logger.info("Closing SMTP connection.")
                server.quit()
            except Exception:
                 pass # Ignore errors during quit

    # Redirect back to index, preserving form inputs is complex, so we just redirect.
    # User will need to re-enter details if an error occurs.
    return redirect(url_for('index'))


if __name__ == '__main__':
    # Debug mode is useful for development, but use environment variable for production
    is_debug_mode = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(host='0.0.0.0', port=5000, debug=is_debug_mode)

# --- END OF FILE app.py ---
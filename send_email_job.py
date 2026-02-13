import os
import sys
import time
import smtplib
import socket
from email.message import EmailMessage

from dotenv import load_dotenv


def build_email_body():
    return """Greetings from Aantre 🎶

Thank you for your patience while we prepared your custom audio mashup. Your file has been successfully generated and is attached to this email in ZIP format.

We carefully compiled and blended the selected tracks to give you a smooth, high-energy listening experience. We hope you truly enjoy the mashup and share it with your friends and audience.

If you have any feedback, feature requests, or would like another mashup created with different artists or durations, feel free to reply to this email — we’d love to build it for you.

Thank you for choosing Aantre.

Warm regards,
Nihar Sharma
"""


def send_email(to_email, zip_path, retries=5):
    load_dotenv(override=True)

    socket.setdefaulttimeout(120)

    sender = os.getenv("MASHMIX_EMAIL")
    app_password = os.getenv("MASHMIX_APP_PASSWORD")
    if not sender or not app_password:
        print("Email credentials not set.")
        return False

    if not os.path.exists(zip_path):
        print(f"Zip file not found: {zip_path}")
        return False

    msg = EmailMessage()
    msg["Subject"] = "Your MashMix Audio Mashup is Ready"
    msg["From"] = sender
    msg["To"] = to_email
    msg.set_content(build_email_body())

    with open(zip_path, "rb") as f:
        msg.add_attachment(
            f.read(),
            maintype="application",
            subtype="zip",
            filename="mashmix.zip",
        )

    methods = [
        ("smtp.gmail.com", 465, "ssl"),
        ("smtp.gmail.com", 587, "starttls"),
    ]

    for attempt in range(retries):
        for host, port, mode in methods:
            try:
                print(
                    f"Sending email via Gmail ({mode}) attempt {attempt + 1}/{retries}..."
                )
                if mode == "ssl":
                    with smtplib.SMTP_SSL(host, port, timeout=120) as s:
                        s.ehlo()
                        s.login(sender, app_password)
                        s.send_message(msg)
                else:
                    with smtplib.SMTP(host, port, timeout=120) as s:
                        s.ehlo()
                        s.starttls()
                        s.ehlo()
                        s.login(sender, app_password)
                        s.send_message(msg)

                print(f"Email sent to {to_email}")
                return True
            except smtplib.SMTPAuthenticationError:
                print("Gmail authentication failed. Check credentials.")
                return False
            except Exception as e:
                print(f"{mode} attempt failed: {str(e)}")

        if attempt < retries - 1:
            time.sleep(2)

    print("Email failed after retries")
    return False


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python send_email_job.py <to_email> <zip_path>")
        sys.exit(1)

    success = send_email(sys.argv[1], sys.argv[2])
    sys.exit(0 if success else 1)

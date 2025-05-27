import smtplib
import random
from email.message import EmailMessage
import os
import logging

# Setup logging
logging.basicConfig(filename="auth.log", level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')

def send_otp(to_email):
    """Send OTP to the specified email."""
    try:
        smtp_email = os.getenv('SMTP_EMAIL', 'your_email@gmail.com')
        smtp_password = os.getenv('SMTP_PASSWORD', 'your_app_password')
        if not smtp_email or not smtp_password:
            logging.error("SMTP_EMAIL or SMTP_PASSWORD not set in environment variables.")
            return None

        otp = str(random.randint(100000, 999999))  # 6-digit OTP
        msg = EmailMessage()
        msg.set_content(f"Your VoiceAuth OTP is: {otp}")
        msg['Subject'] = 'VoiceAuth: OTP Verification'
        msg['From'] = smtp_email
        msg['To'] = to_email

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(smtp_email, smtp_password)
            smtp.send_message(msg)
        logging.info(f"OTP sent to {to_email}.")
        return otp
    except Exception as e:
        logging.error(f"Failed to send OTP to {to_email}: {e}")
        return None
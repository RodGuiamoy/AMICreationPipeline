import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.message import EmailMessage
import sys

def send_email(smtp_server, sender_email, recipient_email, subject, email_body_file_path):
    # Read email body from the specified file
    with open(email_body_file_path, 'r') as f:
        body = f.read()

    # Create the email headers and body
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject

    # Attach the email body
    msg.attach(MIMEText(body, 'html'))

    try:
        # Connect to the SMTP server
        server = smtplib.SMTP(smtp_server)
    
        # Send the email
        server.sendmail(sender_email, recipient_email, msg.as_string())
        print(f"Email sent successfully to {recipient_email}")

    except Exception as e:
        print(f"Error: {str(e)}")

    finally:
        server.quit()

if len(sys.argv) < 6:
    print("Usage: python script.py <smtp_server> <sender_email> <recipient_email> <subject> <html_file_path>")
    sys.exit(1)

smtp_server = sys.argv[1]
sender_email = sys.argv[2]
recipient_email = sys.argv[3]
subject = sys.argv[4]
email_body_file_path = sys.argv[5]

send_email(smtp_server, sender_email, recipient_email, subject, email_body_file_path)

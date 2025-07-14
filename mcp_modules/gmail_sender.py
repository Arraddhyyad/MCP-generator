import os
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials


def send_email_with_attachments(to_email: str, subject: str, body: str, attachments: list, creds_path: str = "token.json") -> dict:
    """
    Sends an email with attachments via Gmail API.

    Args:
        to_email: Recipient's email address
        subject: Email subject
        body: Email body
        attachments: List of file paths
        creds_path: Path to Gmail API credentials JSON

    Returns:
        Gmail API send response
    """
    creds = Credentials.from_authorized_user_file(creds_path, ['https://www.googleapis.com/auth/gmail.send'])
    service = build('gmail', 'v1', credentials=creds)

    message = MIMEMultipart()
    message['to'] = to_email
    message['subject'] = subject
    message.attach(MIMEText(body, 'plain'))

    for file_path in attachments:
        filename = os.path.basename(file_path)
        with open(file_path, 'rb') as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename="{filename}"')
            message.attach(part)

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return service.users().messages().send(userId="me", body={'raw': raw}).execute()

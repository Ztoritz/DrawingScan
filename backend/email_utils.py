from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr
from typing import List
import os
from dotenv import load_dotenv

load_dotenv()

conf = ConnectionConfig(
    MAIL_USERNAME=os.environ.get("MAIL_USERNAME"),
    MAIL_PASSWORD=os.environ.get("MAIL_PASSWORD"),
    MAIL_FROM=os.environ.get("MAIL_FROM"),
    MAIL_PORT=int(os.environ.get("MAIL_PORT", 587)),
    MAIL_SERVER=os.environ.get("MAIL_SERVER", "smtp.gmail.com"),
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

async def send_approval_request(new_user_email: str, approval_link: str):
    """
    Sends an email to the Admin requesting approval for a new user.
    """
    admin_email = os.environ.get("MAIL_USERNAME") # Admin is the sender
    
    html = f"""
    <h3>New User Registration</h3>
    <p>A new user has requested access:</p>
    <p><strong>Email:</strong> {new_user_email}</p>
    <br>
    <p>Click below to approve this user:</p>
    <a href="{approval_link}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Aprove User</a>
    """

    message = MessageSchema(
        subject="Action Required: New User Request",
        recipients=[admin_email],
        body=html,
        subtype=MessageType.html
    )

    fm = FastMail(conf)
    await fm.send_message(message)

async def send_password_reset(email: EmailStr, token: str):
    # TODO: Implement Reset Logic
    pass

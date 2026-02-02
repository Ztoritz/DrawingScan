from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr
from typing import List
import os
from dotenv import load_dotenv

load_dotenv()

async def get_email_config():
    try:
        return ConnectionConfig(
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
    except Exception as e:
        print(f"EMAIL CONFIG ERROR: {e}")
        return None

async def send_approval_request(new_user_email: str, approval_link: str):
    """
    Sends an email to the Admin requesting approval for a new user.
    Falls back to printing to console if email service is not configured.
    """
    admin_email = os.environ.get("MAIL_USERNAME")
    
    # FALLBACK: If no admin email configured, just log it.
    if not admin_email:
        print("\n" + "="*50)
        print(f" [MOCK EMAIL] To Admin: ACTION REQUIRED")
        print(f" New User: {new_user_email}")
        print(f" APPROVE LINK: {approval_link}")
        print("="*50 + "\n")
        return

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

    conf = await get_email_config()
    if conf:
        try:
            fm = FastMail(conf)
            await fm.send_message(message)
        except Exception as e:
            print(f"SMTP SEND ERROR: {e}")
            # Fallback to console even if config existed but connection failed
            print(f"MANUAL APPROVAL LINK: {approval_link}")
    else:
        print(f"MANUAL APPROVAL LINK (No Config): {approval_link}")

async def send_password_reset(email: EmailStr, token: str):
    # TODO: Implement Reset Logic
    pass

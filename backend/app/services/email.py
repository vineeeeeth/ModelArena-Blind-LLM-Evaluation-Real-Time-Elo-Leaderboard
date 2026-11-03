"""Email service – sends verification and password-reset emails via SMTP."""

from __future__ import annotations

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib

from app.core.config import get_settings
from app.core.logging import logger


async def _send_email(to: str, subject: str, html_body: str) -> None:
    settings = get_settings()
    msg = MIMEMultipart("alternative")
    msg["From"] = settings.smtp_from
    msg["To"] = to
    msg["Subject"] = subject
    msg.attach(MIMEText(html_body, "html"))

    try:
        await aiosmtplib.send(
            msg,
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_user or None,
            password=settings.smtp_password or None,
            use_tls=settings.smtp_tls,
            start_tls=False,
        )
        logger.info("email_sent", to=to, subject=subject)
    except Exception:
        logger.exception("email_send_failed", to=to, subject=subject)
        raise


async def send_verification_email(
    email: str, token: str, frontend_url: str
) -> None:
    verify_link = f"{frontend_url}/verify-email?token={token}"
    html = f"""
    <html>
    <body>
        <h2>Welcome to ModelArena!</h2>
        <p>Please verify your email by clicking the link below:</p>
        <p><a href="{verify_link}">Verify Email</a></p>
        <p>Or copy this URL: {verify_link}</p>
        <p>This link expires in 24 hours.</p>
    </body>
    </html>
    """
    await _send_email(email, "Verify your ModelArena email", html)


async def send_password_reset_email(
    email: str, token: str, frontend_url: str
) -> None:
    reset_link = f"{frontend_url}/reset-password?token={token}"
    html = f"""
    <html>
    <body>
        <h2>Password Reset</h2>
        <p>Click the link below to reset your ModelArena password:</p>
        <p><a href="{reset_link}">Reset Password</a></p>
        <p>Or copy this URL: {reset_link}</p>
        <p>This link expires in 1 hour. If you did not request this, ignore this email.</p>
    </body>
    </html>
    """
    await _send_email(email, "Reset your ModelArena password", html)

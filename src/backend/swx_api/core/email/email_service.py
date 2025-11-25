"""
Email Service
-------------
This module provides functions for generating and sending emails using SMTP.

Features:
- `send_email()`: Sends an email via configured SMTP settings.
- `generate_test_email()`: Generates a test email.
- `generate_reset_password_email()`: Generates a password reset email.
- `generate_new_account_email()`: Generates an email for new user accounts.

The email sending functionality is currently **disabled**, and only email generation works.
"""

from dataclasses import dataclass

from swx_api.core.config.settings import settings
from swx_api.core.email.email_templates import render_email_template


@dataclass
class EmailData:
    """
    Data structure for storing email content.

    Attributes:
        html_content (str): The HTML body of the email.
        subject (str): The subject line of the email.
    """
    html_content: str
    subject: str


def send_email(*, email_to: str, subject: str = "", html_content: str = "") -> None:
    """
    Sends an email using the configured SMTP settings.

    **This function is currently disabled.**
    To enable it, uncomment the SMTP implementation below.

    Args:
        email_to (str): The recipient's email address.
        subject (str, optional): The subject of the email. Defaults to "".
        html_content (str, optional): The HTML content of the email. Defaults to "".

    Raises:
        AssertionError: If SMTP configuration is missing.

    Logs:
        - Email sending status.
    """
    pass  # Disabled functionality

    # assert settings.emails_enabled, "Email configuration is missing!"

    # message = emails.Message(
    #     subject=subject,
    #     html=html_content,
    #     mail_from=(settings.EMAILS_FROM_NAME, settings.EMAILS_FROM_EMAIL),
    # )
    #
    # smtp_options = {
    #     "host": settings.SMTP_HOST,
    #     "port": settings.SMTP_PORT,
    #     "tls": settings.SMTP_TLS,
    #     "ssl": settings.SMTP_SSL,
    #     "user": settings.SMTP_USER,
    #     "password": settings.SMTP_PASSWORD,
    # }
    #
    # response = message.send(to=email_to, smtp=smtp_options)
    # logger.info(f"Email sent to {email_to} - Response: {response}")


def generate_test_email(email_to: str) -> EmailData:
    """
    Generates a test email for debugging purposes.

    Args:
        email_to (str): The recipient's email address.

    Returns:
        EmailData: A dataclass containing the subject and HTML content of the email.
    """
    project_name = settings.PROJECT_NAME
    subject = f"{project_name} - Test email"
    html_content = render_email_template(
        template_name="test_email.html",
        context={"project_name": settings.PROJECT_NAME, "email": email_to},
    )
    return EmailData(html_content=html_content, subject=subject)


def generate_reset_password_email(email_to: str, email: str, token: str) -> EmailData:
    """
    Generates an email for password reset requests.

    Args:
        email_to (str): The recipient's email address.
        email (str): The user's email address.
        token (str): The password reset token.

    Returns:
        EmailData: A dataclass containing the subject and HTML content of the email.
    """
    project_name = settings.PROJECT_NAME
    subject = f"{project_name} - Password recovery for user {email}"
    link = f"{settings.FRONTEND_HOST}/reset-password?token={token}"
    html_content = render_email_template(
        template_name="reset_password.html",
        context={
            "project_name": settings.PROJECT_NAME,
            "username": email,
            "email": email_to,
            "valid_hours": settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS,
            "link": link,
        },
    )
    return EmailData(html_content=html_content, subject=subject)


def generate_new_account_email(
    email_to: str, username: str, password: str
) -> EmailData:
    """
    Generates an email for newly created user accounts.

    Args:
        email_to (str): The recipient's email address.
        username (str): The username of the new account.
        password (str): The generated password for the account.

    Returns:
        EmailData: A dataclass containing the subject and HTML content of the email.
    """
    project_name = settings.PROJECT_NAME
    subject = f"{project_name} - New account for user {username}"
    html_content = render_email_template(
        template_name="new_account.html",
        context={
            "project_name": settings.PROJECT_NAME,
            "username": username,
            "password": password,
            "email": email_to,
            "link": settings.FRONTEND_HOST,
        },
    )
    return EmailData(html_content=html_content, subject=subject)

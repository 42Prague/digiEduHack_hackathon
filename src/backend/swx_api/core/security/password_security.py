"""
Password Security & Token Management
------------------------------------
This module provides:
- **Password hashing & verification** using bcrypt.
- **JWT-based password reset token generation & validation.**
- **Security mechanisms for handling authentication safely.**

Key Functions:
- `verify_password()`: Check if a plaintext password matches a hashed password.
- `get_password_hash()`: Hash a password securely.
- `generate_password_reset_token()`: Create a JWT token for password reset.
- `verify_password_reset_token()`: Validate and decode a password reset token.

"""

from datetime import datetime, timedelta, timezone

import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from passlib.context import CryptContext

from swx_api.core.config.settings import settings

# Password hashing context (bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plaintext password against a securely hashed password.

    Args:
        plain_password (str): The user-provided plaintext password.
        hashed_password (str): The stored bcrypt-hashed password.

    Returns:
        bool: True if the password is valid, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password securely using bcrypt.

    Args:
        password (str): The plaintext password.

    Returns:
        str: The hashed password.
    """
    return pwd_context.hash(password)


def generate_password_reset_token(email: str, auth_provider: str = "local") -> str | None:
    """
    Generate a JWT token for password reset.

    This function is only available for users with `auth_provider = local` (i.e., not social login users).

    Args:
        email (str): The email address associated with the user.
        auth_provider (str, optional): The authentication provider. Defaults to `"local"`.

    Returns:
        str | None: A JWT reset token, or None if the user uses a social login provider.
    """
    if auth_provider != "local":
        return None  # Social login users should reset passwords via their provider.

    # Set token expiration time (configurable via settings)
    expires = datetime.now(timezone.utc) + timedelta(
        hours=settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS
    )

    # Create JWT payload with expiration timestamp and user email
    encoded_jwt = jwt.encode(
        {"exp": expires.timestamp(), "sub": email, "auth_provider": "local"},
        settings.SECRET_KEY,
        algorithm=settings.PASSWORD_SECURITY_ALGORITHM,
    )
    return encoded_jwt


def verify_password_reset_token(token: str) -> str | None:
    """
    Verify and decode a password reset token.

    Args:
        token (str): The JWT reset token.

    Returns:
        str | None: The email associated with the reset token if valid, otherwise None.
    """
    try:
        # Decode the token using the application's secret key
        decoded_token = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.PASSWORD_SECURITY_ALGORITHM],
        )

        # Check if the token has expired
        if datetime.now(timezone.utc).timestamp() > decoded_token["exp"]:
            return None  # Token expired

        # Return the email stored in the token
        return str(decoded_token["sub"])

    except (ExpiredSignatureError, InvalidTokenError):
        return None  # Invalid or expired token

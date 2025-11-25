"""
Authentication Controller
----------------------
This module serves as the controller layer for authentication-related endpoints.

Features:
- Handles user authentication (local and social logins).
- Manages token refresh and user registration.
- Supports password recovery and reset.

Methods:
- `login_controller()`: Handles user login for local authentication.
- `login_social_user_controller()`: Handles login via social authentication providers.
- `refresh_token_controller()`: Refreshes an expired access token using a valid refresh token.
- `register_controller()`: Registers a new user.
- `logout_controller()`: Logs out a user by revoking the refresh token.
- `recover_password_controller()`: Sends a password reset email.
- `reset_password_controller()`: Resets a user's password and revokes existing tokens.
"""

from fastapi import HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm

from swx_api.core.models.common import Message
from swx_api.core.models.user import User, UserCreate, UserNewPassword
from swx_api.core.models.token import Token, TokenRefreshRequest
from swx_api.core.services.auth_service import (
    login_user_service,
    refresh_access_token_service,
    register_user_service,
    logout_service,
    recover_password_service,
    reset_password_service,
    login_social_user_service,
)


def login_controller(
    session, form_data: OAuth2PasswordRequestForm, request: Request = None
) -> Token:
    """
    Handles user login using email and password authentication.

    Args:
        session: The database session.
        form_data (OAuth2PasswordRequestForm): The login form data (username & password).
        request (Request, optional): The HTTP request object.

    Returns:
        Token: A dictionary containing the access token, refresh token, and token type.
    """
    return login_user_service(session, form_data, request)


def login_social_user_controller(session, form_data) -> Token:
    """
    Handles login for users authenticated via social authentication providers.

    Args:
        session: The database session.
        form_data: The social authentication user data.

    Returns:
        Token: A dictionary containing the access token, refresh token, and token type.
    """
    return login_social_user_service(session, form_data)


def refresh_token_controller(
    session, request_data: TokenRefreshRequest, request: Request
) -> Token:
    """
    Refreshes an expired access token using a valid refresh token.

    Args:
        session: The database session.
        request_data (TokenRefreshRequest): The refresh token request data.
        request (Request): The HTTP request object.

    Returns:
        Token: A dictionary containing the new access token, refresh token, and token type.
    """
    return refresh_access_token_service(session, request_data, request)


def register_controller(session, user_in: UserCreate, request: Request):
    """
    Registers a new user.

    Args:
        session: The database session.
        user_in (UserCreate): The user registration data.
        request (Request): The HTTP request object.

    Returns:
        User: The newly created user.
    """
    return register_user_service(session, user_in, request)


def logout_controller(session, request_data: TokenRefreshRequest, request: Request):
    """
    Logs out the user by revoking their refresh token.

    Args:
        session: The database session.
        request_data (TokenRefreshRequest): The refresh token to revoke.
        request (Request): The HTTP request object.

    Returns:
        dict: A message indicating successful logout.
    """
    return logout_service(session, request_data, request)


def recover_password_controller(
    email: str, session, request: Request = None
) -> Message:
    """
    Sends a password reset email to the user.

    Args:
        email (str): The user's email address.
        session: The database session.
        request (Request, optional): The HTTP request object.

    Returns:
        Message: A response indicating that the reset email has been sent.
    """
    return recover_password_service(email, session, request)


def reset_password_controller(
    session, body: UserNewPassword, request: Request = None
) -> Message:
    """
    Resets the user's password and revokes all active tokens.

    Args:
        session: The database session.
        body (UserNewPassword): The password reset request data.
        request (Request, optional): The HTTP request object.

    Returns:
        Message: A success message indicating that the password has been reset.
    """
    return reset_password_service(session, body, request)

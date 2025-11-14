"""
Authentication Service
----------------------
This module provides authentication-related services, including:
- User login (local and social authentication)
- Token management (access and refresh tokens)
- User registration
- Password recovery and reset

Methods:
- `login_user_service()`: Handles user login for local accounts.
- `login_social_user_service()`: Handles login via social authentication providers.
- `refresh_access_token_service()`: Generates a new access token using a valid refresh token.
- `register_user_service()`: Registers a new user.
- `logout_service()`: Revokes the refresh token to log a user out.
- `recover_password_service()`: Sends a password reset email.
- `reset_password_service()`: Resets a user's password and revokes existing tokens.
"""

from datetime import timedelta
from fastapi import HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm

from swx_api.core.config.settings import settings
from swx_api.core.email.email_service import generate_reset_password_email, send_email
from swx_api.core.models.common import Message
from swx_api.core.models.user import User, UserCreate, UserNewPassword
from swx_api.core.models.token import Token, TokenRefreshRequest
from swx_api.core.repositories.user_repository import (
    authenticate_user,
    create_user,
    get_user_by_email,
)
from swx_api.core.security.password_security import (
    generate_password_reset_token,
    verify_password_reset_token,
    get_password_hash,
)
from swx_api.core.security.refresh_token_service import (
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
    revoke_refresh_token,
    revoke_all_tokens,
)
from swx_api.core.utils.language_helper import translate


def login_user_service(
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
    existing_user = authenticate_user(
        session=session, email=form_data.username, password=form_data.password
    )
    if not existing_user:
        raise HTTPException(
            status_code=400, detail=translate(request, "incorrect_email_or_password")
        )
    if not existing_user.is_active:
        raise HTTPException(status_code=400, detail=translate(request, "inactive_user"))

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    access_token = create_access_token(
        existing_user.email, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(
        session, existing_user.email, expires_delta=refresh_token_expires
    )

    return Token(
        access_token=access_token, refresh_token=refresh_token, token_type="bearer"
    )


def login_social_user_service(session, user_email: str) -> Token:
    """
    Handles login for users authenticated via social authentication providers.

    Args:
        session: The database session.
        user_email (str): The email address of the user.

    Returns:
        Token: A dictionary containing the access token, refresh token, and token type.
    """
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    access_token = create_access_token(user_email, expires_delta=access_token_expires)
    refresh_token = create_refresh_token(
        session, user_email, expires_delta=refresh_token_expires
    )

    return Token(
        access_token=access_token, refresh_token=refresh_token, token_type="bearer"
    )


def refresh_access_token_service(
    session, request_data: TokenRefreshRequest, request: Request
) -> Token:
    """
    Generates a new access token using a valid refresh token.

    Args:
        session: The database session.
        request_data (TokenRefreshRequest): The refresh token request data.
        request (Request): The HTTP request object.

    Returns:
        Token: A dictionary containing the new access token, refresh token, and token type.
    """
    result = verify_refresh_token(session, request_data.refresh_token, request)
    if not result:
        raise HTTPException(
            status_code=401,
            detail=translate(request, "invalid_or_expired_refresh_token"),
        )
    email, auth_provider = result
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    new_access_token = create_access_token(
        email, expires_delta=access_token_expires, auth_provider=auth_provider
    )
    new_refresh_token = create_refresh_token(
        session, email, expires_delta=refresh_token_expires, auth_provider=auth_provider
    )
    return Token(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
    )


def register_user_service(session, user_in: UserCreate, request: Request):
    """
    Registers a new user account.

    Args:
        session: The database session.
        user_in (UserCreate): The user registration data.
        request (Request): The HTTP request object.

    Returns:
        User: The newly created user.
    """
    try:
        return create_user(session=session, user_create=user_in)
    except Exception:
        raise HTTPException(
            status_code=400, detail=translate(request, "user_already_exists")
        )


def logout_service(session, request_data: TokenRefreshRequest, request: Request):
    """
    Logs out the user by revoking their refresh token.

    Args:
        session: The database session.
        request_data (TokenRefreshRequest): The refresh token to revoke.
        request (Request): The HTTP request object.

    Returns:
        dict: A message indicating successful logout.
    """
    result = verify_refresh_token(session, request_data.refresh_token, request)
    if not result:
        raise HTTPException(
            status_code=401,
            detail=translate(request, "invalid_or_expired_refresh_token"),
        )
    revoked = revoke_refresh_token(session, request_data.refresh_token)
    if not revoked:
        raise HTTPException(
            status_code=401, detail=translate(request, "token_already_revoked")
        )
    return {"message": translate(request, "logged_out_successfully")}


def recover_password_service(email: str, session, request: Request = None) -> Message:
    """
    Sends a password reset email to the user.

    Args:
        email (str): The user's email address.
        session: The database session.
        request (Request, optional): The HTTP request object.

    Returns:
        Message: A response indicating that the reset email has been sent.
    """
    existing_user = get_user_by_email(session=session, email=email)
    if not existing_user:
        raise HTTPException(
            status_code=404, detail=translate(request, "user_email_not_found")
        )
    if existing_user.auth_provider != "local":
        raise HTTPException(
            status_code=400, detail=translate(request, "password_reset_not_available")
        )
    password_reset_token = generate_password_reset_token(email=email)
    email_data = generate_reset_password_email(
        email_to=existing_user.email, email=email, token=password_reset_token
    )
    send_email(
        email_to=existing_user.email,
        subject=email_data.subject,
        html_content=email_data.html_content,
    )
    return Message(message=translate(request, "password_recovery_email_sent_successfully"))


def reset_password_service(
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
    email = verify_password_reset_token(body.token)
    if not email:
        raise HTTPException(
            status_code=400, detail=translate(request, "invalid_or_expired_reset_token")
        )
    existing_user = get_user_by_email(session=session, email=email)
    if not existing_user:
        raise HTTPException(
            status_code=404, detail=translate(request, "user_not_found")
        )
    existing_user.hashed_password = get_password_hash(body.new_password)
    session.add(existing_user)
    session.commit()
    revoke_all_tokens(session, email)
    return Message(message=translate(request, "password_reset_successful"))

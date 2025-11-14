"""
Refresh Token & Authentication Token Management
----------------------------------------------
This module provides:
- **Access token generation** for authentication.
- **Refresh token generation, validation, and revocation**.
- **Token-based authentication using JWT (JSON Web Tokens).**
- **Secure storage & management of refresh tokens in the database.**

Key Functions:
- `create_access_token()`: Generates a short-lived access token.
- `create_refresh_token()`: Creates a refresh token stored in the database.
- `verify_refresh_token()`: Validates refresh tokens before issuing new access tokens.
- `revoke_refresh_token()`: Logs out a user by invalidating a refresh token.
- `revoke_all_tokens()`: Revokes all active refresh tokens (e.g., after password reset).
"""

import jwt
from fastapi import HTTPException, Request
from sqlmodel import Session, select
from datetime import datetime, timedelta, timezone

from swx_api.core.config.settings import settings
from swx_api.core.models.refresh_token import RefreshToken
from swx_api.core.utils.language_helper import translate


def create_access_token(
    email: str, expires_delta: timedelta, auth_provider: str = "local"
) -> str:
    """
    Generate a short-lived JWT access token.

    Args:
        email (str): The email of the authenticated user.
        expires_delta (timedelta): The expiration duration of the token.
        auth_provider (str, optional): The authentication provider (default: "local").

    Returns:
        str: The encoded JWT access token.
    """
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode = {
        "exp": expire.timestamp(),
        "sub": email,
        "auth_provider": auth_provider,
    }
    return jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.PASSWORD_SECURITY_ALGORITHM
    )


def create_refresh_token(
    session: Session, email: str, expires_delta: timedelta, auth_provider: str = "local"
) -> str:
    """
    Create or update a refresh token for the user.

    - If a refresh token exists, update it instead of creating a new one.
    - If no token exists, create a new refresh token.

    Args:
        session (Session): The database session.
        email (str): The email of the user.
        expires_delta (timedelta): The expiration duration of the refresh token.
        auth_provider (str, optional): The authentication provider (default: "local").

    Returns:
        str: The encoded JWT refresh token.
    """
    expire_at = datetime.now(timezone.utc) + expires_delta
    encoded_jwt = jwt.encode(
        {"exp": expire_at.timestamp(), "sub": email, "auth_provider": auth_provider},
        settings.REFRESH_SECRET_KEY,
        algorithm=settings.PASSWORD_SECURITY_ALGORITHM,
    )

    # Check if a refresh token already exists for this user
    existing_token = session.exec(
        select(RefreshToken).where(RefreshToken.user_email == email)
    ).first()

    if existing_token:
        # Update the existing refresh token
        existing_token.token = encoded_jwt
        existing_token.expires_at = expire_at
    else:
        # Create a new refresh token record
        new_refresh_token = RefreshToken(
            user_email=email, token=encoded_jwt, expires_at=expire_at
        )
        session.add(new_refresh_token)

    session.commit()
    return encoded_jwt


def verify_refresh_token(
    session: Session, refresh_token: str, request: Request
) -> tuple[str, str] | None:
    """
    Verify the refresh token and return (email, auth_provider) if valid.

    - Checks if the token exists in the database and is not expired.
    - Returns user email and authentication provider.

    Args:
        session (Session): The database session.
        refresh_token (str): The refresh token to verify.
        request (Request): The FastAPI request object for localization.

    Returns:
        tuple[str, str] | None: The email and auth provider if valid, otherwise None.

    Raises:
        HTTPException: If the token is invalid, revoked, or expired.
    """
    try:
        # Decode the JWT refresh token using the REFRESH_SECRET_KEY
        payload = jwt.decode(
            refresh_token,
            settings.REFRESH_SECRET_KEY,
            algorithms=[settings.PASSWORD_SECURITY_ALGORITHM],
        )
        email = payload.get("sub")
        auth_provider = payload.get("auth_provider", "local")

        if not email:
            raise HTTPException(
                status_code=401,
                detail=translate(request, "invalid_refresh_token_payload"),
            )

        # Validate that the token exists in the database
        db_token = session.exec(
            select(RefreshToken).where(RefreshToken.token == refresh_token)
        ).first()
        if not db_token:
            raise HTTPException(
                status_code=401,
                detail=translate(request, "invalid_or_revoked_refresh_token"),
            )

        # Ensure token expiration is timezone-aware (assume UTC if naive)
        token_exp = db_token.expires_at
        if token_exp.tzinfo is None:
            token_exp = token_exp.replace(tzinfo=timezone.utc)

        # Check if the token is expired
        if datetime.now(timezone.utc) > token_exp:
            raise HTTPException(
                status_code=401, detail=translate(request, "refresh_token_expired")
            )

        return email, auth_provider
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401, detail=translate(request, "refresh_token_expired")
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401, detail=translate(request, "invalid_refresh_token")
        )
    except Exception:
        raise HTTPException(
            status_code=401,
            detail=translate(request, "invalid_or_revoked_refresh_token"),
        )


def revoke_refresh_token(session: Session, refresh_token: str) -> bool:
    """
    Revoke a refresh token (logout).

    - Removes the refresh token from the database.
    - If the token is not found, it is considered already revoked.

    Args:
        session (Session): The database session.
        refresh_token (str): The refresh token to revoke.

    Returns:
        bool: True if the token is successfully revoked (or already revoked).
    """
    db_token = session.exec(
        select(RefreshToken).where(RefreshToken.token == refresh_token)
    ).first()
    if db_token:
        session.delete(db_token)
        session.commit()

    # Return True regardless to indicate that the token is no longer valid
    return True


def revoke_all_tokens(session: Session, email: str) -> None:
    """
    Revoke all refresh tokens for a user (e.g., after a password reset).

    Args:
        session (Session): The database session.
        email (str): The email of the user whose tokens should be revoked.
    """
    db_tokens = session.exec(
        select(RefreshToken).where(RefreshToken.user_email == email)
    ).all()
    for token in db_tokens:
        session.delete(token)
    session.commit()

"""
Refresh Token Management
------------------------
This module provides functions for managing refresh tokens in the authentication system.

Features:
- Supports token revocation for session invalidation.

Methods:
- `revoke_refresh_token()`: Deletes a refresh token from the database.
"""

from sqlmodel import Session
from swx_api.core.models.refresh_token import RefreshToken


def revoke_refresh_token(session: Session, token_str: str) -> bool:
    """
    Revoke a refresh token by removing it from the database.

    Args:
        session (Session): The database session.
        token_str (str): The refresh token string to be revoked.

    Returns:
        bool: True if the token was successfully revoked, False if the token was not found.
    """
    token = session.query(RefreshToken).filter(RefreshToken.token == token_str).first()
    if not token:
        return False
    session.delete(token)
    session.commit()
    return True

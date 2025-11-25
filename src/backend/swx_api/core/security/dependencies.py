"""
Authentication & Authorization Dependencies
-------------------------------------------
This module provides reusable security dependencies for:
- Extracting and validating JWT tokens.
- Retrieving the currently authenticated user.
- Enforcing role-based access control (RBAC).
- Ensuring only superusers can access certain routes.

Main Dependencies:
- `get_current_user()`: Retrieves and validates the current authenticated user.
- `get_current_active_superuser()`: Ensures the user has superuser privileges.
- `require_roles()`: Restricts access to users with specific roles.

"""

from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pydantic import ValidationError
from sqlmodel import select

from swx_api.core.config.settings import settings
from swx_api.core.database.db import SessionDep
from swx_api.core.models.token import TokenPayload
from swx_api.core.models.user import User
from swx_api.core.utils.language_helper import translate

# OAuth2 Bearer token authentication setup
reusable_oauth2 = OAuth2PasswordBearer(tokenUrl=f"{settings.ROUTE_PREFIX}/auth/login")
TokenDep = Annotated[str, Depends(reusable_oauth2)]  # Type alias for token dependency


def get_current_user(session: SessionDep, token: TokenDep, request: Request) -> User:
    """
    Retrieves and validates the currently authenticated user based on the provided JWT token.

    Args:
        session (SessionDep): The database session.
        token (TokenDep): The JWT token from the request header.
        request (Request): The HTTP request object.

    Returns:
        User: The authenticated user instance.

    Raises:
        HTTPException (401): If the token is invalid or expired.
        HTTPException (404): If the user is not found in the database.
        HTTPException (400): If the user account is inactive.
    """
    try:
        # Decode JWT token and extract user information
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.PASSWORD_SECURITY_ALGORITHM],
        )
        token_data = TokenPayload(**payload)
    except (InvalidTokenError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=translate(request, "could_not_validate_credentials"),
        )

    # Query the user from the database
    statement = select(User).where(User.email == token_data.sub)
    user = session.exec(statement).first()

    if not user:
        raise HTTPException(
            status_code=404, detail=translate(request, "user_not_found")
        )
    if not user.is_active:
        raise HTTPException(
            status_code=400, detail=translate(request, "inactive_user"),
        )

    return user


# Type alias for dependency injection to retrieve the authenticated user
CurrentUser = Annotated[User, Depends(get_current_user)]


def get_current_active_superuser(current_user: CurrentUser, request: Request) -> User:
    """
    Ensures that the current authenticated user has superuser privileges.

    Args:
        current_user (CurrentUser): The authenticated user.
        request (Request): The HTTP request object.

    Returns:
        User: The superuser instance.

    Raises:
        HTTPException (403): If the user lacks superuser privileges.
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=translate(request, "insufficient_privileges"),
        )
    return current_user


# Type alias for dependency injection to enforce superuser access
AdminUser = Annotated[User, Depends(get_current_active_superuser)]


def require_roles(*roles):
    """
    Factory function that generates a dependency to enforce role-based access control (RBAC).

    Example usage:
        ```python
        @router.get("/admin/dashboard", dependencies=[Depends(require_roles("admin", "superuser"))])
        ```

    Args:
        *roles (str): Variable-length list of required roles.

    Returns:
        Callable: A FastAPI dependency function that validates user roles.

    Raises:
        HTTPException (403): If the user lacks the required privileges.
    """

    def role_checker(current_user: CurrentUser, request: Request) -> User:
        """
        Checks if the current authenticated user has at least one of the required roles.

        Args:
            current_user (CurrentUser): The authenticated user.
            request (Request): The HTTP request object.

        Returns:
            User: The authenticated user if they have the required role.

        Raises:
            HTTPException (403): If the user lacks the required privileges.
        """
        if not any(getattr(current_user, role, False) for role in roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=translate(request, "user_lacks_required_privileges"),
            )
        return current_user

    return role_checker

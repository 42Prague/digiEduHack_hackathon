"""
User Profile Routes
-------------------
This module defines API routes for user profile management, including:
- Updating the current user profile.
- Fetching user details by ID.
- Changing user password.
- Deleting the user account.

Endpoints:
- `update_user_me()`: Update the current user's profile.
- `read_user_me()`: Retrieve the current user's profile information.
- `read_user_by_id()`: Retrieve user details by ID.
- `update_password()`: Change the current user's password.
- `delete_user_me()`: Delete the current user's account.
"""

from typing import Any
from uuid import UUID
from fastapi import APIRouter, HTTPException, Request

from swx_api.core.database.db import SessionDep
from swx_api.core.models.common import Message
from swx_api.core.models.user import UserPublic, UserUpdate, UserUpdatePassword
from swx_api.core.security.dependencies import CurrentUser
from swx_api.core.services.user_service import (
    update_user_profile_service,
    get_user_by_id_service,
    update_password_service,
    delete_user_service,
)
from swx_api.core.utils.language_helper import translate

# Define the router with a prefix for user profile-related operations
router = APIRouter(prefix="/user/profile")


@router.patch(
    "/",
    response_model=UserPublic,
    operation_id="update_current_user",
    status_code=200,
)
def update_user_me(
        session: SessionDep,
        user_in: UserUpdate,
        current_user: CurrentUser,
        request: Request,
) -> UserPublic:
    """
    Update the current user's profile.

    Args:
        session (SessionDep): The database session.
        user_in (UserUpdate): The updated user information.
        current_user (CurrentUser): The currently authenticated user.
        request (Request): The HTTP request object.

    Returns:
        UserPublic: The updated user profile.
    """
    return update_user_profile_service(session, user_in, current_user, request)


@router.get(
    "/",
    response_model=UserPublic,
    operation_id="get_current_user",
    status_code=200,
)
def read_user_me(current_user: CurrentUser) -> UserPublic:
    """
    Retrieve the currently authenticated user's profile.

    Args:
        current_user (CurrentUser): The currently authenticated user.

    Returns:
        UserPublic: The authenticated user's profile information.
    """
    return current_user


@router.get(
    "/{user_id}",
    response_model=UserPublic,
    operation_id="get_user_by_id",
    status_code=200,
)
def read_user_by_id(
        user_id: UUID,
        session: SessionDep,
        current_user: CurrentUser,
        request: Request,
) -> UserPublic:
    """
    Retrieve user details by their unique ID.

    Args:
        user_id (UUID): The ID of the user to retrieve.
        session (SessionDep): The database session.
        current_user (CurrentUser): The currently authenticated user.
        request (Request): The HTTP request object.

    Returns:
        UserPublic: The requested user's details.

    Raises:
        HTTPException: If the authenticated user attempts to access another user's details.
    """
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail=translate(request, "access_denied"))
    return get_user_by_id_service(session, user_id, current_user, request)


@router.patch(
    "/password/update",
    response_model=Message,
    operation_id="change_password",
    status_code=200,
)
def update_password(
        session: SessionDep,
        body: UserUpdatePassword,
        current_user: CurrentUser,
        request: Request,
) -> Message:
    """
    Change the current user's password.

    Args:
        session (SessionDep): The database session.
        body (UserUpdatePassword): The current and new passwords.
        current_user (CurrentUser): The currently authenticated user.
        request (Request): The HTTP request object.

    Returns:
        Message: A success message indicating password change.
    """
    return update_password_service(session, current_user.id, body, request)


@router.delete(
    "/delete",
    response_model=Message,
    operation_id="delete_current_user",
    status_code=200,
)
def delete_user_me(
        session: SessionDep,
        current_user: CurrentUser,
        request: Request = None,
) -> Message:
    """
    Delete the currently authenticated user's account.

    Args:
        session (SessionDep): The database session.
        current_user (CurrentUser): The currently authenticated user.
        request (Request, optional): The HTTP request object.

    Returns:
        Message: A success message indicating account deletion.
    """
    return delete_user_service(session, current_user, request)

"""
User Profile Service
----------------------
This module provides user profile management services, including:
- Profile updates
- Password updates
- User retrieval
- User deletion

Methods:
- `update_user_profile_service()`: Updates a user's profile information.
- `get_all_users_service()`: Retrieves a paginated list of all users.
- `get_user_by_id_service()`: Fetches user details by user ID.
- `update_password_service()`: Updates a user's password after verification.
- `delete_user_service()`: Deletes a user's account.
"""

from typing import List

from fastapi import HTTPException, Request

from swx_api.core.models.user import User
from swx_api.core.repositories.user_repository import (
    update_user,
    get_user_by_id,
    update_user_password,
    delete_user,
    get_all_users,
)
from swx_api.core.utils.language_helper import translate


def update_user_profile_service(session, user_in, current_user, request: Request):
    """
    Updates the profile information of the current user.

    Args:
        session: The database session.
        user_in: The updated user data.
        current_user: The currently authenticated user.
        request (Request): The HTTP request object.

    Returns:
        User: The updated user profile.
    """
    updated_user = update_user(session=session, db_user=current_user, user_in=user_in)
    return updated_user


def get_all_users_service(session, skip: int, limit: int):
    """
    Retrieves a paginated list of all users.

    Args:
        session: The database session.
        skip (int): The number of users to skip.
        limit (int): The maximum number of users to retrieve.

    Returns:
        List[User]: A list of user objects.
    """
    users = get_all_users(session, skip, limit)
    return users


def get_user_by_id_service(session, user_id, current_user, request: Request):
    """
    Retrieves user details by their unique ID.

    Args:
        session: The database session.
        user_id (str): The unique identifier of the user.
        current_user: The currently authenticated user.
        request (Request): The HTTP request object.

    Returns:
        User: The requested user object.

    Raises:
        HTTPException: If the user is not found.
    """
    user_obj = get_user_by_id(session, user_id)
    if not user_obj:
        raise HTTPException(
            status_code=404, detail=translate(request, "user_not_found")
        )
    return user_obj


def update_password_service(session, current_user, body, request: Request):
    """
    Updates the password for the authenticated user after verification.

    Args:
        session: The database session.
        current_user: The currently authenticated user.
        body: The password update request containing the old and new password.
        request (Request): The HTTP request object.

    Returns:
        dict: A success message confirming password update.

    Raises:
        HTTPException: If the password update fails.
    """
    updated = update_user_password(
        session, current_user, body.current_password, body.new_password
    )
    if not updated:
        raise HTTPException(
            status_code=400, detail=translate(request, "password_update_failed")
        )
    return {"message": translate(request, "password_updated_successfully")}


def delete_user_service(session, current_user, request: Request):
    """
    Deletes the authenticated user's account.

    Args:
        session: The database session.
        current_user: The currently authenticated user.
        request (Request): The HTTP request object.

    Returns:
        dict: A success message confirming account deletion.

    Raises:
        HTTPException: If the user deletion fails.
    """
    deleted = delete_user(session, current_user)
    if not deleted:
        raise HTTPException(
            status_code=400, detail=translate(request, "user_deletion_failed")
        )
    return {"message": translate(request, "user_deleted_successfully")}

"""
User Controller
----------------------
This module serves as the controller layer for user-related endpoints.

Features:
- Handles user profile management.
- Retrieves user information.
- Updates user profile and password.
- Deletes user accounts.

Methods:
- `update_user_controller()`: Updates the user's profile information.
- `get_current_user_controller()`: Returns the authenticated user's details.
- `get_user_by_id_controller()`: Retrieves user details by user ID.
- `get_all_users_controller()`: Fetches a paginated list of all users.
- `update_password_controller()`: Updates the user's password.
- `delete_user_controller()`: Deletes a user's account.
"""

from fastapi import HTTPException, Request

from swx_api.core.models.user import User, UserCreate, UserUpdate, UserUpdatePassword
from swx_api.core.security.dependencies import CurrentUser
from swx_api.core.services.user_service import (
    update_user_profile_service,
    get_user_by_id_service,
    update_password_service,
    delete_user_service,
    get_all_users_service,
)


def update_user_controller(
    session, user_in: UserUpdate, current_user: CurrentUser, request: Request
):
    """
    Updates the authenticated user's profile information.

    Args:
        session: The database session.
        user_in (UserUpdate): The user profile update data.
        current_user (CurrentUser): The currently authenticated user.
        request (Request): The HTTP request object.

    Returns:
        User: The updated user profile.
    """
    return update_user_profile_service(session, user_in, current_user, request)


def get_current_user_controller(current_user: CurrentUser):
    """
    Retrieves the authenticated user's details.

    Args:
        current_user (CurrentUser): The currently authenticated user.

    Returns:
        User: The authenticated user's details.
    """
    return current_user


def get_user_by_id_controller(
    session, user_id, current_user: CurrentUser, request: Request
):
    """
    Retrieves user details by their unique ID.

    Args:
        session: The database session.
        user_id (str): The unique identifier of the user.
        current_user (CurrentUser): The currently authenticated user.
        request (Request): The HTTP request object.

    Returns:
        User: The requested user object.

    Raises:
        HTTPException: If the user is not found.
    """
    return get_user_by_id_service(session, user_id, current_user, request)


def get_all_users_controller(session, skip: int, limit: int):
    """
    Retrieves a paginated list of all users.

    Args:
        session: The database session.
        skip (int): The number of users to skip.
        limit (int): The maximum number of users to retrieve.

    Returns:
        list[User]: A list of user objects.

    Raises:
        HTTPException: If no users are found.
    """
    users = get_all_users_service(session, skip, limit)
    if not users:
        raise HTTPException(status_code=404, detail="No users found")
    return users


def update_password_controller(
    session, current_user: CurrentUser, body: UserUpdatePassword, request: Request
):
    """
    Updates the authenticated user's password.

    Args:
        session: The database session.
        current_user (CurrentUser): The currently authenticated user.
        body (UserUpdatePassword): The password update request.
        request (Request): The HTTP request object.

    Returns:
        dict: A success message confirming password update.
    """
    return update_password_service(session, current_user, body, request)


def delete_user_controller(session, current_user: CurrentUser, request: Request):
    """
    Deletes the authenticated user's account.

    Args:
        session: The database session.
        current_user (CurrentUser): The currently authenticated user.
        request (Request): The HTTP request object.

    Returns:
        dict: A success message confirming account deletion.
    """
    return delete_user_service(session, current_user, request)

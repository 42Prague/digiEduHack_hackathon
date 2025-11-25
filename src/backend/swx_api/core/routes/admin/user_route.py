"""
Admin User Management Routes
----------------------------
This module defines API routes for **admin-level user management**, including:
- Retrieving all users.
- Fetching user details by ID.
- Creating new users.
- Updating user details.
- Deleting users.

Endpoints:
- `get_all_users()`: Retrieve a list of all users (Admin only).
- `get_user_by_id()`: Retrieve a user’s details by their ID (Admin only).
- `create_user()`: Create a new user (Admin only).
- `update_user()`: Update a user’s details (Admin only).
- `delete_user()`: Delete a user by ID (Admin only).
"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Request, HTTPException

from swx_api.core.controllers.auth_controller import register_controller
from swx_api.core.controllers.user_controller import (
    get_all_users_controller,
    get_user_by_id_controller,
    update_user_controller,
    delete_user_controller,
)
from swx_api.core.database.db import SessionDep
from swx_api.core.models.common import Message
from swx_api.core.models.user import UserPublic, UsersPublic, UserCreate, UserUpdate
from swx_api.core.security.dependencies import get_current_active_superuser, CurrentUser

# Define router with admin-level access dependency
router = APIRouter(
    prefix="/admin/user",
    dependencies=[Depends(get_current_active_superuser)],
)


@router.get("/", response_model=UsersPublic, status_code=200, operation_id="admin_get_all_users")
def get_all_users(session: SessionDep, skip: int = 0, limit: int = 100) -> UsersPublic:
    """
    Retrieve a list of all users (Admin only).

    Args:
        session (SessionDep): The database session.
        skip (int): Number of records to skip (pagination).
        limit (int): Maximum number of users to return.

    Returns:
        UsersPublic: A list of users with a total count.

    Raises:
        HTTPException: If no users are found.
    """
    users = get_all_users_controller(session, skip, limit)
    if not users:
        raise HTTPException(status_code=404, detail="No users found")
    return UsersPublic(data=users, count=len(users))


@router.get("/{user_id}", response_model=UserPublic, status_code=200,
            operation_id="admin_get_user_by_id")
def get_user_by_id(
        session: SessionDep,
        user_id: UUID,
        current_user: CurrentUser,
        request: Request = None,
) -> UserPublic:
    """
    Retrieve details of a specific user by ID (Admin only).

    Args:
        session (SessionDep): The database session.
        user_id (UUID): The unique ID of the user.
        current_user (CurrentUser): The authenticated admin user.
        request (Request, optional): The HTTP request object.

    Returns:
        UserPublic: The requested user's details.

    Raises:
        HTTPException: If the user is not found.
    """
    user = get_user_by_id_controller(session, user_id, current_user, request)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/", response_model=UserPublic, status_code=201, operation_id="admin_create_user")
def create_user(session: SessionDep, user_in: UserCreate, request: Request) -> UserPublic:
    """
    Create a new user (Admin only).

    Args:
        session (SessionDep): The database session.
        user_in (UserCreate): The new user data.
        request (Request): The HTTP request object.

    Returns:
        UserPublic: The created user's details.

    Raises:
        HTTPException: If user creation fails.
    """
    user = register_controller(session, user_in, request)
    if not user:
        raise HTTPException(status_code=400, detail="User creation failed")
    return user


@router.patch("/{user_id}", response_model=UserPublic, status_code=200, operation_id="admin_update_user")
def update_user(
        session: SessionDep,
        user_id: UUID,
        user_in: UserUpdate,
        current_user: CurrentUser,
        request: Request = None,
) -> UserPublic:
    """
    Update a user's details (Admin only).

    Args:
        session (SessionDep): The database session.
        user_id (UUID): The unique ID of the user.
        user_in (UserUpdate): The updated user data.
        current_user (CurrentUser): The authenticated admin user.
        request (Request, optional): The HTTP request object.

    Returns:
        UserPublic: The updated user details.

    Raises:
        HTTPException: If user update fails.
    """
    user = update_user_controller(session, user_in, current_user, request)
    if not user:
        raise HTTPException(status_code=400, detail="User update failed")
    return user


@router.delete("/{user_id}", response_model=Message, status_code=200, operation_id="admin_delete_user")
def delete_user(
        session: SessionDep,
        user_id: UUID,
        current_user: CurrentUser,
        request: Request = None,
) -> Message:
    """
    Delete a user by ID (Admin only).

    Args:
        session (SessionDep): The database session.
        user_id (UUID): The unique ID of the user to delete.
        current_user (CurrentUser): The authenticated admin user.
        request (Request, optional): The HTTP request object.

    Returns:
        Message: A confirmation message upon successful deletion.

    Raises:
        HTTPException: If user deletion fails.
    """
    success = delete_user_controller(session, current_user, request)
    if not success:
        raise HTTPException(status_code=400, detail="User deletion failed")
    return Message(message="User deleted successfully")

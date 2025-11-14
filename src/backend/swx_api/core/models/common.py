"""
Common Schemas
--------------
This module contains common response schemas used across the API.
"""
from typing import Generic, TypeVar, List
from pydantic import BaseModel
from sqlmodel import SQLModel


class Message(SQLModel):
    """
    Generic message response schema.

    Attributes:
        message (str): The message to return in the response.
    """

    message: str


T = TypeVar("T")

class PaginatedResponse(BaseModel, Generic[T]):
    total: int
    items: List[T]
    skip: int
    limit: int

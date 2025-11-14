"""
Base Model
----------
This module defines the global base model for all SQLModel database models.

Features:
- Ensures models are registered without being a table.
"""

from sqlmodel import SQLModel


class Base(SQLModel):
    """
    Global base model for all database models.

    This ensures that models inheriting from it are recognized by SQLModel
    but do not create a separate table.
    """

    __abstract__ = True
    model_config = {
        "arbitrary_types_allowed": True
    }

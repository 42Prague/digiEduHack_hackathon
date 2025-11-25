"""
Utility helpers shared across ingestion modules.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Optional, Tuple

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .models_db import Teacher
from .schemas import ApiError

WHITESPACE_RE = re.compile(r"\s+")


def normalize_name(value: Optional[str]) -> Optional[str]:
    """
    Normalize a person's name for easier matching.
    """
    if not value:
        return None

    text = value.strip().lower()
    text = WHITESPACE_RE.sub(" ", text)
    text = (
        unicodedata.normalize("NFKD", text)
        .encode("ascii", "ignore")
        .decode("ascii")
    )
    return text or None


def clean_email(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    return value.strip().lower() or None


def build_error(
    code: str, message: str, row_index: Optional[int] = None, column: Optional[str] = None
) -> ApiError:
    return ApiError(code=code, message=message, row_index=row_index, column=column)


def find_or_create_teacher(
    *,
    db: Session,
    normalized_name: Optional[str],
    email: Optional[str],
    original_name: Optional[str],
) -> Tuple[Optional[int], Optional[ApiError]]:
    """
    Tries to resolve a teacher id by email or normalized name.
    Creates a new teacher row when enough information is available.
    """

    teacher = None
    if email:
        teacher = (
            db.query(Teacher)
            .filter(func.lower(Teacher.email) == email.lower())
            .one_or_none()
        )

    if not teacher and normalized_name:
        teacher = (
            db.query(Teacher)
            .filter(Teacher.normalized_name == normalized_name)
            .one_or_none()
        )

    if teacher:
        return teacher.id, None

    if not normalized_name and not email:
        return None, build_error(
            code="TEACHER_MATCH_ERROR",
            message="Teacher information missing (no name/email provided).",
        )

    teacher = Teacher(
        full_name=original_name,
        normalized_name=normalized_name,
        email=email,
    )
    db.add(teacher)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        return None, build_error(
            code="TEACHER_CREATE_ERROR",
            message=f"Failed to create teacher: {exc.orig}",
        )

    return teacher.id, None

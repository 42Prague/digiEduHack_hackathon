"""
Survey ingestion pipeline: load Google Form exports, normalize, and store rows.
"""

from __future__ import annotations

import io
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

import pandas as pd
import numpy as np
from sqlalchemy.orm import Session

from .models_db import SurveyResponse
from .schemas import ApiError, SurveyIngestResult
from .utils import build_error, clean_email, find_or_create_teacher, normalize_name

TEACHER_COLUMNS = [
    "teacher",
    "teacher name",
    "teacher_name",
    "name",
    "full name",
    "instructor",
    "ucitel",
    "imya",
]

EMAIL_COLUMNS = [
    "email",
    "teacher email",
    "teacher_email",
    "mail",
]

TIMESTAMP_COLUMNS = [
    "timestamp",
    "submitted at",
    "submission time",
    "cas",
    "data",
]


def _match_column(columns: List[str], candidates: List[str]) -> Optional[str]:
    lowered = {col.lower(): col for col in columns}
    for candidate in candidates:
        key = candidate.lower()
        if key in lowered:
            return lowered[key]
    return None


def _load_dataframe(file_bytes: bytes, filename: str) -> pd.DataFrame:
    suffix = Path(filename).suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(io.BytesIO(file_bytes))
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(io.BytesIO(file_bytes))
    if suffix == ".json":
        payload = json.loads(file_bytes.decode("utf-8"))
        if isinstance(payload, list):
            return pd.DataFrame(payload)
        if isinstance(payload, dict):
            return pd.DataFrame(payload.get("rows") or payload.get("data") or [])
        raise ValueError("JSON payload must be a list or contain 'rows'/'data'.")
    raise ValueError("Unsupported survey file format. Use CSV, Excel, or JSON.")


def _row_to_dict(row: pd.Series) -> dict:
    result = {}
    for key, value in row.items():
        if pd.isna(value):
            result[key] = None
        elif isinstance(value, pd.Timestamp):
            result[key] = value.isoformat()
        elif isinstance(value, datetime):
            result[key] = value.isoformat()
        elif isinstance(value, np.generic):
            result[key] = value.item()
        else:
            result[key] = value
    return result


def process_survey_file(
    *,
    file_bytes: bytes,
    filename: str,
    workshop_id: Optional[int],
    db: Session,
) -> SurveyIngestResult:
    errors: List[ApiError] = []
    inserted = 0
    skipped = 0

    try:
        df = _load_dataframe(file_bytes, filename)
    except Exception as exc:
        return SurveyIngestResult(
            success=False,
            inserted_rows=0,
            skipped_rows=0,
            errors=[
                build_error(
                    code="SURVEY_LOAD_ERROR",
                    message=str(exc),
                )
            ],
        )

    if df.empty:
        return SurveyIngestResult(
            success=False,
            inserted_rows=0,
            skipped_rows=0,
            errors=[
                build_error(
                    code="SURVEY_EMPTY",
                    message="Survey file had no rows.",
                )
            ],
        )

    columns = list(df.columns)
    teacher_col = _match_column(columns, TEACHER_COLUMNS)
    email_col = _match_column(columns, EMAIL_COLUMNS)
    timestamp_col = _match_column(columns, TIMESTAMP_COLUMNS)

    for idx, row in df.iterrows():
        row_errors: List[ApiError] = []
        teacher_name = None
        teacher_email = None

        if teacher_col:
            value = row.get(teacher_col)
            teacher_name = None if pd.isna(value) else str(value).strip()

        if email_col:
            value = row.get(email_col)
            teacher_email = clean_email(None if pd.isna(value) else str(value))

        normalized_teacher = normalize_name(teacher_name)

        teacher_id = None
        if normalized_teacher or teacher_email:
            teacher_id, teacher_error = find_or_create_teacher(
                db=db,
                normalized_name=normalized_teacher,
                email=teacher_email,
                original_name=teacher_name,
            )
            if teacher_error:
                row_errors.append(teacher_error.copy(update={"row_index": idx}))
        else:
            row_errors.append(
                build_error(
                    code="TEACHER_INFO_MISSING",
                    message="Teacher name/email missing for survey row.",
                    row_index=idx,
                )
            )
            skipped += 1
            errors.extend(row_errors)
            continue

        submitted_at = None
        submitted_iso = None
        if timestamp_col:
            value = row.get(timestamp_col)
            if pd.notna(value):
                parsed = pd.to_datetime(value, dayfirst=True, errors="coerce")
                if pd.isna(parsed):
                    row_errors.append(
                        build_error(
                            code="DATE_PARSE_ERROR",
                            message="Unable to parse submission timestamp.",
                            row_index=idx,
                            column=timestamp_col,
                        )
                    )
                else:
                    submitted_at = parsed.to_pydatetime()
                    if submitted_at.tzinfo is None:
                        submitted_at = submitted_at.replace(tzinfo=timezone.utc)
                    else:
                        submitted_at = submitted_at.astimezone(timezone.utc)
                    submitted_iso = submitted_at.isoformat()

        row_raw = _row_to_dict(row)
        normalized_payload = {
            "teacher_name": teacher_name,
            "teacher_email": teacher_email,
            "normalized_teacher_name": normalized_teacher,
            "submitted_at": submitted_iso,
            "workshop_id": workshop_id,
        }

        response = SurveyResponse(
            teacher_id=teacher_id,
            workshop_id=workshop_id,
            submitted_at=submitted_at,
            raw_data=row_raw,
            normalized_data=normalized_payload,
        )

        try:
            db.add(response)
            db.commit()
            inserted += 1
        except Exception as exc:
            db.rollback()
            row_errors.append(
                build_error(
                    code="SURVEY_DB_ERROR",
                    message=f"Unable to store survey row: {exc}",
                    row_index=idx,
                )
            )
            skipped += 1

        errors.extend(row_errors)

    success = skipped == 0 and len(errors) == 0
    return SurveyIngestResult(
        success=success,
        inserted_rows=inserted,
        skipped_rows=skipped,
        errors=errors,
    )

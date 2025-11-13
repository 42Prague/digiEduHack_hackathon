"""
Generic raw file ingestion helpers.
"""

from __future__ import annotations

import io
import json
import mimetypes
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from uuid import uuid4

import pandas as pd
import pdfplumber
from sqlalchemy.orm import Session

from .models_db import RawDocument
from .schemas import ApiError, RawIngestResult
from .utils import build_error

TEXT_EXTENSIONS = {".txt", ".md", ".rtf"}
TABLE_EXTENSIONS = {".csv", ".tsv", ".xlsx", ".xls", ".json"}


def _safe_table_records(df: pd.DataFrame) -> list:
    return df.where(pd.notnull(df), None).to_dict(orient="records")


def ingest_raw_file(
    *,
    file_bytes: bytes,
    filename: str,
    doc_type: Optional[str],
    teacher_id: Optional[int],
    workshop_id: Optional[int],
    db: Session,
    base_dir: Path,
) -> RawIngestResult:
    raw_id = uuid4()
    suffix = Path(filename or "raw").suffix.lower()
    dest_dir = base_dir / "raw"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / f"{raw_id}{suffix or '.bin'}"

    errors: list[ApiError] = []

    try:
        dest_path.write_bytes(file_bytes)
    except Exception as exc:
        errors.append(
            build_error(
                code="RAW_SAVE_ERROR",
                message=f"Failed to persist uploaded file: {exc}",
            )
        )
        return RawIngestResult(
            success=False,
            raw_id=str(raw_id),
            has_text=False,
            has_table_data=False,
            errors=errors,
        )

    text_content: Optional[str] = None
    table_data: Optional[list] = None

    try:
        if suffix in TEXT_EXTENSIONS:
            text_content = file_bytes.decode("utf-8", errors="ignore")
        elif suffix == ".pdf":
            with pdfplumber.open(str(dest_path)) as pdf:
                parts = []
                for page in pdf.pages:
                    content = page.extract_text() or ""
                    if content:
                        parts.append(content.strip())
                if parts:
                    text_content = "\n\n".join(parts)
        elif suffix in {".csv", ".tsv"}:
            sep = "," if suffix == ".csv" else "\t"
            df = pd.read_csv(io.BytesIO(file_bytes), sep=sep)
            table_data = _safe_table_records(df)
        elif suffix in {".xlsx", ".xls"}:
            df = pd.read_excel(io.BytesIO(file_bytes))
            table_data = _safe_table_records(df)
        elif suffix == ".json":
            payload = json.loads(file_bytes.decode("utf-8"))
            if isinstance(payload, list):
                table_data = payload
            elif isinstance(payload, dict):
                table_data = payload.get("rows") or payload.get("data") or [payload]
            else:
                table_data = [payload]
        else:
            try:
                text_content = file_bytes.decode("utf-8")
            except UnicodeDecodeError:
                text_content = None
    except Exception as exc:
        errors.append(
            build_error(
                code="RAW_PARSE_ERROR",
                message=f"Failed to extract content: {exc}",
            )
        )

    mime_type, _ = mimetypes.guess_type(filename)

    document = RawDocument(
        id=raw_id,
        doc_type=doc_type or (suffix.lstrip(".") if suffix else "unknown"),
        teacher_id=teacher_id,
        workshop_id=workshop_id,
        uploaded_at=datetime.now(timezone.utc),
        original_filename=filename,
        mime_type=mime_type,
        file_path=str(dest_path),
        text_content=text_content,
        table_data=table_data,
    )

    try:
        db.add(document)
        db.commit()
    except Exception as exc:
        db.rollback()
        errors.append(
            build_error(
                code="RAW_DB_ERROR",
                message=f"Failed to write record: {exc}",
            )
        )
        return RawIngestResult(
            success=False,
            raw_id=str(raw_id),
            has_text=bool(text_content),
            has_table_data=table_data is not None,
            errors=errors,
        )

    return RawIngestResult(
        success=len(errors) == 0,
        raw_id=str(raw_id),
        has_text=bool(text_content),
        has_table_data=table_data is not None,
        errors=errors,
    )

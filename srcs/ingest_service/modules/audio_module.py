"""
Audio ingestion logic that stores files and runs local Whisper transcription.
"""

from __future__ import annotations

import asyncio
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from uuid import uuid4

from fastapi import UploadFile
from faster_whisper import WhisperModel
from sqlalchemy.orm import Session

from .models_db import AudioRecording
from .schemas import ApiError, AudioResult
from .utils import build_error

_model_lock = asyncio.Lock()
_whisper_model: Optional[WhisperModel] = None


async def _get_model() -> WhisperModel:
    global _whisper_model
    if _whisper_model is None:
        async with _model_lock:
            if _whisper_model is None:
                model_name = os.getenv("WHISPER_MODEL_SIZE", "tiny")
                device = os.getenv("WHISPER_DEVICE", "cpu")
                compute_type = os.getenv("WHISPER_COMPUTE_TYPE", "int8")
                _whisper_model = WhisperModel(
                    model_name,
                    device=device,
                    compute_type=compute_type,
                )
    return _whisper_model


async def handle_audio_upload(
    *,
    upload_file: UploadFile,
    db: Session,
    base_dir: Path,
    teacher_id: Optional[int] = None,
    workshop_id: Optional[int] = None,
) -> AudioResult:
    audio_id = uuid4()
    suffix = Path(upload_file.filename or "audio").suffix or ".wav"
    dest_dir = base_dir / "audio"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / f"{audio_id}{suffix}"

    errors: list[ApiError] = []

    try:
        file_bytes = await upload_file.read()
        dest_path.write_bytes(file_bytes)
    except Exception as exc:
        errors.append(
            build_error(code="AUDIO_SAVE_ERROR", message=f"Failed to save audio: {exc}")
        )
        return AudioResult(
            success=False, audio_id=str(audio_id), transcript_length=0, errors=errors
        )

    transcript_text = ""
    duration_sec: Optional[int] = None

    try:
        model = await _get_model()
        segments, info = model.transcribe(
            str(dest_path),
            language=os.getenv("WHISPER_LANG", "cs"),
            beam_size=5,
        )
        transcript_chunks = []
        for segment in segments:
            transcript_chunks.append(segment.text.strip())
        transcript_text = " ".join(chunk for chunk in transcript_chunks if chunk)
        if info and info.duration:
            duration_sec = int(info.duration)
    except Exception as exc:
        errors.append(
            build_error(
                code="AUDIO_TRANSCRIBE_ERROR",
                message=str(exc),
            )
        )
        transcript_text = ""

    try:
        recording = AudioRecording(
            id=audio_id,
            teacher_id=teacher_id,
            workshop_id=workshop_id,
            created_at=datetime.now(timezone.utc),
            audio_path=str(dest_path),
            transcript_text=transcript_text,
            duration_sec=duration_sec,
        )
        db.add(recording)
        db.commit()
    except Exception as exc:
        db.rollback()
        errors.append(
            build_error(code="AUDIO_DB_ERROR", message=f"Failed to store audio: {exc}")
        )
        return AudioResult(
            success=False,
            audio_id=str(audio_id),
            transcript_length=len(transcript_text),
            errors=errors,
        )

    success = len(errors) == 0
    return AudioResult(
        success=success,
        audio_id=str(audio_id),
        transcript_length=len(transcript_text),
        errors=errors,
    )

import os
import time
from datetime import datetime

import requests
from sqlmodel import Session, select

from .db import engine, init_db
from .models import FileMeta
from .analysis import analyze_file

POLL_INTERVAL = 5  # seconds

# URL of the Whisper service (internal Docker hostname)
WHISPER_URL = os.getenv("WHISPER_URL", "http://whisper:8000/transcribe")
# Root where tusd stores uploaded files inside the container
# (we'll send paths relative to /data, e.g. "uploads/<filename>")
UPLOAD_ROOT = os.getenv("UPLOAD_ROOT", "/data/uploads")


def is_audio_file(file_meta: FileMeta) -> bool:
    """
    Heuristics to decide whether this FileMeta represents an audio file
    we should send to Whisper.
    """
    mime = getattr(file_meta, "mime_type", None) or getattr(file_meta, "content_type", None)
    if mime and mime.startswith("audio/"):
        return True

    name = (
        getattr(file_meta, "stored_filename", None)
        or getattr(file_meta, "filename", None)
        or getattr(file_meta, "original_filename", None)
        or ""
    ).lower()

    return name.endswith(".wav") or name.endswith(".mp3") or name.endswith(".m4a") or name.endswith(".flac")


def build_audio_rel_path(file_meta: FileMeta) -> str:
    """
    Build the path that Whisper API should see (relative to /data).
    Adjust this to match how you actually store files from tusd.
    """
    # If you already store a relative path, prefer that
    stored_path = getattr(file_meta, "stored_path", None)
    if stored_path:
        return stored_path

    # Common pattern: uploads are stored as /data/uploads/<tus_id> or /data/uploads/<filename>
    tus_id = getattr(file_meta, "tus_id", None)
    if tus_id:
        return f"uploads/{tus_id}"

    name = (
        getattr(file_meta, "stored_filename", None)
        or getattr(file_meta, "filename", None)
        or getattr(file_meta, "original_filename", None)
    )
    if name:
        return f"uploads/{name}"

    # Fallback – you can customize/replace this as needed
    raise RuntimeError(f"Cannot determine audio path for FileMeta id={file_meta.id}")


def transcribe_with_whisper(file_meta: FileMeta) -> str:
    """
    Call the Whisper HTTP API and return the transcript text.
    """
    rel_path = build_audio_rel_path(file_meta)

    payload = {
        "path": rel_path,   # relative to /data inside whisper container
        "language": "cs",   # Czech; can be made dynamic if needed
    }

    response = requests.post(WHISPER_URL, json=payload, timeout=600)
    response.raise_for_status()
    data = response.json()

    text = data.get("text", "").strip()
    if not text:
        raise RuntimeError(f"Whisper returned empty transcript for path={rel_path}")

    return text

def main():
    init_db()

    while True:
        with Session(engine) as session:
            pending_files = session.exec(
                select(FileMeta).where(FileMeta.analysis_status == "pending")
            ).all()

            if not pending_files:
                time.sleep(POLL_INTERVAL)
                continue

            for f in pending_files:
                f.analysis_status = "processing"
                f.analysis_started_at = datetime.utcnow()
                session.add(f)
                session.commit()

                try:
                    # 1) For audio files: get transcript from Whisper
                    override_text = None
                    if is_audio_file(f):
                        transcript = transcribe_with_whisper(f)

                        # Optional: persist transcript on the FileMeta if you add such a field
                        if hasattr(f, "transcript_text"):
                            f.transcript_text = transcript
                            session.add(f)
                            session.commit()

                        override_text = transcript

                    # 2) Run your existing metadata / analysis pipeline
                    analyze_file(session, f, override_text=override_text)

                    f.analysis_status = "done"
                    f.analysis_finished_at = datetime.utcnow()
                    f.analysis_error = None
                except Exception as e:
                    f.analysis_status = "failed"
                    f.analysis_finished_at = datetime.utcnow()
                    f.analysis_error = str(e)[:512]

                session.add(f)
                session.commit()

if __name__ == "__main__":
    main()

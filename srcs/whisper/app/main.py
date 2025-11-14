import os
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from faster_whisper import WhisperModel

# ----- Model loading (one global instance) -----
model_name = os.getenv("WHISPER_MODEL", "small")
device = os.getenv("WHISPER_DEVICE", "cpu")  # "cpu" or "cuda"
compute_type = os.getenv("WHISPER_COMPUTE_TYPE", "int8")  # int8 / float16 / float32 etc.

model = WhisperModel(model_name, device=device, compute_type=compute_type)

# ----- API schema -----
class TranscriptionRequest(BaseModel):
    # Path to audio file relative to /data (e.g. "uploads/xyz.wav")
    path: str
    language: Optional[str] = "cs"  # default Czech


class TranscriptionResponse(BaseModel):
    text: str


app = FastAPI(title="Whisper STT", version="0.1.0")


@app.get("/health")
def health():
    return {"status": "ok", "model": model_name, "device": device}


@app.post("/transcribe", response_model=TranscriptionResponse)
def transcribe(req: TranscriptionRequest):
    # If not absolute, treat as relative to /data shared volume
    audio_path = req.path
    if not audio_path.startswith("/"):
        audio_path = os.path.join("/data", audio_path)

    if not os.path.exists(audio_path):
        raise HTTPException(status_code=404, detail=f"File not found: {audio_path}")

    try:
        segments, info = model.transcribe(
            audio_path,
            language=req.language,
            beam_size=5,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    text = "".join(segment.text for segment in segments)
    return TranscriptionResponse(text=text)

"""FastAPI app for Whisper transcription with ROCm/GPU support."""

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from typing import Optional
import io
import os
from services.whisper_rocm import WhisperService

app = FastAPI(title="Whisper API (ROCm/GPU)")

# Initialize service
whisper_service = WhisperService()

@app.get("/")
async def root():
    return {"message": "Whisper API with ROCm/GPU", "model": os.getenv('WHISPER_MODEL_SIZE', 'large-v3')}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/transcribe")
async def transcribe(
    file: UploadFile = File(...),
    language: Optional[str] = Form(None),
    task: Optional[str] = Form('transcribe')
):
    # Read audio file
    contents = await file.read()
    audio_buffer = io.BytesIO(contents)
    
    # Transcribe
    result = await whisper_service.transcribe(audio_buffer, language)
    
    return result

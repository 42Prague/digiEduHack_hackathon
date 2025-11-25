"""Whisper-only service using faster-whisper."""

import os
import io
import tempfile
from typing import Optional
from faster_whisper import WhisperModel

class WhisperService:
    def __init__(self):
        model_size = os.getenv('WHISPER_MODEL_SIZE', 'large-v3')
        self.model = WhisperModel(model_size, device='cpu', compute_type='int8')
        print(f'Whisper model {model_size} loaded on CPU')
    
    async def transcribe(self, audio_file: io.BytesIO, language: Optional[str] = None):
        # Save audio to temp file
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
            tmp_file.write(audio_file.read())
            tmp_path = tmp_file.name
        
        try:
            segments, info = self.model.transcribe(
                tmp_path,
                language=language,
                beam_size=5,
                vad_filter=True
            )
            
            # Combine segments
            full_text = ' '.join([segment.text for segment in segments])
            
            return {
                'text': full_text,
                'detected_language': info.language,
                'confidence': info.language_probability
            }
        finally:
            os.unlink(tmp_path)

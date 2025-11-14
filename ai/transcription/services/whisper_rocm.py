"""Whisper service with ROCm/GPU support using OpenAI Whisper with PyTorch."""

import os
import io
import tempfile
from typing import Optional
import whisper
import torch

class WhisperService:
    def __init__(self):
        model_size = os.getenv('WHISPER_MODEL_SIZE', 'large-v3')
        
        # Detect device
        if torch.cuda.is_available():
            self.device = 'cuda'
            print(f'ROCm/GPU detected: {torch.cuda.get_device_name(0)}')
            print(f'GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB')
        else:
            self.device = 'cpu'
            print('Warning: GPU not detected, falling back to CPU')
        
        print(f'Loading Whisper model {model_size} on {self.device.upper()}...')
        self.model = whisper.load_model(model_size, device=self.device)
        print(f'Whisper model {model_size} loaded successfully on {self.device.upper()}')
    
    async def transcribe(self, audio_file: io.BytesIO, language: Optional[str] = None):
        # Save audio to temp file
        with tempfile.NamedTemporaryFile(suffix='.m4a', delete=False) as tmp_file:
            tmp_file.write(audio_file.read())
            tmp_path = tmp_file.name
        
        try:
            # Transcribe using OpenAI Whisper
            result = self.model.transcribe(
                tmp_path,
                language=language,
                verbose=False
            )
            
            return {
                'text': result['text'],
                'detected_language': result.get('language', language),
                'confidence': 1.0  # OpenAI Whisper doesn't provide confidence scores
            }
        finally:
            os.unlink(tmp_path)

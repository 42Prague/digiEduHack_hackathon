"""Base service interfaces for all models."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import io


@dataclass
class TranscriptionResult:
    """Result from audio transcription."""
    text: str
    detected_language: Optional[str] = None
    confidence: Optional[float] = None


@dataclass
class OCRResult:
    """Result from OCR processing."""
    text: str
    detected_language: Optional[str] = None
    bounding_boxes: Optional[List[Dict]] = None


@dataclass
class GenerationResult:
    """Result from text generation."""
    text: str
    tokens_used: Optional[int] = None


@dataclass
class TranslationResult:
    """Result from translation."""
    text: str
    source_language: str
    target_language: str


class BaseTranscriptionService(ABC):
    """Base interface for audio transcription services."""

    @abstractmethod
    async def transcribe(self, audio_file: io.BytesIO, language: Optional[str] = None) -> TranscriptionResult:
        """Transcribe audio file to text."""
        pass


class BaseOCRService(ABC):
    """Base interface for OCR services."""

    @abstractmethod
    async def extract_text(self, image_file: io.BytesIO, language: Optional[str] = None) -> OCRResult:
        """Extract text from image or PDF."""
        pass


class BaseGenerationService(ABC):
    """Base interface for text generation services."""

    @abstractmethod
    async def generate(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.7) -> GenerationResult:
        """Generate text based on prompt."""
        pass


class BaseTranslationService(ABC):
    """Base interface for translation services."""

    @abstractmethod
    async def translate(self, text: str, source_lang: str, target_lang: str) -> TranslationResult:
        """Translate text between languages."""
        pass

    @abstractmethod
    async def detect_language(self, text: str) -> str:
        """Detect the language of the text."""
        pass
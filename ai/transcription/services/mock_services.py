"""Mock service implementations using OpenRouter and external APIs."""

import os
import io
import base64
import httpx
from typing import Optional, List
from services.base import (
    BaseTranscriptionService, BaseOCRService, BaseGenerationService, BaseTranslationService,
    TranscriptionResult, OCRResult, GenerationResult, TranslationResult
)

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False


class MockTranscriptionService(BaseTranscriptionService):
    """Mock transcription using Runpod Whisper API."""

    def __init__(self):
        # Get Runpod configuration from environment variables
        self.api_key = os.getenv("RUNPOD_API_KEY", "")
        self.endpoint_id = os.getenv("RUNPOD_WHISPER_ENDPOINT_ID", "")

        if not self.api_key or not self.endpoint_id:
            print("Warning: RUNPOD_API_KEY or RUNPOD_WHISPER_ENDPOINT_ID not set")

        self.api_url = f"https://api.runpod.ai/v2/{self.endpoint_id}/runsync"

    async def transcribe(self, audio_file: io.BytesIO, language: Optional[str] = None) -> TranscriptionResult:
        """Transcribe audio using Runpod's Whisper API."""

        # Check if API credentials are available
        if not self.api_key or not self.endpoint_id:
            # Return a mock response if Runpod is not configured
            mock_text = "Runpod Whisper API not configured. This is a fallback mock response."
            if language == "cs":
                mock_text = "Runpod Whisper API není nakonfigurováno. Toto je záložní simulovaná odpověď."
            return TranscriptionResult(
                text=mock_text,
                detected_language=language or "en",
                confidence=0.0
            )

        try:
            # Read and encode audio file to base64
            audio_data = audio_file.read()
            audio_file.seek(0)  # Reset for potential re-reading
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')

            # Prepare the request
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            # Prepare input data for Runpod
            data = {
                "input": {
                    "audio_base64": audio_base64,
                    "model": "turbo",  # Using turbo model for speed
                    "language": language,  # Czech if specified
                    "task": "transcribe"
                }
            }

            # Make the API call
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_url,
                    headers=headers,
                    json=data,
                    timeout=120.0  # 2 minutes timeout for transcription
                )

                if response.status_code == 200:
                    result = response.json()

                    # Log the response for debugging
                    import json
                    print(f"Runpod response: {json.dumps(result, indent=2)[:500]}")

                    # Extract transcription from Runpod response
                    # Runpod returns the result in result['output']
                    if 'output' in result:
                        output = result['output']
                        # The output contains the transcription directly
                        if isinstance(output, dict):
                            transcription = output.get('transcription', '') or output.get('text', '')
                            detected_lang = output.get('detected_language', language or 'cs')
                        elif isinstance(output, str):
                            # Sometimes it's just a string
                            transcription = output
                            detected_lang = language or 'cs'
                        else:
                            transcription = str(output) if output else ""
                            detected_lang = language or 'cs'
                    else:
                        # Fallback to checking at the top level
                        transcription = result.get('transcription', '') or result.get('text', '')
                        detected_lang = result.get('detected_language', language or 'cs')

                    if not transcription:
                        # Log the full result for debugging
                        print(f"No transcription found in result: {result}")

                    return TranscriptionResult(
                        text=transcription if transcription else "Transcription failed - no text returned",
                        detected_language=detected_lang,
                        confidence=0.95 if transcription else 0.0
                    )
                else:
                    # Return error information
                    error_msg = f"Runpod API error: {response.status_code}"
                    try:
                        error_detail = response.json()
                        error_msg += f" - {error_detail}"
                    except:
                        error_msg += f" - {response.text}"

                    return TranscriptionResult(
                        text=error_msg,
                        detected_language=language or "unknown",
                        confidence=0.0
                    )

        except Exception as e:
            # If Runpod fails, return error message
            return TranscriptionResult(
                text=f"Transcription error: {str(e)}",
                detected_language=language or "unknown",
                confidence=0.0
            )


class MockOCRService(BaseOCRService):
    """Mock OCR using OpenRouter's Qwen3-VL."""

    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY", "")
        self.base_url = "https://openrouter.ai/api/v1"

    def _is_pdf(self, file_data: bytes) -> bool:
        """Check if the file is a PDF based on magic bytes."""
        return file_data[:4] == b'%PDF'

    def _convert_pdf_to_images(self, pdf_data: bytes) -> List[bytes]:
        """Convert PDF pages to PNG images using PyMuPDF."""
        if not PYMUPDF_AVAILABLE:
            raise ImportError("PyMuPDF is required for PDF processing. Install with: pip install PyMuPDF")

        images = []
        pdf_document = fitz.open(stream=pdf_data, filetype="pdf")

        try:
            for page_num in range(len(pdf_document)):
                page = pdf_document[page_num]
                # Render page to image (default 96 DPI, increase for better quality)
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x scale for better OCR
                img_data = pix.pil_tobytes(format="PNG")
                images.append(img_data)
        finally:
            pdf_document.close()

        return images

    async def _process_single_image(self, image_data: bytes, prompt: str, page_num: Optional[int] = None) -> str:
        """Process a single image through Qwen3-VL."""
        async with httpx.AsyncClient() as client:
            base64_image = base64.b64encode(image_data).decode('utf-8')

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:8000",
                "X-Title": "Multi-Model API"
            }

            page_prompt = prompt
            if page_num is not None:
                page_prompt = f"Page {page_num + 1}: {prompt}"

            data = {
                "model": "qwen/qwen3-vl-30b-a3b-instruct",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": page_prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
                        ]
                    }
                ]
            }

            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=30.0
                )

                if response.status_code == 200:
                    result = response.json()
                    return result['choices'][0]['message']['content']
                else:
                    return f"Error processing {'page ' + str(page_num + 1) if page_num is not None else 'image'}: API returned {response.status_code}"
            except Exception as e:
                return f"Error processing {'page ' + str(page_num + 1) if page_num is not None else 'image'}: {str(e)}"

    async def extract_text(self, file: io.BytesIO, language: Optional[str] = None) -> OCRResult:
        """Extract text from image or PDF using Qwen3-VL through OpenRouter."""

        # Read file data
        file_data = file.read()
        file.seek(0)  # Reset for potential re-reading

        # Prepare prompt based on language
        prompt = "Extract all text from this image. If there's text in Czech, include it as is. Preserve the original formatting and structure."
        if language == "cs":
            prompt = "Extrahujte veškerý text z tohoto obrázku. Zachovejte původní formátování a strukturu."

        # Check if it's a PDF
        if self._is_pdf(file_data):
            try:
                # Convert PDF to images
                images = self._convert_pdf_to_images(file_data)

                # Process each page
                all_text = []
                for i, img_data in enumerate(images):
                    page_text = await self._process_single_image(img_data, prompt, page_num=i)
                    all_text.append(f"=== Page {i + 1} ===\n{page_text}")

                # Combine results from all pages
                combined_text = "\n\n".join(all_text)

                return OCRResult(
                    text=combined_text,
                    detected_language=language or "en",
                    bounding_boxes=None  # Could add page metadata here
                )
            except Exception as e:
                return OCRResult(
                    text=f"Error processing PDF: {str(e)}",
                    detected_language=language or "en"
                )
        else:
            # Process as single image
            try:
                extracted_text = await self._process_single_image(file_data, prompt)
                return OCRResult(
                    text=extracted_text,
                    detected_language=language or "en"
                )
            except Exception as e:
                return OCRResult(
                    text=f"Error processing image: {str(e)}",
                    detected_language=language or "en"
                )


class MockGenerationService(BaseGenerationService):
    """Mock text generation using OpenRouter's Llama 3.3 70B."""

    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY", "")
        self.base_url = "https://openrouter.ai/api/v1"

    async def generate(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.7) -> GenerationResult:
        """Generate text using Llama 3.3 70B through OpenRouter."""

        async with httpx.AsyncClient() as client:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:8000",
                "X-Title": "Multi-Model API"
            }

            data = {
                "model": "meta-llama/llama-3.3-70b-instruct",
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": max_tokens,
                "temperature": temperature
            }

            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=30.0
                )

                if response.status_code == 200:
                    result = response.json()
                    generated_text = result['choices'][0]['message']['content']
                    tokens = result.get('usage', {}).get('total_tokens', 0)

                    return GenerationResult(
                        text=generated_text,
                        tokens_used=tokens
                    )
                else:
                    return GenerationResult(
                        text=f"Mock generation: API returned {response.status_code}",
                        tokens_used=0
                    )
            except Exception as e:
                return GenerationResult(
                    text=f"Mock generation: Error - {str(e)}",
                    tokens_used=0
                )


class MockTranslationService(BaseTranslationService):
    """Mock translation using OpenRouter (Claude/GPT for Czech-English)."""

    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY", "")
        self.base_url = "https://openrouter.ai/api/v1"
        # Using Claude for better Czech translation
        self.model = "anthropic/claude-3.5-sonnet"

    async def detect_language(self, text: str) -> str:
        """Detect language of the text."""
        # Simple detection based on common Czech characters
        czech_chars = ['ě', 'š', 'č', 'ř', 'ž', 'ý', 'á', 'í', 'é']
        text_lower = text.lower()

        czech_count = sum(1 for char in czech_chars if char in text_lower)

        if czech_count >= 2 or any(word in text_lower for word in ['je', 'a', 'že', 'se', 'na']):
            return "cs"
        return "en"

    async def translate(self, text: str, source_lang: str, target_lang: str) -> TranslationResult:
        """Translate text using Claude through OpenRouter."""

        async with httpx.AsyncClient() as client:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:8000",
                "X-Title": "Multi-Model API"
            }

            lang_names = {
                "cs": "Czech",
                "en": "English"
            }

            prompt = f"""Translate the following text from {lang_names.get(source_lang, source_lang)} to {lang_names.get(target_lang, target_lang)}.
Only provide the translation, no explanations or additional text.

Text to translate:
{text}"""

            data = {
                "model": self.model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3  # Lower temperature for more accurate translation
            }

            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=30.0
                )

                if response.status_code == 200:
                    result = response.json()
                    translated_text = result['choices'][0]['message']['content']

                    return TranslationResult(
                        text=translated_text.strip(),
                        source_language=source_lang,
                        target_language=target_lang
                    )
                else:
                    return TranslationResult(
                        text=f"Translation error: API returned {response.status_code}",
                        source_language=source_lang,
                        target_language=target_lang
                    )
            except Exception as e:
                return TranslationResult(
                    text=f"Translation error: {str(e)}",
                    source_language=source_lang,
                    target_language=target_lang
                )
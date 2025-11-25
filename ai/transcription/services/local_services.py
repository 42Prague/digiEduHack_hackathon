"""Local service implementations for ROCm/GPU deployment."""

import os
import io
import torch
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


class LocalTranscriptionService(BaseTranscriptionService):
    """Local Whisper implementation using faster-whisper with ROCm support."""

    def __init__(self):
        self.model_path = os.getenv("WHISPER_MODEL_PATH", "/models/whisper-large-v3")
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = None

    def load_model(self):
        """Lazy load the model when first needed."""
        if self.model is None:
            try:
                from faster_whisper import WhisperModel
                # Use int8 quantization for better performance on ROCm
                self.model = WhisperModel(
                    self.model_path,
                    device=self.device,
                    compute_type="int8" if self.device == "cuda" else "int16"
                )
            except ImportError:
                raise RuntimeError("faster-whisper not installed. Please install with ROCm support.")

    async def transcribe(self, audio_file: io.BytesIO, language: Optional[str] = None) -> TranscriptionResult:
        """Transcribe audio using local Whisper model."""
        self.load_model()

        # Save audio temporarily (faster-whisper needs file path)
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            tmp_file.write(audio_file.read())
            tmp_path = tmp_file.name

        try:
            segments, info = self.model.transcribe(
                tmp_path,
                language=language,
                beam_size=5,
                vad_filter=True
            )

            # Combine all segments
            full_text = " ".join([segment.text for segment in segments])

            return TranscriptionResult(
                text=full_text,
                detected_language=info.language,
                confidence=info.language_probability
            )
        finally:
            # Clean up temp file
            os.unlink(tmp_path)


class LocalOCRService(BaseOCRService):
    """Local Qwen3-VL implementation with ROCm support."""

    def __init__(self):
        self.model_path = os.getenv("QWEN3_VL_MODEL_PATH", "/models/qwen3-vl-32b")
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = None
        self.processor = None

    def load_model(self):
        """Lazy load the model when first needed."""
        if self.model is None:
            try:
                from transformers import Qwen2VLForConditionalGeneration, AutoProcessor

                # Load with 8-bit quantization for memory efficiency
                self.model = Qwen2VLForConditionalGeneration.from_pretrained(
                    self.model_path,
                    torch_dtype=torch.float16,
                    device_map="auto",
                    load_in_8bit=True
                )
                self.processor = AutoProcessor.from_pretrained(self.model_path)
            except ImportError:
                raise RuntimeError("transformers not installed with Qwen support.")

    def _is_pdf(self, file_data: bytes) -> bool:
        """Check if the file is a PDF based on magic bytes."""
        return file_data[:4] == b'%PDF'

    def _convert_pdf_to_images(self, pdf_data: bytes) -> List:
        """Convert PDF pages to PIL Images using PyMuPDF."""
        if not PYMUPDF_AVAILABLE:
            raise ImportError("PyMuPDF is required for PDF processing. Install with: pip install PyMuPDF")

        from PIL import Image
        images = []
        pdf_document = fitz.open(stream=pdf_data, filetype="pdf")

        try:
            for page_num in range(len(pdf_document)):
                page = pdf_document[page_num]
                # Render page to image (2x scale for better quality)
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                # Convert to PIL Image
                img_data = pix.pil_tobytes(format="PNG")
                img = Image.open(io.BytesIO(img_data))
                images.append(img)
        finally:
            pdf_document.close()

        return images

    async def _process_single_image(self, image, prompt: str) -> str:
        """Process a single image through Qwen3-VL."""
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image", "image": image}
                ]
            }
        ]

        # Process with Qwen3-VL
        text = self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        image_inputs, video_inputs = process_vision_info(messages)

        inputs = self.processor(
            text=[text],
            images=image_inputs,
            videos=video_inputs,
            return_tensors="pt"
        ).to(self.device)

        with torch.no_grad():
            generated_ids = self.model.generate(
                **inputs,
                max_new_tokens=512,
                temperature=0.1
            )

        generated_text = self.processor.batch_decode(
            generated_ids,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=False
        )[0]

        return generated_text

    async def extract_text(self, file: io.BytesIO, language: Optional[str] = None) -> OCRResult:
        """Extract text from image or PDF using local Qwen3-VL model."""
        self.load_model()

        # Read file data
        file_data = file.read()
        file.seek(0)

        # Prepare prompt
        prompt = "Extract all text from this image. Preserve the original formatting and structure."
        if language == "cs":
            prompt = "Extrahujte veškerý text z tohoto obrázku. Zachovejte původní formátování a strukturu."

        # Check if it's a PDF
        if self._is_pdf(file_data):
            try:
                # Convert PDF to images
                images = self._convert_pdf_to_images(file_data)

                # Process each page
                all_text = []
                for i, img in enumerate(images):
                    page_prompt = f"Page {i + 1}: {prompt}"
                    page_text = await self._process_single_image(img, page_prompt)
                    all_text.append(f"=== Page {i + 1} ===\n{page_text}")

                # Combine results
                combined_text = "\n\n".join(all_text)

                return OCRResult(
                    text=combined_text,
                    detected_language=language or "en"
                )
            except Exception as e:
                return OCRResult(
                    text=f"Error processing PDF: {str(e)}",
                    detected_language=language or "en"
                )
        else:
            # Process as single image
            try:
                from PIL import Image
                image = Image.open(file)
                extracted_text = await self._process_single_image(image, prompt)

                return OCRResult(
                    text=extracted_text,
                    detected_language=language or "en"
                )
            except Exception as e:
                return OCRResult(
                    text=f"Error processing image: {str(e)}",
                    detected_language=language or "en"
                )


class LocalGenerationService(BaseGenerationService):
    """Local Llama 3.3 70B implementation using vLLM with ROCm support."""

    def __init__(self):
        self.model_path = os.getenv("LLAMA_MODEL_PATH", "/models/llama-3.3-70b-instruct")
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = None

    def load_model(self):
        """Lazy load the model when first needed."""
        if self.model is None:
            try:
                # Try vLLM first (best performance)
                from vllm import LLM, SamplingParams

                # Use tensor parallelism for 70B model
                self.model = LLM(
                    model=self.model_path,
                    tensor_parallel_size=torch.cuda.device_count() if self.device == "cuda" else 1,
                    dtype="float16",
                    max_model_len=8192
                )
                self.use_vllm = True
            except ImportError:
                # Fallback to llama.cpp
                try:
                    from llama_cpp import Llama

                    self.model = Llama(
                        model_path=f"{self.model_path}/llama-3.3-70b.Q4_K_M.gguf",
                        n_gpu_layers=-1,  # Use all GPU layers
                        n_ctx=8192,
                        n_batch=512,
                        verbose=False
                    )
                    self.use_vllm = False
                except ImportError:
                    raise RuntimeError("Neither vLLM nor llama-cpp-python installed.")

    async def generate(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.7) -> GenerationResult:
        """Generate text using local Llama 3.3 70B model."""
        self.load_model()

        if self.use_vllm:
            from vllm import SamplingParams

            sampling_params = SamplingParams(
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=0.95
            )

            outputs = self.model.generate([prompt], sampling_params)
            generated_text = outputs[0].outputs[0].text
            tokens_used = len(outputs[0].outputs[0].token_ids)
        else:
            # Using llama.cpp
            response = self.model(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=0.95,
                echo=False
            )
            generated_text = response['choices'][0]['text']
            tokens_used = response['usage']['total_tokens']

        return GenerationResult(
            text=generated_text,
            tokens_used=tokens_used
        )


class LocalTranslationService(BaseTranslationService):
    """Local NLLB-200 implementation for translation."""

    def __init__(self):
        self.model_path = os.getenv("NLLB_MODEL_PATH", "/models/nllb-200-3.3B")
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = None
        self.tokenizer = None

    def load_model(self):
        """Lazy load the model when first needed."""
        if self.model is None:
            try:
                from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

                self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
                self.model = AutoModelForSeq2SeqLM.from_pretrained(
                    self.model_path,
                    torch_dtype=torch.float16,
                    device_map="auto"
                )
            except ImportError:
                raise RuntimeError("transformers not installed with NLLB support.")

    async def detect_language(self, text: str) -> str:
        """Detect language of the text."""
        # Simple detection - in production use a proper language detection model
        czech_chars = ['ě', 'š', 'č', 'ř', 'ž', 'ý', 'á', 'í', 'é']
        text_lower = text.lower()

        czech_count = sum(1 for char in czech_chars if char in text_lower)

        if czech_count >= 2 or any(word in text_lower for word in ['je', 'a', 'že', 'se', 'na']):
            return "cs"
        return "en"

    async def translate(self, text: str, source_lang: str, target_lang: str) -> TranslationResult:
        """Translate text using local NLLB model."""
        self.load_model()

        # NLLB language codes
        lang_codes = {
            "cs": "ces_Latn",  # Czech
            "en": "eng_Latn"   # English
        }

        src_lang = lang_codes.get(source_lang, source_lang)
        tgt_lang = lang_codes.get(target_lang, target_lang)

        # Set source language
        self.tokenizer.src_lang = src_lang

        # Tokenize
        inputs = self.tokenizer(text, return_tensors="pt").to(self.device)

        # Generate translation
        with torch.no_grad():
            translated_tokens = self.model.generate(
                **inputs,
                forced_bos_token_id=self.tokenizer.lang_code_to_id[tgt_lang],
                max_length=512,
                num_beams=5,
                temperature=0.3
            )

        # Decode
        translated_text = self.tokenizer.batch_decode(
            translated_tokens,
            skip_special_tokens=True
        )[0]

        return TranslationResult(
            text=translated_text,
            source_language=source_lang,
            target_language=target_lang
        )


# Helper function for Qwen3-VL
def process_vision_info(messages):
    """Process vision information from messages for Qwen3-VL."""
    image_inputs = []
    video_inputs = []

    for message in messages:
        if isinstance(message.get("content"), list):
            for item in message["content"]:
                if item.get("type") == "image":
                    image_inputs.append(item.get("image"))
                elif item.get("type") == "video":
                    video_inputs.append(item.get("video"))

    return image_inputs, video_inputs
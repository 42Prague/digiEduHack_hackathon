"""Tesseract OCR service for CPU-based inference."""

import os
import logging
from typing import Optional, Dict, List
from io import BytesIO
from PIL import Image
import fitz  # PyMuPDF
import pytesseract

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TesseractService:
    """Tesseract OCR service using CPU."""

    def __init__(self):
        """Initialize the Tesseract OCR service."""
        # Languages to support
        self.languages = 'ces+eng'  # Czech + English

        logger.info(f"Initializing Tesseract with languages: {self.languages}")

        # Test if Tesseract is available
        try:
            version = pytesseract.get_tesseract_version()
            logger.info(f"Tesseract version: {version}")
        except Exception as e:
            logger.error(f"Tesseract not found: {e}")
            raise

        # Configure Tesseract for better accuracy
        self.config = '--psm 1 --oem 3'  # PSM 1 = Auto page segmentation with OSD, OEM 3 = Default (LSTM)

        logger.info("Tesseract OCR service initialized successfully")

    def _convert_pdf_page_to_image(self, pdf_document: fitz.Document, page_num: int) -> Image.Image:
        """
        Convert a single PDF page to PIL Image.

        Args:
            pdf_document: PyMuPDF document
            page_num: Page number (0-indexed)

        Returns:
            PIL Image
        """
        page = pdf_document[page_num]
        # Render at 2x resolution for better OCR quality
        # Tesseract works well with higher resolution
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))

        # Convert to PIL Image
        img_data = pix.pil_tobytes(format="PNG")
        img = Image.open(BytesIO(img_data))

        return img

    def _process_single_image(self, image: Image.Image) -> str:
        """
        Process a single image with OCR.

        Args:
            image: PIL Image

        Returns:
            Extracted text
        """
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # Perform OCR with Czech + English
        text = pytesseract.image_to_string(
            image,
            lang=self.languages,
            config=self.config
        )

        return text.strip()

    def process_image(self, image_data: bytes) -> Dict:
        """
        Process a single image for OCR.

        Args:
            image_data: Image file as bytes

        Returns:
            Dictionary with extracted text and metadata
        """
        try:
            # Load image
            image = Image.open(BytesIO(image_data))

            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')

            logger.info(f"Processing image: {image.size}")

            # Extract text
            text = self._process_single_image(image)

            return {
                "text": text,
                "type": "image",
                "model": "Tesseract",
                "languages": self.languages.split('+'),
                "engine": "CPU"
            }

        except Exception as e:
            logger.error(f"Image OCR error: {e}")
            raise

    def process_pdf(self, pdf_data: bytes) -> Dict:
        """
        Process a PDF document for OCR.

        Args:
            pdf_data: PDF file as bytes

        Returns:
            Dictionary with extracted text per page and metadata
        """
        try:
            # Process PDF page-by-page
            pdf_document = fitz.open(stream=pdf_data, filetype="pdf")
            page_count = len(pdf_document)

            logger.info(f"Processing PDF with {page_count} pages")

            # Process each page individually
            pages = []
            for page_num in range(page_count):
                logger.info(f"Processing page {page_num + 1}/{page_count}")

                # Convert single page to image
                image = self._convert_pdf_page_to_image(pdf_document, page_num)

                # Process this page
                text = self._process_single_image(image)

                pages.append({
                    "page": page_num + 1,
                    "text": text
                })

                # Clean up image from memory
                del image

            pdf_document.close()

            # Combine all pages
            full_text = "\n\n---PAGE BREAK---\n\n".join([p["text"] for p in pages])

            return {
                "text": full_text,
                "pages": pages,
                "page_count": len(pages),
                "type": "pdf",
                "model": "Tesseract",
                "languages": self.languages.split('+'),
                "engine": "CPU"
            }

        except Exception as e:
            logger.error(f"PDF OCR error: {e}")
            raise


# Async wrapper for FastAPI compatibility
class AsyncTesseractService:
    """Async wrapper for the Tesseract service."""

    def __init__(self):
        self.service = TesseractService()

    async def process_image(self, image_data: bytes) -> Dict:
        """Async image OCR."""
        return self.service.process_image(image_data)

    async def process_pdf(self, pdf_data: bytes) -> Dict:
        """Async PDF OCR."""
        return self.service.process_pdf(pdf_data)

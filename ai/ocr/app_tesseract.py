"""FastAPI application for Tesseract OCR service."""

import os
import logging
from typing import Optional
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import the OCR service
from services.tesseract_service import AsyncTesseractService

# Global service instance
ocr_service: Optional[AsyncTesseractService] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize the OCR service on startup."""
    global ocr_service
    logger.info("Initializing Tesseract OCR service...")
    ocr_service = AsyncTesseractService()
    logger.info("OCR service ready")
    yield


# Create FastAPI app
app = FastAPI(
    title="Tesseract OCR API",
    description="Image and PDF OCR using Tesseract with Czech and English language support",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Tesseract OCR API",
        "model": "Tesseract (CPU)",
        "languages": ["Czech (ces)", "English (eng)"],
        "endpoints": {
            "/ocr": "Extract text from images or PDFs",
            "/health": "Health check endpoint"
        },
        "supported_formats": ["PNG", "JPEG", "JPG", "PDF"],
        "features": [
            "Multi-language OCR (Czech + English)",
            "PDF multi-page processing",
            "CPU-based inference (no GPU required)",
            "Mature, battle-tested OCR engine"
        ]
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Tesseract OCR",
        "model": "Tesseract (CPU)",
        "languages": ["ces", "eng"],
        "ready": ocr_service is not None
    }


@app.post("/ocr")
async def extract_text(
    file: UploadFile = File(...),
    prompt: Optional[str] = Form(None)  # Kept for API compatibility, but not used by Tesseract
):
    """
    Extract text from an image or PDF file.

    Args:
        file: Image (PNG, JPEG) or PDF file
        prompt: Optional (not used by Tesseract, kept for API compatibility)

    Returns:
        Extracted text with metadata
    """
    if not ocr_service:
        raise HTTPException(status_code=503, detail="OCR service not available")

    # Validate file type
    allowed_types = ["image/png", "image/jpeg", "image/jpg", "application/pdf"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}. Allowed: {', '.join(allowed_types)}"
        )

    try:
        # Read file data
        file_data = await file.read()
        logger.info(f"Processing file: {file.filename} ({file.content_type}, {len(file_data)} bytes)")

        # Process based on file type
        if file.content_type == "application/pdf":
            result = await ocr_service.process_pdf(file_data)
        else:
            result = await ocr_service.process_image(file_data)

        # Add filename to result
        result["filename"] = file.filename

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OCR error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

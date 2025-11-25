# Ubuntu-based Dockerfile for Tesseract OCR service (CPU)
FROM docker.io/ubuntu:24.04

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    python3 \
    python3-pip \
    python3-venv \
    tesseract-ocr \
    tesseract-ocr-ces \
    tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Create virtual environment
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies for OCR
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn \
    pytesseract \
    PyMuPDF \
    python-multipart \
    Pillow

# Copy service files
COPY services/tesseract_service.py /app/services/tesseract_service.py
COPY app_tesseract.py /app/app_tesseract.py

# Create empty __init__.py for imports
RUN touch /app/services/__init__.py

# Environment variables
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "app_tesseract:app", "--host", "0.0.0.0", "--port", "8000"]

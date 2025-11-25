# Tesseract Client

CPU-based OCR service using Tesseract with Czech and English language support.

## Overview

This service provides REST API endpoints for optical character recognition (OCR) using Tesseract. It processes images and PDF documents, extracting text in Czech and English.

## Configuration

### Base Image
- `docker.io/ubuntu:24.04`

### Port
- **8003** - API endpoint (deployed on server)
- **8000** - Container internal port

### Environment Variables
- `PYTHONPATH=/app`
- `PATH="/opt/venv/bin:$PATH"` - Python virtual environment

## Dependencies

### System
- `curl` - Health checks
- `python3` - Python runtime
- `python3-pip` - Package installer
- `python3-venv` - Virtual environment
- `tesseract-ocr` - OCR engine
- `tesseract-ocr-ces` - Czech language data
- `tesseract-ocr-eng` - English language data

### Python
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `pytesseract` - Python wrapper for Tesseract
- `PyMuPDF` - PDF processing (fitz)
- `python-multipart` - File upload handling
- `Pillow` - Image processing

## Building

```bash
podman build -t tesseract-client:latest -f Dockerfile .
```

## Running

```bash
podman run -d \
  --name tesseract-api \
  -p 8003:8000 \
  tesseract-client:latest
```

## Health Check

The service includes automatic health monitoring:
- **Interval**: 30s
- **Timeout**: 10s
- **Start period**: 30s (faster startup than GPU services)
- **Retries**: 3
- **Endpoint**: `http://localhost:8000/health`

## API Endpoints

### Health Check
```bash
curl http://localhost:8003/health
```

### OCR from Image
```bash
curl -X POST http://localhost:8003/ocr \
  -F "file=@document.png" \
  -F "lang=ces+eng"
```

### OCR from PDF
```bash
curl -X POST http://localhost:8003/ocr/pdf \
  -F "file=@document.pdf" \
  -F "lang=ces+eng"
```

## Service Files

The container requires these application files:
- `services/tesseract_service.py` - Tesseract OCR service implementation
- `app_tesseract.py` - FastAPI application

## Supported Languages

- **Czech** (`ces`) - Primary language for Czech documents
- **English** (`eng`) - Secondary language
- Combined: `ces+eng` for mixed-language documents

## Features

- Image OCR (PNG, JPG, etc.)
- PDF OCR (multi-page support)
- Language detection
- Text layout preservation
- Confidence scores

## Server Reference

**Deployed on**: `yms@192.168.191.189`
**Source**: `~/tesseract-service/Dockerfile.tesseract`
**Port**: 8003
**Engine**: Tesseract OCR

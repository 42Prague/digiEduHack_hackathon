# Whisper Client

GPU-accelerated audio transcription service using OpenAI Whisper with AMD ROCm.

## Overview

This service provides REST API endpoints for transcribing audio files using the Whisper model with ROCm GPU acceleration.

## Configuration

### Base Image
- `docker.io/rocm/pytorch:rocm7.1_ubuntu24.04_py3.12_pytorch_release_2.8.0`

### Port
- **8000** - API endpoint

### Environment Variables
- `PYTHONPATH=/app`
- `HSA_OVERRIDE_GFX_VERSION=11.0.0` - ROCm GPU compatibility
- `PYTORCH_HIP_ALLOC_CONF=expandable_segments:True` - Memory management

## Dependencies

### System
- `curl` - Health checks
- `ffmpeg` - Audio processing

### Python
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `openai-whisper` - Transcription model
- `python-multipart` - File upload handling

## Building

```bash
podman build -t whisper-client:latest -f Dockerfile .
```

## Running

```bash
podman run -d \
  --name whisper-api \
  -p 8000:8000 \
  --device=/dev/kfd --device=/dev/dri \
  --security-opt seccomp=unconfined \
  whisper-client:latest
```

## Health Check

The service includes automatic health monitoring:
- **Interval**: 30s
- **Timeout**: 10s
- **Start period**: 180s (allows model loading)
- **Retries**: 3
- **Endpoint**: `http://localhost:8000/health`

## API Endpoints

### Health Check
```bash
curl http://localhost:8000/health
```

### Transcription
```bash
curl -X POST http://localhost:8000/transcribe \
  -F "file=@audio.mp3"
```

## Server Reference

**Deployed on**: `yms@192.168.191.189`
**Source**: `~/whisper-api/Dockerfile.rocm`
**Port**: 8000

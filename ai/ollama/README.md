# GPT-OSS Client

Simple Python client for interacting with Ollama/GPT-OSS API.

## Overview

This service provides a lightweight Python client for making requests to the GPT-OSS (Ollama) API running on the server.

## Configuration

### Base Image
- `python:3.11-slim`

### Port
- **8005** - Client service port

### Environment Variables
- `OLLAMA_URL=http://192.168.191.189:8004` - GPT-OSS API endpoint

## Dependencies

### Python
- `requests` - HTTP client library

## Building

```bash
podman build -t gpt-oss-client:latest -f Dockerfile .
```

## Running

```bash
podman run -d \
  --name gpt-oss-client \
  -p 8005:8005 \
  -e OLLAMA_URL=http://192.168.191.189:8004 \
  gpt-oss-client:latest
```

## Usage

The client connects to the Ollama API at the specified URL and provides a simple interface for LLM inference.

### Example Request
```python
import requests

response = requests.post("http://localhost:8005/generate", json={
    "prompt": "Hello, how are you?",
    "model": "llama2"
})
```

## Server Reference

**Deployed on**: `yms@192.168.191.189`
**Ollama API Port**: 8004
**Client Port**: 8005

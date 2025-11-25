# CSV Data Extractor

Simple LangChain application that extracts structured CSV data from text using GPT-OSS:20B.

## Features

- **Dynamic Schema**: Define CSV columns with name, type, and description
- **Type Validation**: Automatic type checking (string, number, date, etc.)
- **Relevance Scoring**: Detects if text matches schema intent (0-1 score)
- **Multi-row Support**: Extracts multiple entities from single text
- **Docker Ready**: Simple containerized deployment

## Quick Start

### 1. Environment Setup

Copy the example environment file and configure your settings:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```bash
# Ollama Configuration
OLLAMA_URL=http://192.168.191.189:8004
OLLAMA_MODEL=gpt-oss:20b
OLLAMA_TEMPERATURE=0.1

# API Server Configuration
API_HOST=0.0.0.0
API_PORT=8005

# Logging Configuration
LOG_LEVEL=INFO
```

### 2. Run the Application

#### Option A: Docker

```bash
cd csv-extractor

# Build image
docker build -t csv-extractor .

# Run container (environment variables will be loaded from .env)
docker run -p 8005:8005 --env-file .env csv-extractor
```

#### Option B: Local Python

```bash
cd csv-extractor

# Install dependencies
pip install -r requirements.txt

# Run server (environment variables will be loaded from .env)
python app.py
```

## Usage

### API Endpoint

**POST** `/extract`

**Request:**
```json
{
  "text": "John Doe is 35 years old, email: john@example.com",
  "schema": [
    {"name": "name", "type": "string", "description": "Full name"},
    {"name": "age", "type": "number", "description": "Age in years"},
    {"name": "email", "type": "string", "description": "Email address"}
  ]
}
```

**Response:**
```json
{
  "relevance_score": 0.95,
  "rows": [
    {"name": "John Doe", "age": 35, "email": "john@example.com"}
  ],
  "explanation": "Extracted complete person information..."
}
```

### Example Client

```bash
# Run examples
python example_request.py
```

### cURL Example

```bash
curl -X POST http://localhost:8005/extract \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Alice works as a Data Scientist at age 28",
    "schema": [
      {"name": "name", "type": "string", "description": "Person name"},
      {"name": "age", "type": "number", "description": "Age"},
      {"name": "role", "type": "string", "description": "Job title"}
    ]
  }'
```

## Supported Types

- `string` - Text data
- `number` - Integer or float
- `integer` - Integer only
- `float` - Decimal number
- `boolean` - true/false
- `date` - Date (ISO format)
- `datetime` - Date and time (ISO format)

## Configuration

### Environment Variables

All configuration is managed through environment variables in the `.env` file:

| Variable | Description | Default |
|----------|-------------|---------|
| `OLLAMA_URL` | URL of the Ollama server | `http://localhost:11434` |
| `OLLAMA_MODEL` | Model name to use | `gpt-oss:20b` |
| `OLLAMA_TEMPERATURE` | Temperature for generation (0.0-1.0) | `0.1` |
| `API_HOST` | Host to bind the API server | `0.0.0.0` |
| `API_PORT` | Port for the API server | `8005` |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | `INFO` |

### Programmatic Override

You can also override settings programmatically:

```python
from csv_extractor import CSVExtractor

# Custom configuration
extractor = CSVExtractor(
    ollama_url="http://your-ollama-server:8004",
    model="custom-model",
    temperature=0.2
)
```

## Requirements

- Python 3.11+
- Access to Ollama server with GPT-OSS:20B model
- Docker (optional, for containerized deployment)

## API Documentation

Once running, visit:
- API docs: `http://localhost:8005/docs`
- Health check: `http://localhost:8005/health`

## Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ POST /extract
       │ {text, schema}
       ▼
┌─────────────┐
│  FastAPI    │
│    App      │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ CSV         │
│ Extractor   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ LangChain   │
│ + Pydantic  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ GPT-OSS:20B │
│  (Ollama)   │
└─────────────┘
```

## Files

- `app.py` - FastAPI application
- `csv_extractor.py` - Core extraction logic
- `example_request.py` - Usage examples
- `Dockerfile` - Container definition
- `requirements.txt` - Python dependencies
- `README.md` - This file

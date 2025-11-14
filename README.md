# EduScale Engine

A data ingestion and analytics platform designed to handle messy educational data with ML-based pipelines and natural language querying.

## Tech Stack

- **Python 3.11**: Modern Python with performance improvements
- **FastAPI**: High-performance async web framework
- **Docker**: Containerization for consistent environments
- **docker-compose**: Local development orchestration
- **Google Cloud Run**: Serverless container deployment platform

## Architecture

This is the foundational infrastructure skeleton for EduScale Engine. The current implementation provides:

- FastAPI application with health check endpoint
- Environment-based configuration management
- Structured logging for Cloud Run
- Docker containerization with multi-stage builds
- Local development environment with hot reload

### Implemented Features

- File upload API for educational data
- ML-based data ingestion pipelines
- BigQuery integration for data warehousing
- **Natural language to SQL query interface** (NLQ Chat) - [Documentation](docs/NLQ_FEATURE.md)
- Data quality validation and cleaning

#### Natural Language Query (NLQ) Chat

Ask questions about your educational data in plain English:
- **Chat UI**: Access at `/nlq/chat` for interactive querying
- **REST API**: POST to `/api/v1/nlq/chat` for programmatic access
- **Powered by**: Llama 3.1 8B Instruct via Featherless.ai API
- **Safe & Validated**: Read-only queries with multi-layer safety checks
- **Demo Ready**: 5 pre-tested queries for presentations

See [NLQ Feature Documentation](docs/NLQ_FEATURE.md) for detailed setup and usage.

## Getting Started

### Prerequisites

- Python 3.11+
- Docker and docker-compose (for containerized development)
- Google Cloud SDK (for deployment)

### Configuration

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and configure your environment variables:
   - `ENV`: Environment name (local, dev, prod)
   - `SERVICE_NAME`: Service name (default: eduscale-engine)
   - `SERVICE_VERSION`: Version number (default: 0.1.0)
   - `GCP_PROJECT_ID`: Your Google Cloud project ID
   - `GCP_REGION`: Deployment region (default: europe-west1)

### Running Locally (Without Docker)

1. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   uvicorn eduscale.main:app --reload --host 0.0.0.0 --port 8000
   ```

4. Access the application:
   - Health check: http://localhost:8000/health
   - API docs: http://localhost:8000/docs

### Running with Docker Compose

1. Start the development environment:
   ```bash
   docker compose -f docker/docker-compose.dev.yml up --build
   ```

2. The application will be available at http://localhost:8000

3. Code changes will automatically reload the application

4. Stop the environment:
   ```bash
   docker compose -f docker/docker-compose.dev.yml down
   ```

## Testing

Run tests with pytest:

```bash
pytest
```

## Deployment to Google Cloud Run

### Build and Push Container Image

```bash
# Set your GCP project ID
export GCP_PROJECT_ID=your-project-id

# Build the Docker image
docker build -f docker/Dockerfile -t gcr.io/$GCP_PROJECT_ID/eduscale-engine:latest .

# Push to Google Container Registry
docker push gcr.io/$GCP_PROJECT_ID/eduscale-engine:latest
```

### Deploy to Cloud Run

```bash
gcloud run deploy eduscale-engine \
  --image=gcr.io/$GCP_PROJECT_ID/eduscale-engine:latest \
  --region=europe-west1 \
  --platform=managed \
  --allow-unauthenticated \
  --port=8080 \
  --set-env-vars ENV=prod,SERVICE_VERSION=0.1.0
```

**Note**: This is a manual deployment example. For production use, implement a CI/CD pipeline with automated testing and deployment.

## Project Structure

```
.
├── src/
│   └── eduscale/
│       ├── __init__.py
│       ├── main.py              # Application entrypoint
│       ├── api/                 # API routes
│       │   └── v1/
│       │       └── routes_health.py
│       ├── core/                # Core utilities
│       │   ├── config.py        # Configuration management
│       │   └── logging.py       # Logging setup
│       ├── models/              # Data models (placeholder)
│       └── ingest/              # Ingestion logic (placeholder)
├── tests/                       # Test files
├── docker/
│   ├── Dockerfile              # Multi-stage production build
│   └── docker-compose.dev.yml  # Local development setup
├── requirements.txt            # Python dependencies
├── .env.example               # Environment template
└── README.md                  # This file
```

## License

[Add your license here]

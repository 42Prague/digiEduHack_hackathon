# Implementation Plan

- [x] 1. Create project structure and configuration files
  - Create the complete directory structure under `src/eduscale/` with all necessary `__init__.py` files
  - Create `requirements.txt` with pinned versions of fastapi, uvicorn[standard], pydantic, python-dotenv, httpx, and pytest
  - Create `.env.example` with template environment variables (ENV, SERVICE_NAME, SERVICE_VERSION, GCP_PROJECT_ID, GCP_REGION, GCP_RUN_SERVICE)
  - Create `.gitignore` to exclude `.env`, `__pycache__`, `.venv`, and other development artifacts
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 3.4, 5.1, 5.2, 5.3_

- [x] 2. Implement core configuration system
  - Create `src/eduscale/core/config.py` with pydantic BaseSettings class
  - Define Settings class with fields: ENV, SERVICE_NAME, SERVICE_VERSION, GCP_PROJECT_ID, GCP_REGION, GCP_RUN_SERVICE
  - Set default values: SERVICE_NAME="eduscale-engine", SERVICE_VERSION="0.1.0", GCP_REGION="europe-west1"
  - Configure Settings to load from .env file with case_sensitive=True
  - Export singleton settings instance at module level
  - _Requirements: 3.1, 3.2, 3.3, 3.5_

- [x] 3. Implement logging system
  - Create `src/eduscale/core/logging.py` with setup_logging() function
  - Configure Python logging to output structured logs to stdout
  - Set log format to include timestamp, level, logger name, and message in a structured format
  - Configure log level based on environment (DEBUG for local, INFO for production)
  - Ensure logging configuration is suitable for Cloud Run log ingestion
  - _Requirements: 4.1, 4.2, 4.5_

- [x] 4. Implement health check endpoint
  - Create `src/eduscale/api/v1/routes_health.py` with APIRouter
  - Implement GET /health endpoint that returns JSON with status, service, and version fields
  - Set status field to "ok" in the response
  - Read service and version values from the configuration system
  - Use async handler function for consistency with FastAPI patterns
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [x] 5. Create FastAPI application factory
  - Create `src/eduscale/main.py` with create_app() factory function
  - Initialize logging system at the start of create_app()
  - Create FastAPI instance with appropriate title and version from configuration
  - Register the health check router from api/v1/routes_health.py
  - Export app instance at module level by calling create_app()
  - _Requirements: 2.5, 4.3_

- [x] 6. Create multi-stage Dockerfile
  - Create `docker/Dockerfile` with Python 3.11 slim base image
  - Implement builder stage that installs dependencies using pip install --no-cache-dir
  - Implement runtime stage that copies artifacts from builder
  - Create non-root user 'appuser' and set as runtime user
  - Set PYTHONUNBUFFERED=1 and PYTHONDONTWRITEBYTECODE=1 environment variables
  - Set WORKDIR to /app and copy source code from src/ to /app/src
  - Expose PORT environment variable with default value 8080
  - Set CMD to run uvicorn with host 0.0.0.0 and port from $PORT environment variable
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8_

- [x] 7. Create docker-compose configuration for local development
  - Create `docker/docker-compose.dev.yml` with api service definition
  - Configure build context to project root and dockerfile to docker/Dockerfile
  - Mount src/ directory as volume to /app/src for live code reloading
  - Map port 8000 on host to port 8000 in container
  - Configure service to load environment variables from .env file
  - Override command to use uvicorn with --reload flag for hot reloading
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6_

- [x]* 8. Implement health endpoint test
  - Create `tests/test_health.py` with pytest test function
  - Import FastAPI TestClient and the app instance from eduscale.main
  - Write test that makes GET request to /health endpoint
  - Assert response status code is 200
  - Assert response JSON contains status, service, and version keys
  - Assert status field equals "ok"
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6_

- [x] 9. Create comprehensive README documentation
  - Create `README.md` with project name "EduScale Engine" and one-sentence description
  - Document tech stack: Python 3.11, FastAPI, Docker, docker-compose, Google Cloud Run
  - Add section with instructions for running locally without Docker (venv, pip install, uvicorn command)
  - Add section with instructions for running with Docker Compose
  - Document how to copy .env.example to .env and configure environment variables
  - Add high-level architecture note mentioning this is the skeleton and listing future features
  - Include example gcloud run deploy command for Cloud Run deployment
  - Add note that deployment example is not fully automated CI/CD
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7_

- [x] 10. Verify complete setup and deployment readiness
  - Verify application runs locally without Docker using uvicorn command
  - Verify application runs with docker-compose and hot reload works
  - Run pytest and verify all tests pass
  - Build Docker image and verify it builds successfully
  - Run Docker container and verify health endpoint responds correctly
  - Verify logs appear in stdout with correct format
  - Test that PORT environment variable is respected by the container
  - _Requirements: 5.5, 6.5, 10.1, 10.2, 10.3_

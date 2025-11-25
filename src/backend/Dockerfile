# Stage 1: Builder
FROM python:3.10-slim AS builder

# Environment configuration
ENV PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    VENV_PATH=/opt/venv

# Create isolated virtual environment
RUN python -m venv ${VENV_PATH}
ENV PATH="${VENV_PATH}/bin:${PATH}"

# Install build prerequisites
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Upgrade pip tooling
RUN python -m pip install --upgrade pip setuptools wheel

# Copy project metadata and source code
WORKDIR /app
COPY pyproject.toml ./
COPY uv.lock ./
COPY README.md ./
COPY scripts ./scripts
COPY migrations ./migrations
COPY swx_api ./swx_api

# Install project into the virtual environment
RUN pip install --no-cache-dir -e . && \
    pip install --no-cache-dir gunicorn

# Stage 2: Runtime image
FROM python:3.10-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    VENV_PATH=/opt/venv \
    PATH="${VENV_PATH}/bin:${PATH}"

WORKDIR /app

# Copy virtual environment and application source
COPY --from=builder ${VENV_PATH} ${VENV_PATH}
COPY swx_api ./swx_api
COPY migrations ./migrations
COPY README.md ./
COPY scripts ./scripts
COPY data ./data

# Runtime dependencies (pandas requires libstdc++)
RUN apt-get update && apt-get install -y --no-install-recommends libstdc++6 && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

EXPOSE 8000

# Use full path to gunicorn to ensure it's found
CMD ["/opt/venv/bin/gunicorn", "-k", "uvicorn.workers.UvicornWorker", "swx_api.core.main:app", "-b", "0.0.0.0:8000", "--workers", "2", "--threads", "4", "--log-level", "info", "--timeout", "60", "--keep-alive", "5"]

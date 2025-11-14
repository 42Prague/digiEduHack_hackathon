# Multi-stage Dockerfile for EduScale Engine

# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/src \
    PORT=8080

# Create non-root user
RUN useradd -m -u 1000 appuser

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy source code
COPY src/ /app/src/

# Set ownership to non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port (will be overridden by Cloud Run)
EXPOSE ${PORT}

# Run the application
CMD ["sh", "-c", "uvicorn eduscale.main:app --host 0.0.0.0 --port ${PORT}"]

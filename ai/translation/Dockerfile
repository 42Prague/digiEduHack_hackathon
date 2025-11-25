# ===========================
# Stage 1: Runtime image
# ===========================
FROM python:3.11-slim

# Ensure stdout/stderr are unbuffered and nice logs
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Optional: configure Ollama address via env (default already in code)
# ENV OLLAMA_HOST=192.168.191.189
# ENV OLLAMA_PORT=11434
# ENV OLLAMA_MODEL_NAME=gpt-oss:20b

# Set workdir
WORKDIR /app

# Install OS deps (just in case)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy application code
COPY app.py /app/gpt_oss_analysis_api.py

# Expose the API port (matches uvicorn in __main__)
EXPOSE 8002

# Default command: start FastAPI with uvicorn
CMD ["uvicorn", "gpt_oss_analysis_api:app", "--host", "0.0.0.0", "--port", "8002"]


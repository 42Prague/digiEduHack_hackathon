FROM python:3.11-slim

# Install system deps (optional but often useful)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY app ./app

ENV PYTHONPATH=/app

# Default env (override in docker-compose or 'docker run')
ENV APP_HOST=0.0.0.0
ENV APP_PORT=8000

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

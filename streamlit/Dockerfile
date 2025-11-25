FROM python:3.11

# Set working directory inside container
WORKDIR /app

# Install system dependencies if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file and install Python dependencies
COPY requirements.txt .
RUN python -m pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/app ./src/app

# Expose Streamlit's default port
EXPOSE 8501

# Health check to ensure Streamlit is running
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')"

# Run Streamlit on all network interfaces (0.0.0.0) so it's accessible from host
CMD ["streamlit", "run", "src/app/main.py", "--server.address=0.0.0.0", "--server.port=8501"]


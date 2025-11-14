# Whisper API with ROCm/GPU support
FROM docker.io/rocm/pytorch:rocm7.1_ubuntu24.04_py3.12_pytorch_release_2.8.0

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y     ffmpeg     libsndfile1     && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements-rocm.txt /app/requirements-rocm.txt
COPY requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements-rocm.txt

# Install openai-whisper WITHOUT dependencies to preserve ROCm PyTorch
RUN pip3 install --no-deps openai-whisper==20231117

# Copy application code
COPY app_whisper_rocm.py /app/app_whisper_rocm.py
COPY services/ /app/services/

# Set environment variables
ENV WHISPER_MODEL_SIZE=large-v3
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# Run the application
CMD ["uvicorn", "app_whisper_rocm:app", "--host", "0.0.0.0", "--port", "8000"]

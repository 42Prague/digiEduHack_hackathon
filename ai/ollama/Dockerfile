# ROCm 7.1-based Dockerfile for GPT-OSS-20B with vLLM
FROM docker.io/rocm/pytorch:rocm7.1_ubuntu24.04_py3.12_pytorch_release_2.8.0

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install vLLM with ROCm support
# Note: vLLM 0.8+ has better ROCm support
RUN pip install --no-cache-dir \
    vllm>=0.8.0 \
    transformers>=4.50.0 \
    accelerate \
    triton==3.4 \
    kernels \
    openai

# Environment variables for ROCm optimization
# HSA_OVERRIDE_GFX_VERSION for gfx1151 compatibility (Radeon 8060S)
ENV HSA_OVERRIDE_GFX_VERSION=11.0.0
ENV PYTORCH_HIP_ALLOC_CONF=expandable_segments:True
ENV VLLM_USE_TRITON_FLASH_ATTN=1
# Critical: Tell vLLM to use ROCm/HIP instead of CUDA
ENV VLLM_WORKER_MULTIPROC_METHOD=spawn
ENV VLLM_LOGGING_LEVEL=INFO
ENV HIP_VISIBLE_DEVICES=0

# Model configuration
ENV MODEL_NAME=openai/gpt-oss-20b
ENV MODEL_DIR=/models/gpt-oss-20b
ENV PORT=8004

# Expose port
EXPOSE 8004

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:8004/health || exit 1

# Run vLLM server with optimized settings for gfx1151
CMD vllm serve ${MODEL_NAME} \
    --host 0.0.0.0 \
    --port ${PORT} \
    --download-dir ${MODEL_DIR} \
    --device hip \
    --trust-remote-code \
    --max-model-len 8192 \
    --gpu-memory-utilization 0.90 \
    --dtype half \
    --enable-prefix-caching \
    --disable-log-requests

# Multi-stage Dockerfile for TAKTKRONE-I

# Stage 1: Base image with CUDA support
FROM nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04 AS base

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3.10-dev \
    python3-pip \
    git \
    wget \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create symlinks for python
RUN ln -sf /usr/bin/python3.10 /usr/bin/python && \
    ln -sf /usr/bin/pip3 /usr/bin/pip

# Upgrade pip
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

WORKDIR /app

# Stage 2: Development image
FROM base AS development

# Copy requirements first for better caching
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e ".[all]"

# Copy source code
COPY . .

# Install in editable mode
RUN pip install -e .

CMD ["bash"]

# Stage 3: Training image
FROM base AS training

COPY pyproject.toml ./
RUN pip install --no-cache-dir -e ".[train]"

COPY occlm/ ./occlm/
COPY configs/ ./configs/
COPY scripts/ ./scripts/

RUN pip install -e .

# Set up directories
RUN mkdir -p /data /models /results

VOLUME ["/data", "/models", "/results"]

CMD ["python", "-m", "occlm.training"]

# Stage 4: Serving image (production)
FROM base AS serving

COPY pyproject.toml ./
RUN pip install --no-cache-dir -e ".[serve]"

COPY occlm/ ./occlm/
COPY configs/ ./configs/

RUN pip install -e .

# Non-root user for security
RUN useradd -m -u 1000 occlm && \
    chown -R occlm:occlm /app

USER occlm

# Expose API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["python", "-m", "occlm.serving", \
     "--host", "0.0.0.0", \
     "--port", "8000"]

# Stage 5: Demo image (Gradio UI)
FROM serving AS demo

RUN pip install --no-cache-dir gradio

EXPOSE 7860

CMD ["python", "-m", "occlm.ui.demo", \
     "--server-name", "0.0.0.0", \
     "--server-port", "7860"]

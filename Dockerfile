# Multi-stage Dockerfile for running mkquartodocs tests
# Optimized for layer caching in CI environments
#
# Key design principles:
# 1. Dependencies are installed from requirements.txt (exported externally by CI)
# 2. Source code is NOT copied - it's mounted at runtime via -v flag
# 3. Cache invalidation happens only when dependencies change, not on version bumps

# Build argument for Python version
ARG PYTHON_VERSION=3.12
ARG QUARTO_VERSION=1.9.10

# Stage 1: Base image with Quarto and system dependencies
FROM ghcr.io/quarto-dev/quarto:${QUARTO_VERSION} AS base

# Install system dependencies in a single layer
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    chromium-browser \
    xvfb \
    curl \
    ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create symbolic link for python
RUN ln -sf /usr/bin/python3 /usr/bin/python || true

# Install Chromium for Quarto (for mermaid diagrams)
# This is a heavy operation, so we do it in the base layer for caching
RUN quarto install chromium --no-prompt

# Stage 2: Python environment with dependencies
FROM base AS python-env

ARG PYTHON_VERSION

# Install uv (fast Python package installer)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

# Install Python dependencies from requirements.txt
# This file is generated externally by the CI workflow using:
#   uv export --no-hashes --python ${PYTHON_VERSION} --all-groups > requirements.txt
#
# Benefits of this approach:
# - Cache only invalidates when actual dependencies change
# - Version bumps in pyproject.toml don't trigger rebuilds
# - More explicit control over what causes cache invalidation
#
# Note: We filter out the editable install line (-e .) since source code
# will be mounted at runtime, not baked into the image
COPY requirements.txt /tmp/requirements.txt
RUN --mount=type=cache,target=/root/.cache/uv \
    grep -v '^-e' /tmp/requirements.txt > /tmp/requirements-filtered.txt && \
    uv venv /opt/venv --python ${PYTHON_VERSION} && \
    uv pip install --python /opt/venv -r /tmp/requirements-filtered.txt

# Activate the virtual environment
ENV PATH="/opt/venv/bin:${PATH}"
ENV VIRTUAL_ENV="/opt/venv"

# Set working directory where code will be mounted
WORKDIR /work

# No CMD - command should be specified at runtime to match CI/local usage

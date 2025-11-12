# Multi-stage Dockerfile for running mkquartodocs tests
# Optimized for layer caching in CI environments

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
    curl \
    ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create symbolic link for python
RUN ln -sf /usr/bin/python3 /usr/bin/python || true

# Install Chromium for Quarto (for mermaid diagrams)
# This is a heavy operation, so we do it in the base layer for caching
RUN quarto install chromium --no-prompt

# Stage 2: Python environment with uv
FROM base AS python-env

ARG PYTHON_VERSION

# Install uv (fast Python package installer)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

# Install common Python packages used in documentation
# These rarely change, so we install them in a separate layer
# Install dependencies
# Note: We use --python to specify the Python version, and uv will install it if needed
# We don't use --locked because different Python versions may have different lock requirements
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --python ${PYTHON_VERSION} --no-install-project

# Stage 3: Development image with project dependencies
FROM python-env AS dev

# Copy dependency files first (for better caching)
COPY pyproject.toml .
COPY uv.lock . 
COPY tests .
COPY mkquartodocs .

# Default command
CMD ["uv", "run", "--all-groups", "python", "-m", "pytest", "-xs", "--cov", ".", "--cov-report=xml"]

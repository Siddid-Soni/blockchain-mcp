# syntax=docker/dockerfile:1

FROM python:3.10-slim AS base

# Install system dependencies for solc, slither, mythril, manticore, smartcheck, echidna, maian
# (Some tools require build-essential, git, curl, etc.)

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    curl \
    ca-certificates \
    wget \
    python3-dev \
    libssl-dev \
    libffi-dev \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

# Install solc (Solidity compiler)
RUN curl -fsSL https://github.com/ethereum/solidity/releases/download/v0.8.19/solc-static-linux -o /usr/local/bin/solc \
    && chmod +x /usr/local/bin/solc

# Install manticore, smartcheck, echidna, maian dependencies (if needed)
# (Assume these are installed via pip or available in the image)

FROM base AS builder

WORKDIR /app

# Install uv (prebuilt binary)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy dependency files and source code
COPY --link pyproject.toml ./
COPY --link src/ ./src/
COPY --link test_contract.sol ./test_contract.sol

# Create venv and install dependencies
ENV UV_CACHE_DIR=/root/.cache/uv
RUN --mount=type=cache,target=$UV_CACHE_DIR \
    uv venv && \
    uv pip install -e .

# (Optional) Install additional tools not available via pip
# Example: smartcheck, echidna, maian, manticore
# For brevity, assume they are installed via pip or available in the image

FROM base AS final

WORKDIR /app

# Create non-root user
RUN useradd -m appuser
USER appuser

# Copy venv and app code from builder
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/src /app/src
COPY --from=builder /app/test_contract.sol /app/test_contract.sol

ENV PATH="/app/.venv/bin:$PATH"

# Entrypoint: run the MCP server
ENTRYPOINT ["python", "-m", "blockchain_vuln_analyzer"]

# (No EXPOSE, as MCP runs over stdio)

# .dockerignore should include:
# .git
# .gitignore
# .venv
# *.lock
# .env
# __pycache__
# node_modules
# dist
# build
# *.pyc
# *.pyo
# *.egg-info

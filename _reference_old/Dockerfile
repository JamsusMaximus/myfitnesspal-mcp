# syntax=docker/dockerfile:1.4

ARG PYTHON_VERSION=3.11
FROM --platform=$BUILDPLATFORM python:${PYTHON_VERSION}-alpine

WORKDIR /app

# Install system dependencies for uv and potential wheel building
# libffi-dev and openssl-dev are common for Python C extensions.
# build-base provides compilers.
RUN apk add --no-cache build-base libffi-dev openssl-dev

# Install uv
RUN pip install uv

# Create a non-root user and group
RUN addgroup -S appgroup && adduser -S -G appgroup appuser

# Copy dependency definition and lock files
COPY pyproject.toml uv.lock ./

# Install dependencies using uv, leveraging the lock file for reproducibility
# --system installs into the global site-packages, suitable for Docker
# --no-cache avoids populating uv's cache to keep the image small
RUN uv pip sync pyproject.toml --system --no-cache

# Copy application code
# Ensure correct ownership for the non-root user
COPY --chown=appuser:appgroup src/ ./src/

# Expose the port the app runs on (FastAPI app will run on port 80 internally)
EXPOSE 80

# Switch to the non-root user
USER appuser

# Command to run the application using uv and uvicorn
# PYTHONPATH=src ensures modules in src/ are importable
CMD ["uv", "run", "env", "PYTHONPATH=src", "uvicorn", "src.nutrition_coach.api_server:app", "--host", "0.0.0.0", "--port", "80"]
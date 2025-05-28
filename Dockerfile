# syntax=docker/dockerfile:1.4

# ---- Builder Stage ----
ARG PYTHON_VERSION=3.11
FROM --platform=$BUILDPLATFORM python:${PYTHON_VERSION}-alpine AS builder

WORKDIR /app

# Install build dependencies for Poetry and potential wheel building
RUN apk add --no-cache curl build-base libffi-dev openssl-dev

# Install poetry
ENV POETRY_HOME="/opt/poetry" \
    POETRY_VERSION="1.8.3"
ENV PATH="$POETRY_HOME/bin:$PATH"
RUN curl -sSL https://install.python-poetry.org | python3 - \
    && poetry --version

# Copy dependency files
COPY poetry.lock pyproject.toml ./

# Attempt to make the lock file compatible with the current Poetry version
RUN poetry lock --no-update

# poetry export removed, will install directly in runtime

# ---- Runtime Stage ----
FROM --platform=$BUILDPLATFORM python:${PYTHON_VERSION}-alpine AS runtime

WORKDIR /app

# Create a non-root user and group
RUN addgroup -S appgroup && adduser -S -G appgroup appuser

# Install Poetry and runtime dependencies
RUN apk add --no-cache libffi curl # Added curl

# Install poetry in runtime
ENV POETRY_HOME="/opt/poetry" \
    POETRY_VERSION="1.8.3"
ENV PATH="$POETRY_HOME/bin:$PATH"
RUN curl -sSL https://install.python-poetry.org | python3 - \
    && poetry --version

# Copy dependency files for poetry install
COPY pyproject.toml poetry.lock ./

# Install runtime dependencies using Poetry
# libffi is a common runtime dependency, add others if needed by your packages
RUN --mount=type=cache,target=/opt/poetry/cache \
    --mount=type=cache,target=/root/.cache/pip \
    poetry install --no-dev --no-interaction --no-ansi --no-root

# Copy application code from the src directory in your project
# Ensure correct ownership for the non-root user
COPY --chown=appuser:appgroup src/ ./src/

# Expose the port the app runs on
EXPOSE 5000

# Switch to the non-root user
USER appuser

# Command to run the application
# Based on your README: python src/nutrition_coach/api_server.py
CMD ["python", "src/nutrition_coach/api_server.py"]
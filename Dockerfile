# CORRECTED DOCKERFILE - uv sync build
FROM python:3.13.1-slim

# Timestamp for cache busting - BUILD $(date +%s)
RUN echo "=== PIP BUILD - $(date) ===" && \
    echo "Using pip install for dependencies" && \
    echo "======================================="

# Set environment variables
ARG APP_ENV=production
ENV APP_ENV=${APP_ENV} \
    PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PYTHONPATH=/

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean


# Create user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml ./
COPY uv.lock ./

# Install dependencies with pip
RUN echo "=== INSTALLING DEPENDENCIES ===" && \
    pip install -e . && \
    echo "SUCCESS: Dependencies installed"

# Copy application code
COPY . .

# Setup permissions
RUN chown -R appuser:appuser /app
USER appuser

# Create log directory
RUN mkdir -p /app/logs

# Expose port
EXPOSE 8000

# Command - Use PORT environment variable from Cloud Run
CMD ["sh", "-c", "python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

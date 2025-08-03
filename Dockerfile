# COMPLETE REBUILD - Use different base image
FROM python:3.13.1-slim

# RADICAL CACHE BUSTING - NEW TIMESTAMP
ARG CACHE_BUST=REBUILD-17h35
RUN echo "=== COMPLETE REBUILD - Cache bust: $CACHE_BUST ===" && \
    echo "This is a completely new build - no cache allowed" && \
    date && \
    echo "=== END CACHE BUST ==="

# Set environment variables
ARG APP_ENV=production  
ENV APP_ENV=${APP_ENV} \
    PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PYTHONPATH=/app \
    CACHE_BUST=${CACHE_BUST}

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install uv for faster dependency resolution
RUN pip install uv

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /app

# Copy dependency files first for better caching
COPY pyproject.toml ./
COPY uv.lock ./

# Create virtual environment and install dependencies
RUN echo "Installing dependencies with uv sync - REBUILD v2" && \
    uv venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN echo "Running uv sync --frozen --no-dev" && \
    uv sync --frozen --no-dev && \
    echo "Dependencies installed successfully"

# Copy the application code
COPY . .

# Make entrypoint script executable
RUN chmod +x /app/scripts/docker-entrypoint.sh

# Change ownership and switch to non-root user
RUN chown -R appuser:appuser /app
USER appuser

# Create log directory
RUN mkdir -p /app/logs

# Default port
EXPOSE 8000

# Command to run the application
CMD ["/opt/venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

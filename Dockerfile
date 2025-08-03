# CORRECTED DOCKERFILE - uv sync build
FROM python:3.13.1-slim

# Timestamp for cache busting - BUILD $(date +%s)
RUN echo "=== UVICORN FIX BUILD - $(date) ===" && \
    echo "Using uv sync --frozen --no-dev ONLY" && \
    echo "UVICORN COMMAND FIX VERSION" && \
    echo "======================================="

# Set environment variables
ARG APP_ENV=production
ENV APP_ENV=${APP_ENV} \
    PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PYTHONPATH=/app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install uv
RUN pip install uv

# Create user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml ./
COPY uv.lock ./

# Install dependencies directly with uv pip
RUN echo "=== INSTALLING DEPENDENCIES ===" && \
    uv pip install --system -e . && \
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

# Command
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
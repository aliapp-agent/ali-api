# Ali API - Optimized Production Dockerfile (com PIP)
FROM python:3.13.1-slim

# Build metadata
LABEL maintainer="Ali API Team"
LABEL version="1.0.0"
LABEL description="Ali API - FastAPI with Agno and Firebase"

# Set environment variables
ARG APP_ENV=production
ENV APP_ENV=${APP_ENV} \
    PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PORT=8080 \
    # Set Hugging Face cache directory to a location the appuser owns
    HF_HOME=/app/tmp

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create app user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /app

# Copy dependency file first (for better Docker layer caching)
COPY requirements.txt ./

# Install dependencies with PIP, with an increased timeout
RUN echo "=== INSTALLING DEPENDENCIES WITH PIP ===" && \
    pip install --no-cache-dir --timeout=100 --requirement requirements.txt && \
    echo "SUCCESS: Dependencies installed with PIP"

# Copy application code
COPY . .

# Create necessary directories with proper permissions
RUN mkdir -p /app/logs /app/data /app/tmp && \
    chmod 777 /app/logs /app/data /app/tmp

# Set up permissions
RUN chown -R appuser:appuser /app

# Switch to non-root user for security
USER appuser

# Health check (using Python instead of curl for lighter container)
HEALTHCHECK --interval=30s --timeout=15s --start-period=180s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT}/health', timeout=10)" || exit 1

# Expose port
EXPOSE ${PORT}

# Optimized startup command using standard Python
CMD ["sh", "-c", "python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080} --workers 1"]

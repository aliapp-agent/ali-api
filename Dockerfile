# Ali API - Optimized Production Dockerfile
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
    HF_HOME=/app/tmp

# Install system dependencies and uv
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl ca-certificates && \
    curl -LsSf https://astral.sh/uv/install.sh | sh && \
    apt-get purge -y --auto-remove curl && \
    rm -rf /var/lib/apt/lists/*

# Add uv to the system's PATH so it can be found in subsequent commands
ENV PATH="/root/.local/bin:${PATH}"

# Create app user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /app

# Copy dependency file first (for better Docker layer caching)
COPY requirements.txt ./

# Install dependencies with uv
RUN echo "=== INSTALLING DEPENDENCIES WITH UV ===" && \
    uv pip sync --system --no-cache requirements.txt && \
    echo "SUCCESS: Dependencies installed with UV"

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

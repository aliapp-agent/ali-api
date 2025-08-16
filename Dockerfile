# Single-Stage Dockerfile with uv
FROM python:3.12-slim

# Set essential environment variables for production
ENV PYTHONUNBUFFERED=1 \
    APP_ENV=production \
    PORT=8080 \
    PATH="/root/.local/bin:${PATH}"

# Set the working directory for the application
WORKDIR /app

# Install system dependencies, install uv, and then clean up.
# This is done in a single RUN command to reduce layer size.
# We remove curl and ca-certificates after use to keep the image smaller.
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl ca-certificates && \
    curl -LsSf https://astral.sh/uv/install.sh | sh && \
    apt-get purge -y --auto-remove curl && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements file and install dependencies.
# This is done before copying the rest of the code to leverage Docker caching.
COPY requirements.txt .
RUN uv pip sync --system --no-cache requirements.txt

# Copy the rest of the application code
COPY . .

# Create a non-root user, create necessary directories, and set permissions.
# Combining these commands reduces the number of layers in the final image.
RUN groupadd --system appgroup && \
    useradd --system -g appgroup --shell /sbin/nologin appuser && \
    mkdir -p /app/logs /app/data && \
    chown -R appuser:appgroup /app && \
    chmod -R 775 /app

# Switch to the non-root user for security
USER appuser

# Expose the port the application will run on
EXPOSE ${PORT}

# Healthcheck to verify that the application is running correctly
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; exit(0) if urllib.request.urlopen('http://localhost:${PORT}/health').getcode() == 200 else exit(1)"

# Command to run the application using uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]

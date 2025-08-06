# 🐳 Ali API - Docker Setup Guide

Complete guide for running Ali API with Docker locally.

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Docker Scripts](#docker-scripts)
- [Docker Compose](#docker-compose)
- [Manual Docker Commands](#manual-docker-commands)
- [Development](#development)
- [Production](#production)
- [Troubleshooting](#troubleshooting)
- [Performance Optimization](#performance-optimization)

## 🛠️ Prerequisites

### Required Software
- **Docker** 20.10+ ([Install Docker](https://docs.docker.com/get-docker/))
- **Docker Compose** v2+ (included with Docker Desktop)
- **curl** (for testing)
- **jq** (optional, for JSON parsing in tests)

### Required Files
- `firebase-credentials.json` - Firebase service account key
- `.env` or `.env.docker` - Environment variables
- Valid OpenAI API key

### System Requirements
- **RAM**: 2GB minimum, 4GB recommended
- **Disk**: 2GB free space for Docker image
- **CPU**: 2 cores recommended

## 🚀 Quick Start

### 1. Clone and Setup
```bash
cd ali-api
cp .env .env.docker  # Copy environment file

# IMPORTANT: Fix permissions first (prevents log errors)
mkdir -p logs data
chmod 777 logs data
```

### 2. Build and Run (Automated)
```bash
# One-command setup
./docker-build.sh && ./docker-run.sh

# Or with Docker Compose
./docker-compose-up.sh
```

### 3. Test the API
```bash
# Run comprehensive tests
./docker-test.sh

# Or manual health check
curl http://localhost:8080/health
```

### 4. Access the API
- **Root**: http://localhost:8080/
- **Health Check**: http://localhost:8080/health
- **API Docs**: http://localhost:8080/docs
- **ReDoc**: http://localhost:8080/redoc

## ⚙️ Configuration

### Environment Files

#### `.env.docker` (Recommended for Docker)
```bash
# Docker-optimized settings
APP_ENV=development
DEBUG=true
PORT=8080

# Firebase
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_CREDENTIALS_PATH=/app/firebase-credentials.json

# OpenAI
LLM_API_KEY=your-openai-api-key

# Qdrant
QDRANT_URL=your-qdrant-url
QDRANT_API_KEY=your-qdrant-key
```

#### Key Docker-Specific Settings
- **Paths**: Use container paths (`/app/...`)
- **Host**: Always use `0.0.0.0` in containers
- **CORS**: Include `host.docker.internal` for local development
- **Logging**: Use `/app/logs` for persistent logs

### Volume Mounts
```yaml
volumes:
  - ./logs:/app/logs          # Persistent logs
  - ./data:/app/data          # AgnoAgent memory
  - ./firebase-credentials.json:/app/firebase-credentials.json:ro
  - ./app:/app/app:ro         # Hot-reload (dev only)
```

## 🎯 Docker Scripts

### `docker-build.sh`
Builds the Docker image with optimizations.

```bash
./docker-build.sh                # Standard build
./docker-build.sh -v            # Verbose output
./docker-build.sh --verbose     # Show image layers
```

**Features:**
- ✅ Multi-stage build optimization
- ✅ Dependency caching
- ✅ Security hardening (non-root user)
- ✅ Health check integration
- ✅ Build validation

### `docker-run.sh`
Runs the container with proper configuration.

```bash
./docker-run.sh                 # Standard run
./docker-run.sh -l             # Show initial logs
./docker-run.sh --logs         # Show initial logs
./docker-run.sh -f             # Follow logs
./docker-run.sh --follow       # Follow logs
```

**Features:**
- ✅ Automatic port mapping (8080)
- ✅ Volume mounting for development
- ✅ Environment file loading
- ✅ Container lifecycle management
- ✅ Status monitoring

### `docker-test.sh`
Comprehensive testing suite for the containerized API.

```bash
./docker-test.sh                # Full test suite
./docker-test.sh --open         # Open API docs after test
```

**Tests:**
1. **Container Status** - Verify container is running
2. **Root Endpoint** - Basic API connectivity
3. **Health Check** - Component status validation
4. **Detailed Health** - Deep system checks
5. **API Documentation** - Swagger/ReDoc availability
6. **Resource Usage** - Memory and CPU monitoring

## 🐳 Docker Compose

### `docker-compose-up.sh`
Smart Docker Compose management script.

```bash
# Start services
./docker-compose-up.sh           # Background mode
./docker-compose-up.sh up        # Background mode
./docker-compose-up.sh up-fg     # Foreground mode

# Management
./docker-compose-up.sh down      # Stop services
./docker-compose-up.sh restart   # Restart services
./docker-compose-up.sh logs      # View logs
./docker-compose-up.sh status    # Check status

# Maintenance
./docker-compose-up.sh build     # Rebuild images
./docker-compose-up.sh clean     # Full cleanup

# Help
./docker-compose-up.sh help      # Show all commands
```

### Docker Compose Features
- ✅ **Zero-dependency setup** (no external services)
- ✅ **Hot-reload development** (volume mounting)
- ✅ **Resource limits** (memory/CPU constraints)
- ✅ **Health monitoring** (automatic container restarts)
- ✅ **Persistent storage** (logs, AgnoAgent memory)

## 🔧 Manual Docker Commands

### Build Image
```bash
docker build -t ali-api:latest .
docker build -t ali-api:dev --build-arg APP_ENV=development .
```

### Run Container
```bash
# Basic run
docker run -d \
  --name ali-api-dev \
  -p 8080:8080 \
  --env-file .env.docker \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/firebase-credentials.json:/app/firebase-credentials.json:ro \
  ali-api:latest

# Development mode with hot-reload
docker run -d \
  --name ali-api-dev \
  -p 8080:8080 \
  --env-file .env.docker \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/app:/app/app:ro \
  -v $(pwd)/firebase-credentials.json:/app/firebase-credentials.json:ro \
  ali-api:latest
```

### Container Management
```bash
# View logs
docker logs -f ali-api-dev

# Enter container
docker exec -it ali-api-dev /bin/bash

# Check container stats
docker stats ali-api-dev

# Stop and remove
docker stop ali-api-dev
docker rm ali-api-dev
```

## 💻 Development

### Hot Reload Setup
The development configuration includes hot-reload via volume mounting:

```yaml
volumes:
  - ./app:/app/app:ro  # Mount source code as read-only
```

**Benefits:**
- ✅ Instant code changes without rebuild
- ✅ Faster development iteration
- ✅ Container isolation maintained

### Debugging
```bash
# View detailed logs
docker logs ali-api-dev --tail 100 -f

# Enter container for debugging
docker exec -it ali-api-dev /bin/bash

# Check environment variables
docker exec ali-api-dev env | grep -E "(FIREBASE|LLM|QDRANT)"

# Monitor resource usage
docker stats ali-api-dev --no-stream
```

### Development Workflow
```bash
# 1. Build image
./docker-build.sh

# 2. Run with hot-reload
./docker-run.sh

# 3. Make code changes (auto-reload)

# 4. Test changes
./docker-test.sh

# 5. Check logs
docker logs -f ali-api-dev
```

## 🏭 Production

### Production Image
```dockerfile
# Optimized for production
FROM python:3.13.1-slim

# Security hardening
USER appuser
EXPOSE 8080

# Performance optimization
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]
```

### Production Environment
```bash
# Build production image
docker build -t ali-api:prod --build-arg APP_ENV=production .

# Run production container
docker run -d \
  --name ali-api-prod \
  -p 8080:8080 \
  --env APP_ENV=production \
  --env DEBUG=false \
  --restart unless-stopped \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/data:/app/data \
  ali-api:prod
```

### Production Checklist
- [ ] Set `APP_ENV=production`
- [ ] Set `DEBUG=false`
- [ ] Use secure JWT secret
- [ ] Configure proper CORS origins
- [ ] Set up log rotation
- [ ] Configure resource limits
- [ ] Set up monitoring
- [ ] Use HTTPS proxy (nginx/traefik)

## 🔧 Troubleshooting

### Common Issues

#### 1. Container Won't Start
```bash
# Check container logs
docker logs ali-api-dev

# Common causes:
# - Missing firebase-credentials.json
# - Invalid environment variables
# - Port already in use
# - Insufficient resources
```

#### 2. Health Check Fails
```bash
# Check health status
curl http://localhost:8080/health

# Debug health issues
curl http://localhost:8080/api/v1/health/detailed

# Common causes:
# - OpenAI API key invalid
# - Firebase connection issues
# - Qdrant connectivity problems
```

#### 3. Permission Issues (Logs/Data)
```bash
# Quick fix - Set broad permissions
chmod 777 logs data

# OR - Fix ownership (requires sudo)
sudo chown -R $(id -u):$(id -g) logs data

# OR - Create directories with correct permissions first
mkdir -p logs data
chmod 777 logs data

# Check container user
docker exec ali-api-dev id

# Verify log file permissions inside container
docker exec ali-api-dev ls -la /app/logs
```

**Common Causes:**
- Host/container user ID mismatch
- Volume mount permission conflicts
- SELinux context issues (Red Hat/CentOS)

**Prevention:**
- Always run `chmod 777 logs data` before container start
- Use `USER 1000:1000` in Dockerfile to match common host user
- For production, use init containers to fix permissions

#### 4. Build Failures
```bash
# Clean build (no cache)
docker build --no-cache -t ali-api:latest .

# Check disk space
docker system df

# Clean unused resources
docker system prune -f
```

#### 5. Network Issues
```bash
# Check container network
docker inspect ali-api-dev | grep NetworkMode

# Test connectivity
docker exec ali-api-dev curl -I https://api.openai.com
```

### Debug Commands
```bash
# Full system info
docker info

# Container inspection
docker inspect ali-api-dev

# Image layers
docker history ali-api:latest

# Resource usage
docker stats ali-api-dev

# Network inspection
docker network ls
docker network inspect bridge
```

## 🚀 Performance Optimization

### Container Resources
```yaml
deploy:
  resources:
    limits:
      memory: 2G      # Maximum memory
      cpus: '1.0'     # Maximum CPU cores
    reservations:
      memory: 512M    # Reserved memory
      cpus: '0.5'     # Reserved CPU cores
```

### Image Optimization
- ✅ **Multi-stage builds** (separate build/runtime)
- ✅ **Layer caching** (strategic COPY ordering)
- ✅ **Minimal base image** (python:slim)
- ✅ **Dependency optimization** (requirements.txt caching)

### Runtime Optimization
```bash
# Single worker for development
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]

# Multiple workers for production
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "4"]
```

### Monitoring
```bash
# Resource monitoring
docker stats ali-api-dev --no-stream

# Health monitoring
watch -n 5 'curl -s http://localhost:8080/health | jq .status'

# Log monitoring
docker logs ali-api-dev --tail 50 -f | grep -i error
```

## 📊 Success Metrics

After successful setup, you should see:

### Health Check Response
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "environment": "development",
  "components": {
    "api": "healthy",
    "database": "healthy", 
    "rag_service": "healthy",
    "agno_agent": "healthy"
  }
}
```

### Container Stats
```bash
CONTAINER ID   NAME          CPU %     MEM USAGE / LIMIT   MEM %     NET I/O       BLOCK I/O   PIDS
abc123def456   ali-api-dev   2.34%     456.2MiB / 2GiB    22.3%     1.23MB / 0B   0B / 0B     45
```

### Ready Endpoints
- ✅ http://localhost:8080/ (API root)
- ✅ http://localhost:8080/health (health check)
- ✅ http://localhost:8080/docs (Swagger UI)
- ✅ http://localhost:8080/redoc (ReDoc)

---

## 📞 Support

### Quick Help
```bash
# Get help for any script
./docker-build.sh --help
./docker-run.sh --help  
./docker-test.sh --help
./docker-compose-up.sh help
```

### Container Logs
```bash
# Follow all logs
docker logs -f ali-api-dev

# Filter error logs
docker logs ali-api-dev 2>&1 | grep -i error

# Last 100 lines
docker logs ali-api-dev --tail 100
```

### Emergency Reset
```bash
# Complete cleanup and restart
./docker-compose-up.sh clean
./docker-build.sh
./docker-compose-up.sh
./docker-test.sh
```

---

**🎉 Congratulations!** You now have Ali API running in Docker with full development and production capabilities.
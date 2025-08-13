#!/bin/bash
# Ali API - Docker Run Script
# =============================================================================

set -e  # Exit on any error

echo "🚀 Ali API - Docker Run Script"
echo "==============================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="ali-api"
IMAGE_TAG="latest"
CONTAINER_NAME="ali-api-dev"
PORT="8080"
ENV_FILE=".env.docker"

echo -e "${BLUE}📋 Run Configuration:${NC}"
echo "  Image: ${IMAGE_NAME}:${IMAGE_TAG}"
echo "  Container: ${CONTAINER_NAME}"
echo "  Port: ${PORT}"
echo "  Env File: ${ENV_FILE}"
echo ""

# Check if image exists
if ! docker image inspect "${IMAGE_NAME}:${IMAGE_TAG}" > /dev/null 2>&1; then
    echo -e "${RED}❌ Error: Image ${IMAGE_NAME}:${IMAGE_TAG} not found!${NC}"
    echo "   Run './docker-build.sh' first."
    exit 1
fi

# Check if env file exists
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${YELLOW}⚠️  Warning: $ENV_FILE not found!${NC}"
    echo "   Using default environment variables."
    ENV_FILE_ARG=""
else
    ENV_FILE_ARG="--env-file $ENV_FILE"
fi

# Stop and remove existing container if running
if docker ps -q -f name="$CONTAINER_NAME" | grep -q .; then
    echo -e "${YELLOW}🛑 Stopping existing container...${NC}"
    docker stop "$CONTAINER_NAME" > /dev/null
fi

if docker ps -aq -f name="$CONTAINER_NAME" | grep -q .; then
    echo -e "${YELLOW}🗑️  Removing existing container...${NC}"
    docker rm "$CONTAINER_NAME" > /dev/null
fi

# Create necessary directories
echo -e "${BLUE}📁 Creating directories...${NC}"
mkdir -p logs data

# Run container
echo -e "${BLUE}🏃 Starting container...${NC}"
echo ""

docker run \
    --name "$CONTAINER_NAME" \
    --detach \
    --publish "${PORT}:8080" \
    --volume "$(pwd)/logs:/app/logs" \
    --volume "$(pwd)/data:/app/data" \
    --volume "$(pwd)/firebase-credentials.json:/app/firebase-credentials.json:ro" \
    --volume "$(pwd)/app:/app/app:ro" \
    $ENV_FILE_ARG \
    --restart unless-stopped \
    "${IMAGE_NAME}:${IMAGE_TAG}"

# Wait a moment for container to start
echo "⏳ Waiting for container to start..."
sleep 3

# Check if container is running
if docker ps -q -f name="$CONTAINER_NAME" | grep -q .; then
    echo -e "${GREEN}✅ Container started successfully!${NC}"
    echo ""
    
    # Show container info
    echo -e "${BLUE}📊 Container Information:${NC}"
    docker ps --filter name="$CONTAINER_NAME" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    
    echo ""
    echo -e "${GREEN}🎉 Ali API is now running!${NC}"
    echo ""
    echo -e "${YELLOW}💡 Quick Commands:${NC}"
    echo "   • View logs: docker logs -f $CONTAINER_NAME"
    echo "   • Health check: curl http://localhost:$PORT/health"
    echo "   • Stop: docker stop $CONTAINER_NAME"
    echo "   • API docs: http://localhost:$PORT/docs"
    echo ""
    
    # Optional: Show initial logs
    if [ "$1" = "-l" ] || [ "$1" = "--logs" ]; then
        echo -e "${BLUE}📋 Container Logs (last 20 lines):${NC}"
        docker logs --tail 20 "$CONTAINER_NAME"
        echo ""
    fi
    
    # Optional: Follow logs
    if [ "$1" = "-f" ] || [ "$1" = "--follow" ]; then
        echo -e "${BLUE}📋 Following container logs (Ctrl+C to exit):${NC}"
        docker logs -f "$CONTAINER_NAME"
    fi
    
else
    echo -e "${RED}❌ Container failed to start!${NC}"
    echo ""
    echo -e "${YELLOW}🔍 Container logs:${NC}"
    docker logs "$CONTAINER_NAME" 2>&1 | tail -20
    exit 1
fi
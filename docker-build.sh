#!/bin/bash
# Ali API - Docker Build Script
# =============================================================================

set -e  # Exit on any error

echo "🔨 Ali API - Docker Build Script"
echo "================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="ali-api"
IMAGE_TAG="latest"
DOCKERFILE="Dockerfile"

echo -e "${BLUE}📋 Build Configuration:${NC}"
echo "  Image Name: ${IMAGE_NAME}"
echo "  Image Tag: ${IMAGE_TAG}"
echo "  Dockerfile: ${DOCKERFILE}"
echo ""

# Check if Dockerfile exists
if [ ! -f "$DOCKERFILE" ]; then
    echo -e "${RED}❌ Error: $DOCKERFILE not found!${NC}"
    exit 1
fi

# Check if firebase credentials exist
if [ ! -f "firebase-credentials.json" ]; then
    echo -e "${YELLOW}⚠️  Warning: firebase-credentials.json not found!${NC}"
    echo "   Make sure you have the Firebase credentials file."
    echo ""
fi

# Start build
echo -e "${BLUE}🏗️  Building Docker image...${NC}"
echo ""

# Build with detailed output
docker build \
    --tag "${IMAGE_NAME}:${IMAGE_TAG}" \
    --tag "${IMAGE_NAME}:dev" \
    --build-arg APP_ENV=development \
    --no-cache \
    . 2>&1 | while IFS= read -r line; do
    echo "   $line"
done

# Check if build was successful
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ Build successful!${NC}"
    
    # Show image info
    echo ""
    echo -e "${BLUE}📊 Image Information:${NC}"
    docker image ls "${IMAGE_NAME}:${IMAGE_TAG}" --format "table {{.Repository}}\t{{.Tag}}\t{{.ID}}\t{{.Size}}\t{{.CreatedAt}}"
    
    # Show image layers (if verbose)
    if [ "$1" = "-v" ] || [ "$1" = "--verbose" ]; then
        echo ""
        echo -e "${BLUE}📋 Image Layers:${NC}"
        docker history "${IMAGE_NAME}:${IMAGE_TAG}" --format "table {{.CreatedBy}}\t{{.Size}}\t{{.CreatedAt}}" | head -10
    fi
    
    echo ""
    echo -e "${GREEN}🎉 Build completed successfully!${NC}"
    echo ""
    echo -e "${YELLOW}💡 Next steps:${NC}"
    echo "   • Run with: ./docker-run.sh"
    echo "   • Test with: ./docker-test.sh" 
    echo "   • Use compose: docker-compose up"
    echo ""
else
    echo ""
    echo -e "${RED}❌ Build failed!${NC}"
    echo "   Check the error messages above."
    exit 1
fi
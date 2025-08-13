#!/bin/bash
# Ali API - Docker Compose Script
# =============================================================================

set -e  # Exit on any error

echo "🐳 Ali API - Docker Compose Script"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.yml"
ENV_FILE=".env.docker"

echo -e "${BLUE}📋 Compose Configuration:${NC}"
echo "  Compose File: ${COMPOSE_FILE}"
echo "  Env File: ${ENV_FILE}"
echo ""

# Check if docker-compose.yml exists
if [ ! -f "$COMPOSE_FILE" ]; then
    echo -e "${RED}❌ Error: $COMPOSE_FILE not found!${NC}"
    exit 1
fi

# Check if .env.docker exists
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${YELLOW}⚠️  Warning: $ENV_FILE not found!${NC}"
    echo "   Using default environment variables."
    ENV_ARG=""
else
    ENV_ARG="--env-file $ENV_FILE"
fi

# Parse command line arguments
ACTION=${1:-"up"}
OPTIONS=""

case $ACTION in
    "up"|"start")
        OPTIONS="-d --build"
        echo -e "${BLUE}🚀 Starting services in background...${NC}"
        ;;
    "up-fg"|"foreground")
        OPTIONS="--build"
        echo -e "${BLUE}🚀 Starting services in foreground...${NC}"
        ;;
    "down"|"stop")
        OPTIONS=""
        echo -e "${YELLOW}🛑 Stopping services...${NC}"
        ;;
    "restart")
        echo -e "${YELLOW}🔄 Restarting services...${NC}"
        docker-compose $ENV_ARG down
        sleep 2
        ACTION="up"
        OPTIONS="-d --build"
        ;;
    "logs")
        echo -e "${BLUE}📋 Showing logs...${NC}"
        docker-compose $ENV_ARG logs -f
        exit 0
        ;;
    "status"|"ps")
        echo -e "${BLUE}📊 Service Status:${NC}"
        docker-compose $ENV_ARG ps
        exit 0
        ;;
    "build")
        echo -e "${BLUE}🔨 Building services...${NC}"
        docker-compose $ENV_ARG build --no-cache
        exit 0
        ;;
    "clean")
        echo -e "${YELLOW}🧹 Cleaning up...${NC}"
        docker-compose $ENV_ARG down --volumes --remove-orphans
        docker system prune -f
        echo -e "${GREEN}✅ Cleanup completed!${NC}"
        exit 0
        ;;
    "help"|"-h"|"--help")
        echo -e "${BLUE}💡 Usage:${NC}"
        echo "  $0 [ACTION]"
        echo ""
        echo -e "${BLUE}Available Actions:${NC}"
        echo "  up, start     - Start services in background (default)"
        echo "  up-fg         - Start services in foreground"
        echo "  down, stop    - Stop services"
        echo "  restart       - Restart services"
        echo "  logs          - Show and follow logs"
        echo "  status, ps    - Show service status"
        echo "  build         - Build services"
        echo "  clean         - Stop and cleanup everything"
        echo "  help          - Show this help"
        exit 0
        ;;
    *)
        echo -e "${RED}❌ Unknown action: $ACTION${NC}"
        echo "   Use '$0 help' for available actions."
        exit 1
        ;;
esac

# Create necessary directories
echo -e "${BLUE}📁 Creating directories...${NC}"
mkdir -p logs data

# Execute the action
if [ "$ACTION" = "down" ]; then
    docker-compose $ENV_ARG down $OPTIONS
    echo -e "${GREEN}✅ Services stopped!${NC}"
else
    # Start services
    docker-compose $ENV_ARG $ACTION $OPTIONS
    
    if [ "$ACTION" = "up" ]; then
        # Wait a moment and check status
        echo "⏳ Waiting for services to start..."
        sleep 5
        
        # Check service status
        echo ""
        echo -e "${BLUE}📊 Service Status:${NC}"
        docker-compose $ENV_ARG ps
        
        # Test health if service is running
        if docker-compose $ENV_ARG ps ali-api | grep -q "Up"; then
            echo ""
            echo -e "${BLUE}🏥 Health Check:${NC}"
            
            # Wait a bit more for health check to be ready
            sleep 10
            
            HEALTH_CHECK=$(curl -s http://localhost:8080/health 2>/dev/null || echo "ERROR")
            if echo "$HEALTH_CHECK" | grep -q "status"; then
                OVERALL_STATUS=$(echo $HEALTH_CHECK | jq -r '.status' 2>/dev/null || echo "unknown")
                if [ "$OVERALL_STATUS" = "healthy" ]; then
                    echo -e "${GREEN}✅ Service is healthy!${NC}"
                else
                    echo -e "${YELLOW}⚠️  Service status: $OVERALL_STATUS${NC}"
                fi
            else
                echo -e "${YELLOW}⚠️  Health check not ready yet${NC}"
            fi
        fi
        
        echo ""
        echo -e "${GREEN}🎉 Ali API is now running with Docker Compose!${NC}"
        echo ""
        echo -e "${YELLOW}💡 Useful Commands:${NC}"
        echo "   • View logs: $0 logs"
        echo "   • Check status: $0 status"
        echo "   • Stop: $0 down"
        echo "   • Restart: $0 restart"
        echo ""
        echo -e "${YELLOW}🌐 Access Points:${NC}"
        echo "   • API Root: http://localhost:8080/"
        echo "   • Health Check: http://localhost:8080/health"
        echo "   • API Docs: http://localhost:8080/docs"
        echo "   • ReDoc: http://localhost:8080/redoc"
        echo ""
    fi
fi
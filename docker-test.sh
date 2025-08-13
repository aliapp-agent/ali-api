#!/bin/bash
# Ali API - Docker Test Script
# =============================================================================

set -e  # Exit on any error

echo "🧪 Ali API - Docker Test Script"
echo "==============================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
CONTAINER_NAME="ali-api-dev"
PORT="8080"
BASE_URL="http://localhost:${PORT}"
HEALTH_ENDPOINT="${BASE_URL}/health"
API_DOCS_ENDPOINT="${BASE_URL}/docs"

echo -e "${BLUE}📋 Test Configuration:${NC}"
echo "  Container: ${CONTAINER_NAME}"
echo "  Base URL: ${BASE_URL}"
echo "  Health Endpoint: ${HEALTH_ENDPOINT}"
echo ""

# Check if container is running
if ! docker ps -q -f name="$CONTAINER_NAME" | grep -q .; then
    echo -e "${RED}❌ Error: Container '$CONTAINER_NAME' is not running!${NC}"
    echo "   Run './docker-run.sh' first."
    exit 1
fi

echo -e "${BLUE}🔍 Container Status:${NC}"
docker ps --filter name="$CONTAINER_NAME" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""

# Wait for container to be ready
echo -e "${YELLOW}⏳ Waiting for API to be ready...${NC}"
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -f -s "${HEALTH_ENDPOINT}" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ API is ready!${NC}"
        break
    fi
    
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "   Attempt $RETRY_COUNT/$MAX_RETRIES..."
    sleep 2
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo -e "${RED}❌ API failed to become ready after $MAX_RETRIES attempts${NC}"
    echo ""
    echo -e "${YELLOW}🔍 Container logs (last 20 lines):${NC}"
    docker logs --tail 20 "$CONTAINER_NAME"
    exit 1
fi

echo ""

# Test 1: Root endpoint
echo -e "${PURPLE}🧪 Test 1: Root Endpoint${NC}"
echo "======================================="
ROOT_RESPONSE=$(curl -s "${BASE_URL}/" || echo "ERROR")

if echo "$ROOT_RESPONSE" | grep -q "Ali API"; then
    echo -e "${GREEN}✅ PASSED: Root endpoint responding${NC}"
    echo "   Response: $(echo $ROOT_RESPONSE | jq -r '.name + " v" + .version' 2>/dev/null || echo $ROOT_RESPONSE)"
else
    echo -e "${RED}❌ FAILED: Root endpoint not responding correctly${NC}"
    echo "   Response: $ROOT_RESPONSE"
fi
echo ""

# Test 2: Health check comprehensive
echo -e "${PURPLE}🧪 Test 2: Health Check${NC}"
echo "======================================="
HEALTH_RESPONSE=$(curl -s "${HEALTH_ENDPOINT}" || echo "ERROR")

if echo "$HEALTH_RESPONSE" | grep -q "status"; then
    echo -e "${GREEN}✅ PASSED: Health endpoint responding${NC}"
    
    # Parse health status
    OVERALL_STATUS=$(echo $HEALTH_RESPONSE | jq -r '.status' 2>/dev/null || echo "unknown")
    echo "   Overall Status: $OVERALL_STATUS"
    
    # Parse components
    COMPONENTS=$(echo $HEALTH_RESPONSE | jq -r '.components | keys[]' 2>/dev/null || echo "")
    if [ ! -z "$COMPONENTS" ]; then
        echo "   Components:"
        for component in $COMPONENTS; do
            COMP_STATUS=$(echo $HEALTH_RESPONSE | jq -r ".components[\"$component\"]" 2>/dev/null || echo "unknown")
            if [ "$COMP_STATUS" = "healthy" ]; then
                echo -e "     ${GREEN}🟢${NC} $component: $COMP_STATUS"
            elif [ "$COMP_STATUS" = "degraded" ]; then
                echo -e "     ${YELLOW}🟡${NC} $component: $COMP_STATUS"  
            else
                echo -e "     ${RED}🔴${NC} $component: $COMP_STATUS"
            fi
        done
    fi
else
    echo -e "${RED}❌ FAILED: Health endpoint not responding correctly${NC}"
    echo "   Response: $HEALTH_RESPONSE"
fi
echo ""

# Test 3: Detailed health check
echo -e "${PURPLE}🧪 Test 3: Detailed Health Check${NC}"
echo "======================================="
DETAILED_HEALTH_RESPONSE=$(curl -s "${BASE_URL}/api/v1/health/detailed" || echo "ERROR")

if echo "$DETAILED_HEALTH_RESPONSE" | grep -q "checks"; then
    echo -e "${GREEN}✅ PASSED: Detailed health endpoint responding${NC}"
    
    # Check specific components
    JWT_STATUS=$(echo $DETAILED_HEALTH_RESPONSE | jq -r '.checks.jwt.status' 2>/dev/null || echo "unknown")
    FIREBASE_STATUS=$(echo $DETAILED_HEALTH_RESPONSE | jq -r '.checks.firebase_config.status' 2>/dev/null || echo "unknown")
    
    echo "   🔐 JWT: $JWT_STATUS"
    echo "   🔥 Firebase: $FIREBASE_STATUS"
else
    echo -e "${YELLOW}⚠️  WARNING: Detailed health endpoint not available${NC}"
fi
echo ""

# Test 4: API Documentation
echo -e "${PURPLE}🧪 Test 4: API Documentation${NC}"
echo "======================================="
DOCS_RESPONSE_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${API_DOCS_ENDPOINT}" || echo "ERROR")

if [ "$DOCS_RESPONSE_CODE" = "200" ]; then
    echo -e "${GREEN}✅ PASSED: API documentation accessible${NC}"
    echo "   URL: ${API_DOCS_ENDPOINT}"
else
    echo -e "${YELLOW}⚠️  WARNING: API documentation not accessible (HTTP $DOCS_RESPONSE_CODE)${NC}"
fi
echo ""

# Test 5: Container resource usage
echo -e "${PURPLE}🧪 Test 5: Container Resources${NC}"
echo "======================================="
CONTAINER_STATS=$(docker stats --no-stream --format "table {{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" "$CONTAINER_NAME" 2>/dev/null | tail -n 1)

if [ ! -z "$CONTAINER_STATS" ]; then
    echo -e "${GREEN}✅ PASSED: Container stats available${NC}"
    echo "   Stats: $CONTAINER_STATS"
else
    echo -e "${YELLOW}⚠️  WARNING: Could not get container stats${NC}"
fi
echo ""

# Test 6: Container logs check
echo -e "${PURPLE}🧪 Test 6: Container Logs${NC}"
echo "======================================="
LOG_LINES=$(docker logs "$CONTAINER_NAME" 2>&1 | wc -l)
ERROR_LINES=$(docker logs "$CONTAINER_NAME" 2>&1 | grep -i error | wc -l)

echo -e "${GREEN}✅ PASSED: Log analysis complete${NC}"
echo "   Total log lines: $LOG_LINES"
echo "   Error lines: $ERROR_LINES"

if [ "$ERROR_LINES" -gt 0 ]; then
    echo -e "${YELLOW}⚠️  Recent errors found:${NC}"
    docker logs "$CONTAINER_NAME" 2>&1 | grep -i error | tail -3 | sed 's/^/   /'
fi
echo ""

# Final Summary
echo -e "${BLUE}📊 TEST SUMMARY${NC}"
echo "======================================="
echo -e "${GREEN}🎉 Docker tests completed!${NC}"
echo ""
echo -e "${YELLOW}💡 Useful Commands:${NC}"
echo "   • View logs: docker logs -f $CONTAINER_NAME"
echo "   • Enter container: docker exec -it $CONTAINER_NAME /bin/bash"
echo "   • Stop container: docker stop $CONTAINER_NAME"
echo "   • Restart container: docker restart $CONTAINER_NAME"
echo ""
echo -e "${YELLOW}🌐 Access Points:${NC}"
echo "   • API Root: $BASE_URL/"
echo "   • Health Check: $HEALTH_ENDPOINT"
echo "   • API Docs: $API_DOCS_ENDPOINT"
echo "   • ReDoc: ${BASE_URL}/redoc"
echo ""

# Optional: Open browser
if command -v xdg-open > /dev/null && [ "$1" = "--open" ]; then
    echo -e "${BLUE}🌐 Opening API documentation in browser...${NC}"
    xdg-open "$API_DOCS_ENDPOINT"
elif command -v open > /dev/null && [ "$1" = "--open" ]; then
    echo -e "${BLUE}🌐 Opening API documentation in browser...${NC}"
    open "$API_DOCS_ENDPOINT"
fi
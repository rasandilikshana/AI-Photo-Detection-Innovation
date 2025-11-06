#!/bin/bash

###############################################################################
# A.V.A.R. Quick Start Script
# Automated setup, deployment, and testing
###############################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}"
cat << "EOF"
    ___   _    __  ___ ___
   / _ | | |  / / / _ | _ \
  / __ | | | / /_/ __ |   /
 /_/ |_| |_| \___/_/ |_|_|_\

 AI-Powered Authenticity Verification System
 for Photography Competitions
EOF
echo -e "${NC}"

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}  A.V.A.R. Quick Start${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

###############################################################################
# Step 1: Check Prerequisites
###############################################################################
echo -e "${YELLOW}Step 1: Checking prerequisites...${NC}"

# Check Docker
if command -v docker &> /dev/null; then
    echo -e "${GREEN}✓ Docker installed${NC}"
else
    echo -e "${RED}✗ Docker not found${NC}"
    echo "Please install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check Docker Compose
if command -v docker-compose &> /dev/null; then
    echo -e "${GREEN}✓ Docker Compose installed${NC}"
else
    echo -e "${RED}✗ Docker Compose not found${NC}"
    echo "Please install Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

# Check Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    echo -e "${GREEN}✓ Python $PYTHON_VERSION installed${NC}"
else
    echo -e "${YELLOW}⚠ Python3 not found (optional for local testing)${NC}"
fi

# Check make
if command -v make &> /dev/null; then
    echo -e "${GREEN}✓ Make installed${NC}"
else
    echo -e "${YELLOW}⚠ Make not found (optional, can use docker-compose directly)${NC}"
fi

echo ""

###############################################################################
# Step 2: Setup Environment
###############################################################################
echo -e "${YELLOW}Step 2: Setting up environment...${NC}"

if [ ! -f .env ]; then
    echo -e "${CYAN}Creating .env file from template...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✓ .env file created${NC}"
    echo -e "${YELLOW}⚠ Please edit .env and add your API keys!${NC}"
else
    echo -e "${GREEN}✓ .env file exists${NC}"
fi

echo ""

###############################################################################
# Step 3: Build and Start Services
###############################################################################
echo -e "${YELLOW}Step 3: Building and starting services...${NC}"

echo -e "${CYAN}Building Docker containers...${NC}"
docker-compose build

echo -e "${CYAN}Starting services...${NC}"
docker-compose up -d

echo ""

###############################################################################
# Step 4: Wait for Services
###############################################################################
echo -e "${YELLOW}Step 4: Waiting for services to be ready...${NC}"

MAX_RETRIES=30
RETRY_DELAY=2

# Wait for AI Detection Service
echo -n "  Waiting for AI Detection Service..."
for i in $(seq 1 $MAX_RETRIES); do
    if curl -s http://localhost:8001/health > /dev/null 2>&1; then
        echo -e " ${GREEN}✓${NC}"
        break
    fi
    sleep $RETRY_DELAY
    echo -n "."
    if [ $i -eq $MAX_RETRIES ]; then
        echo -e " ${RED}✗ Failed${NC}"
        echo "Check logs: docker-compose logs ai-detection-service"
        exit 1
    fi
done

# Wait for API Gateway
echo -n "  Waiting for API Gateway..."
for i in $(seq 1 $MAX_RETRIES); do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e " ${GREEN}✓${NC}"
        break
    fi
    sleep $RETRY_DELAY
    echo -n "."
    if [ $i -eq $MAX_RETRIES ]; then
        echo -e " ${RED}✗ Failed${NC}"
        echo "Check logs: docker-compose logs api-gateway"
        exit 1
    fi
done

echo ""

###############################################################################
# Step 5: Run Health Checks
###############################################################################
echo -e "${YELLOW}Step 5: Running health checks...${NC}"

AI_HEALTH=$(curl -s http://localhost:8001/health | python3 -c "import sys, json; print(json.load(sys.stdin)['status'])" 2>/dev/null || echo "error")
GATEWAY_HEALTH=$(curl -s http://localhost:8000/health | python3 -c "import sys, json; print(json.load(sys.stdin)['status'])" 2>/dev/null || echo "error")

if [ "$AI_HEALTH" = "healthy" ]; then
    echo -e "${GREEN}✓ AI Detection Service: healthy${NC}"
else
    echo -e "${RED}✗ AI Detection Service: $AI_HEALTH${NC}"
fi

if [ "$GATEWAY_HEALTH" = "healthy" ]; then
    echo -e "${GREEN}✓ API Gateway: healthy${NC}"
else
    echo -e "${RED}✗ API Gateway: $GATEWAY_HEALTH${NC}"
fi

echo ""

###############################################################################
# Step 6: Install Test Dependencies (Optional)
###############################################################################
echo -e "${YELLOW}Step 6: Install test dependencies? (y/n)${NC}"
read -r INSTALL_TESTS

if [ "$INSTALL_TESTS" = "y" ]; then
    echo -e "${CYAN}Installing test dependencies...${NC}"
    pip3 install -r tests/requirements.txt 2>/dev/null || echo -e "${YELLOW}⚠ Skipped (pip3 not available)${NC}"
fi

echo ""

###############################################################################
# Step 7: Run Quick Smoke Test
###############################################################################
echo -e "${YELLOW}Step 7: Running quick smoke test...${NC}"

# Test basic endpoint
echo -n "  Testing root endpoint..."
ROOT_RESPONSE=$(curl -s http://localhost:8001/ | python3 -c "import sys, json; print(json.load(sys.stdin).get('service', 'error'))" 2>/dev/null || echo "error")

if [ "$ROOT_RESPONSE" = "A.V.A.R. AI Detection Service" ]; then
    echo -e " ${GREEN}✓${NC}"
else
    echo -e " ${RED}✗${NC}"
fi

echo ""

###############################################################################
# Success!
###############################################################################
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}  ✓ A.V.A.R. System is Running!${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo -e "${CYAN}Service URLs:${NC}"
echo -e "  AI Detection API:  http://localhost:8001"
echo -e "  API Documentation: http://localhost:8001/docs"
echo -e "  API Gateway:       http://localhost:8000"
echo -e "  Gateway Docs:      http://localhost:8000/docs"
echo ""
echo -e "${CYAN}Useful Commands:${NC}"
echo -e "  View logs:         docker-compose logs -f"
echo -e "  Run tests:         make test-all"
echo -e "  Quick test:        make test-quick"
echo -e "  Performance test:  make test-performance"
echo -e "  Stop services:     docker-compose down"
echo -e "  Restart:           docker-compose restart"
echo ""
echo -e "${CYAN}Test the API:${NC}"
echo -e "  curl -X POST http://localhost:8001/api/v1/analyze \\"
echo -e "    -F 'jpg_file=@/path/to/your/image.jpg'"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo -e "  1. Edit .env file and add your API keys"
echo -e "  2. Run comprehensive tests: make test-all"
echo -e "  3. Check the documentation: CLAUDE.md and tests/README.md"
echo -e "  4. Start developing!"
echo ""
echo -e "${GREEN}Happy coding! 🚀${NC}"
echo ""

#!/bin/bash

###############################################################################
# A.V.A.R. Local Development Runner
# Run services locally without Docker (for testing/development)
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

 Local Development Mode
EOF
echo -e "${NC}"

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}  Starting A.V.A.R. Services Locally${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python3 not found${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Python3 available${NC}"

# Create virtual environment for AI Detection Service
echo -e "${YELLOW}Setting up AI Detection Service...${NC}"
cd src/backend/ai-detection-service

if [ ! -d "venv" ]; then
    echo -e "${CYAN}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

source venv/bin/activate

echo -e "${CYAN}Installing dependencies...${NC}"
pip install --quiet fastapi uvicorn pydantic pillow numpy opencv-python pywavelets scipy scikit-image aiofiles python-multipart loguru httpx aiohttp imagehash rawpy 2>&1 | grep -v "Requirement already satisfied" || true

echo -e "${GREEN}✓ AI Detection Service ready${NC}"

# Start AI Detection Service in background
echo -e "${CYAN}Starting AI Detection Service on port 8001...${NC}"
uvicorn app.main:app --host 0.0.0.0 --port 8001 > /tmp/avar-ai-detection.log 2>&1 &
AI_PID=$!
echo $AI_PID > /tmp/avar-ai-detection.pid

sleep 3

# Check if service started
if ps -p $AI_PID > /dev/null; then
    echo -e "${GREEN}✓ AI Detection Service started (PID: $AI_PID)${NC}"
else
    echo -e "${RED}✗ AI Detection Service failed to start${NC}"
    echo "Check logs: tail -f /tmp/avar-ai-detection.log"
    exit 1
fi

cd ../../..

# Start API Gateway
echo -e "${YELLOW}Setting up API Gateway...${NC}"
cd src/backend/api-gateway

if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate

echo -e "${CYAN}Installing dependencies...${NC}"
pip install --quiet fastapi uvicorn pydantic httpx aiohttp python-dotenv loguru 2>&1 | grep -v "Requirement already satisfied" || true

echo -e "${GREEN}✓ API Gateway ready${NC}"

# Start API Gateway in background
echo -e "${CYAN}Starting API Gateway on port 8000...${NC}"
uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/avar-gateway.log 2>&1 &
GATEWAY_PID=$!
echo $GATEWAY_PID > /tmp/avar-gateway.pid

sleep 3

if ps -p $GATEWAY_PID > /dev/null; then
    echo -e "${GREEN}✓ API Gateway started (PID: $GATEWAY_PID)${NC}"
else
    echo -e "${RED}✗ API Gateway failed to start${NC}"
    echo "Check logs: tail -f /tmp/avar-gateway.log"
    kill $AI_PID 2>/dev/null || true
    exit 1
fi

cd ../../..

echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}  ✓ A.V.A.R. Services Running!${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo -e "${CYAN}Service URLs:${NC}"
echo -e "  AI Detection API:  http://localhost:8001"
echo -e "  API Documentation: http://localhost:8001/docs"
echo -e "  API Gateway:       http://localhost:8000"
echo -e "  Gateway Docs:      http://localhost:8000/docs"
echo ""
echo -e "${CYAN}Process IDs:${NC}"
echo -e "  AI Detection: $AI_PID"
echo -e "  API Gateway:  $GATEWAY_PID"
echo ""
echo -e "${CYAN}Logs:${NC}"
echo -e "  AI Detection: tail -f /tmp/avar-ai-detection.log"
echo -e "  API Gateway:  tail -f /tmp/avar-gateway.log"
echo ""
echo -e "${CYAN}Test the API:${NC}"
echo -e "  curl http://localhost:8001/health"
echo ""
echo -e "${YELLOW}To stop services:${NC}"
echo -e "  ./stop_local.sh"
echo -e "  Or: kill $AI_PID $GATEWAY_PID"
echo ""
echo -e "${GREEN}Services are running in the background!${NC}"
echo ""

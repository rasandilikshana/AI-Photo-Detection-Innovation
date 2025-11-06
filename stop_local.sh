#!/bin/bash

###############################################################################
# Stop locally running A.V.A.R. services
###############################################################################

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Stopping A.V.A.R. services...${NC}"

# Stop AI Detection Service
if [ -f /tmp/avar-ai-detection.pid ]; then
    AI_PID=$(cat /tmp/avar-ai-detection.pid)
    if ps -p $AI_PID > /dev/null 2>&1; then
        kill $AI_PID
        echo -e "${GREEN}✓ AI Detection Service stopped (PID: $AI_PID)${NC}"
    else
        echo -e "${YELLOW}AI Detection Service not running${NC}"
    fi
    rm /tmp/avar-ai-detection.pid
fi

# Stop API Gateway
if [ -f /tmp/avar-gateway.pid ]; then
    GATEWAY_PID=$(cat /tmp/avar-gateway.pid)
    if ps -p $GATEWAY_PID > /dev/null 2>&1; then
        kill $GATEWAY_PID
        echo -e "${GREEN}✓ API Gateway stopped (PID: $GATEWAY_PID)${NC}"
    else
        echo -e "${YELLOW}API Gateway not running${NC}"
    fi
    rm /tmp/avar-gateway.pid
fi

# Also kill any uvicorn processes on these ports as fallback
pkill -f "uvicorn app.main:app --host 0.0.0.0 --port 8001" 2>/dev/null
pkill -f "uvicorn app.main:app --host 0.0.0.0 --port 8000" 2>/dev/null

echo -e "${GREEN}All services stopped${NC}"

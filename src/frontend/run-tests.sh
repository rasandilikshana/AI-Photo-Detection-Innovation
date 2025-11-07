#!/bin/bash

# A.V.A.R. Frontend E2E Test Runner
# This script automates the testing process

set -e

echo "======================================"
echo "A.V.A.R. Frontend E2E Test Runner"
echo "======================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
BROWSER="chromium"
HEADED=false
UI_MODE=false
REPORT=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --browser)
            BROWSER="$2"
            shift 2
            ;;
        --headed)
            HEADED=true
            shift
            ;;
        --ui)
            UI_MODE=true
            shift
            ;;
        --report)
            REPORT=true
            shift
            ;;
        --help)
            echo "Usage: ./run-tests.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --browser <name>    Run tests in specific browser (chromium, firefox, webkit)"
            echo "  --headed            Run tests in headed mode (visible browser)"
            echo "  --ui                Run tests in UI mode (interactive)"
            echo "  --report            Show test report after completion"
            echo "  --help              Show this help message"
            echo ""
            echo "Examples:"
            echo "  ./run-tests.sh                           # Run all tests in headless chromium"
            echo "  ./run-tests.sh --browser firefox         # Run in Firefox"
            echo "  ./run-tests.sh --headed                  # Run with visible browser"
            echo "  ./run-tests.sh --ui                      # Run in interactive UI mode"
            echo "  ./run-tests.sh --report                  # Show report after tests"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo -e "${RED}Error: Node.js is not installed${NC}"
    echo "Please install Node.js from https://nodejs.org/"
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo -e "${RED}Error: npm is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Node.js version: $(node --version)"
echo -e "${GREEN}✓${NC} npm version: $(npm --version)"
echo ""

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Installing dependencies...${NC}"
    npm install
    echo -e "${GREEN}✓${NC} Dependencies installed"
    echo ""
fi

# Install Playwright browsers if needed
if [ ! -d "node_modules/@playwright" ]; then
    echo -e "${YELLOW}Installing Playwright browsers...${NC}"
    npx playwright install
    echo -e "${GREEN}✓${NC} Playwright browsers installed"
    echo ""
fi

# Run tests based on options
echo -e "${YELLOW}Running E2E tests...${NC}"
echo ""

if [ "$UI_MODE" = true ]; then
    echo "Starting UI mode..."
    npm run test:e2e:ui
elif [ "$HEADED" = true ]; then
    echo "Running in headed mode (browser: $BROWSER)..."
    npx playwright test --project=$BROWSER --headed
else
    echo "Running in headless mode (browser: $BROWSER)..."
    npx playwright test --project=$BROWSER
fi

# Check test exit code
TEST_EXIT_CODE=$?

echo ""
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
else
    echo -e "${RED}✗ Some tests failed${NC}"
fi

# Show report if requested
if [ "$REPORT" = true ]; then
    echo ""
    echo -e "${YELLOW}Opening test report...${NC}"
    npm run test:e2e:report
fi

exit $TEST_EXIT_CODE

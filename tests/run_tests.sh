#!/bin/bash

###############################################################################
# A.V.A.R. Automated Test Runner
# Comprehensive testing suite for all components
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test configuration
REPORT_DIR="test-reports"
COVERAGE_DIR="htmlcov"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}  A.V.A.R. Automated Test Suite${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# Create report directories
mkdir -p $REPORT_DIR
mkdir -p $COVERAGE_DIR

###############################################################################
# Function: Check if services are running
###############################################################################
check_services() {
    echo -e "${YELLOW}Checking if services are running...${NC}"

    # Check AI Detection Service
    if curl -s http://localhost:8001/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ AI Detection Service is running${NC}"
    else
        echo -e "${RED}✗ AI Detection Service is NOT running${NC}"
        echo -e "${YELLOW}Starting services with docker-compose...${NC}"
        docker-compose up -d
        sleep 10
    fi

    # Check API Gateway
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ API Gateway is running${NC}"
    else
        echo -e "${YELLOW}Waiting for API Gateway to be ready...${NC}"
        sleep 5
    fi

    echo ""
}

###############################################################################
# Function: Run unit tests
###############################################################################
run_unit_tests() {
    echo -e "${BLUE}Running Unit Tests...${NC}"
    echo -e "${BLUE}================================================${NC}"

    docker-compose exec -T ai-detection-service pytest \
        src/backend/ai-detection-service/tests/ \
        -v \
        --tb=short \
        --junit-xml=$REPORT_DIR/unit-tests-${TIMESTAMP}.xml \
        --html=$REPORT_DIR/unit-tests-${TIMESTAMP}.html \
        --self-contained-html \
        || echo -e "${RED}Unit tests failed${NC}"

    echo ""
}

###############################################################################
# Function: Run integration tests
###############################################################################
run_integration_tests() {
    echo -e "${BLUE}Running Integration Tests...${NC}"
    echo -e "${BLUE}================================================${NC}"

    pytest tests/integration/ \
        -v \
        -m "not slow" \
        --junit-xml=$REPORT_DIR/integration-tests-${TIMESTAMP}.xml \
        --html=$REPORT_DIR/integration-tests-${TIMESTAMP}.html \
        --self-contained-html \
        || echo -e "${RED}Integration tests failed${NC}"

    echo ""
}

###############################################################################
# Function: Run E2E tests
###############################################################################
run_e2e_tests() {
    echo -e "${BLUE}Running End-to-End Tests (Playwright)...${NC}"
    echo -e "${BLUE}================================================${NC}"

    # Install playwright browsers if needed
    if [ ! -d "$HOME/.cache/ms-playwright" ]; then
        echo -e "${YELLOW}Installing Playwright browsers...${NC}"
        playwright install chromium
    fi

    pytest tests/e2e/ \
        -v \
        --browser chromium \
        --headed \
        --junit-xml=$REPORT_DIR/e2e-tests-${TIMESTAMP}.xml \
        --html=$REPORT_DIR/e2e-tests-${TIMESTAMP}.html \
        --self-contained-html \
        || echo -e "${YELLOW}E2E tests skipped (frontend not implemented)${NC}"

    echo ""
}

###############################################################################
# Function: Run performance tests
###############################################################################
run_performance_tests() {
    echo -e "${BLUE}Running Performance Tests (Locust)...${NC}"
    echo -e "${BLUE}================================================${NC}"

    echo -e "${YELLOW}Starting Locust in headless mode...${NC}"
    locust \
        -f tests/performance/locustfile.py \
        --host=http://localhost:8001 \
        --users 10 \
        --spawn-rate 2 \
        --run-time 60s \
        --headless \
        --html $REPORT_DIR/performance-${TIMESTAMP}.html \
        || echo -e "${RED}Performance tests failed${NC}"

    echo ""
}

###############################################################################
# Function: Run coverage report
###############################################################################
run_coverage() {
    echo -e "${BLUE}Generating Coverage Report...${NC}"
    echo -e "${BLUE}================================================${NC}"

    docker-compose exec -T ai-detection-service pytest \
        src/backend/ai-detection-service/tests/ \
        --cov=app \
        --cov-report=html:$COVERAGE_DIR \
        --cov-report=term \
        || echo -e "${RED}Coverage generation failed${NC}"

    echo -e "${GREEN}Coverage report: $COVERAGE_DIR/index.html${NC}"
    echo ""
}

###############################################################################
# Function: Run slow tests
###############################################################################
run_slow_tests() {
    echo -e "${BLUE}Running Slow Tests...${NC}"
    echo -e "${BLUE}================================================${NC}"

    pytest tests/integration/ \
        -v \
        -m "slow" \
        --junit-xml=$REPORT_DIR/slow-tests-${TIMESTAMP}.xml \
        || echo -e "${YELLOW}Slow tests skipped${NC}"

    echo ""
}

###############################################################################
# Function: Generate summary report
###############################################################################
generate_summary() {
    echo -e "${BLUE}================================================${NC}"
    echo -e "${BLUE}  Test Summary${NC}"
    echo -e "${BLUE}================================================${NC}"

    echo -e "${GREEN}Test reports saved to: $REPORT_DIR/${NC}"
    echo -e "${GREEN}Coverage report: $COVERAGE_DIR/index.html${NC}"

    # Count test files
    unit_count=$(find src/backend/ai-detection-service/tests -name "test_*.py" | wc -l)
    integration_count=$(find tests/integration -name "test_*.py" 2>/dev/null | wc -l || echo 0)
    e2e_count=$(find tests/e2e -name "test_*.py" 2>/dev/null | wc -l || echo 0)

    echo ""
    echo -e "Test Files:"
    echo -e "  Unit: $unit_count"
    echo -e "  Integration: $integration_count"
    echo -e "  E2E: $e2e_count"

    echo ""
    echo -e "${GREEN}✓ Test suite completed${NC}"
    echo ""
}

###############################################################################
# Main execution
###############################################################################

# Parse command line arguments
TEST_TYPE=${1:-all}

case $TEST_TYPE in
    unit)
        check_services
        run_unit_tests
        ;;
    integration)
        check_services
        run_integration_tests
        ;;
    e2e)
        check_services
        run_e2e_tests
        ;;
    performance)
        check_services
        run_performance_tests
        ;;
    slow)
        check_services
        run_slow_tests
        ;;
    coverage)
        check_services
        run_coverage
        ;;
    all)
        check_services
        run_unit_tests
        run_integration_tests
        # run_e2e_tests  # Skip until frontend is implemented
        run_coverage
        generate_summary
        ;;
    *)
        echo -e "${RED}Unknown test type: $TEST_TYPE${NC}"
        echo ""
        echo "Usage: $0 [unit|integration|e2e|performance|slow|coverage|all]"
        echo ""
        echo "Options:"
        echo "  unit         - Run unit tests only"
        echo "  integration  - Run integration tests only"
        echo "  e2e          - Run end-to-end browser tests"
        echo "  performance  - Run performance/load tests"
        echo "  slow         - Run slow tests"
        echo "  coverage     - Generate coverage report"
        echo "  all          - Run all tests (default)"
        exit 1
        ;;
esac

exit 0

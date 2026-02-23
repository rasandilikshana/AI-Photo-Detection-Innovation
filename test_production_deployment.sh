#!/bin/bash
# E2E Test for V2.0.0 Production Deployment
# Tests the production server at avar.studio

# Don't exit on error - continue all tests
# set -e

SERVER="https://avar.studio"
IP_SERVER="http://165.245.178.225"
API_BASE="$SERVER/api/v1"

echo "=========================================="
echo "V2.0.0 Production E2E Test"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

pass_count=0
fail_count=0

# Test function
test_endpoint() {
    local name=$1
    local url=$2
    local expected_status=$3
    local description=$4

    echo -n "Testing: $name... "
    response=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>&1)

    if [ "$response" = "$expected_status" ]; then
        echo -e "${GREEN}✅ PASS${NC} (HTTP $response)"
        ((pass_count++))
        return 0
    else
        echo -e "${RED}❌ FAIL${NC} (Expected $expected_status, got $response)"
        ((fail_count++))
        return 1
    fi
}

# Test 1: Frontend Accessibility
echo "=== Frontend Tests ==="
test_endpoint "Frontend Homepage" "$SERVER" "200" "Main page loads"
test_endpoint "Frontend via IP" "$IP_SERVER" "200" "IP access works"
echo ""

# Test 2: API Health
echo "=== API Health Tests ==="
test_endpoint "Competition Service Health" "$SERVER/health" "200" "Competition service is healthy"
echo ""

# Test 3: Core API Endpoints
echo "=== Core API Tests ==="
test_endpoint "API Documentation" "$SERVER/docs" "200" "API docs accessible"
test_endpoint "Get Competitions" "$API_BASE/competitions" "200" "Competitions endpoint"
echo ""

# Test 4: V2.0 Endpoints
echo "=== V2.0 Feature Tests ==="
test_endpoint "Camera Profiles" "$API_BASE/cameras/profiles" "200" "Camera reputation endpoint"
test_endpoint "Judge Analytics (Auth Required)" "$API_BASE/judges-analytics/profile/1/1" "401" "Judge analytics endpoint exists"
echo ""

# Test 5: Authentication
echo "=== Authentication Tests ==="
echo -n "Testing: Login Endpoint... "
response=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$API_BASE/auth/login" -H "Content-Type: application/json" 2>&1)
if [ "$response" = "422" ]; then
    echo -e "${GREEN}✅ PASS${NC} (HTTP $response - validation error as expected)"
    ((pass_count++))
else
    echo -e "${YELLOW}⚠️  WARNING${NC} (Got $response, expected 422)"
fi
echo ""

# Test 6: Get actual data
echo "=== Data Verification ==="
echo -n "Fetching competitions... "
competitions=$(curl -s "$API_BASE/competitions" 2>&1)
comp_count=$(echo "$competitions" | grep -o '"id"' | wc -l)
if [ "$comp_count" -gt 0 ]; then
    echo -e "${GREEN}✅ PASS${NC} (Found $comp_count competitions)"
    ((pass_count++))
else
    echo -e "${RED}❌ FAIL${NC} (No competitions found)"
    ((fail_count++))
fi

echo -n "Fetching camera profiles... "
camera_profiles=$(curl -s "$API_BASE/cameras/profiles" 2>&1)
if echo "$camera_profiles" | grep -q "^\["; then
    echo -e "${GREEN}✅ PASS${NC} (Endpoint returns array)"
    ((pass_count++))
else
    echo -e "${RED}❌ FAIL${NC} (Invalid response)"
    ((fail_count++))
fi
echo ""

# Test 7: SSL/Security
echo "=== Security Tests ==="
echo -n "Testing HTTPS... "
ssl_output=$(curl -sI "$SERVER" 2>&1 | head -1)
if echo "$ssl_output" | grep -q "200"; then
    echo -e "${GREEN}✅ PASS${NC} (HTTPS working)"
    ((pass_count++))
else
    echo -e "${YELLOW}⚠️  WARNING${NC} (Check SSL configuration)"
fi
echo ""

# Summary
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo -e "Passed: ${GREEN}$pass_count${NC}"
echo -e "Failed: ${RED}$fail_count${NC}"
echo "Total: $((pass_count + fail_count))"
echo ""

if [ $fail_count -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
    echo ""
    echo "🎉 V2.0.0 deployment is successful!"
    exit 0
else
    echo -e "${RED}❌ Some tests failed${NC}"
    echo ""
    echo "Please check the failed endpoints above."
    exit 1
fi

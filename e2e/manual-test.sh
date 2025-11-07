#!/bin/bash

echo "=== A.V.A.R. Manual Testing Script ==="
echo ""

# Test 1: Check frontend is accessible
echo "Test 1: Frontend accessibility"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000)
if [ "$STATUS" = "200" ]; then
    echo "✅ PASS: Frontend is accessible (HTTP $STATUS)"
else
    echo "❌ FAIL: Frontend not accessible (HTTP $STATUS)"
fi
echo ""

# Test 2: Check API is accessible
echo "Test 2: API accessibility"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/health)
if [ "$STATUS" = "200" ]; then
    echo "✅ PASS: API is accessible (HTTP $STATUS)"
else
    echo "❌ FAIL: API not accessible (HTTP $STATUS)"
fi
echo ""

# Test 3: Check competitions endpoint
echo "Test 3: Competitions API endpoint"
RESPONSE=$(curl -s http://localhost:8080/api/v1/competitions)
if [ -n "$RESPONSE" ]; then
    echo "✅ PASS: Competitions endpoint responds"
    echo "   Response: $RESPONSE"
else
    echo "❌ FAIL: Competitions endpoint not responding"
fi
echo ""

# Test 4: Test registration endpoint
echo "Test 4: User registration API"
TIMESTAMP=$(date +%s)
REG_RESPONSE=$(curl -s -X POST http://localhost:8080/api/v1/auth/register \
    -H "Content-Type: application/json" \
    -d "{
        \"email\": \"test${TIMESTAMP}@example.com\",
        \"username\": \"testuser${TIMESTAMP}\",
        \"password\": \"TestPassword123!\"
    }")

if echo "$REG_RESPONSE" | grep -q "email\|username\|id"; then
    echo "✅ PASS: Registration endpoint works"
    echo "   Response: $REG_RESPONSE"
else
    echo "❌ FAIL: Registration failed"
    echo "   Response: $REG_RESPONSE"
fi
echo ""

# Test 5: Test login endpoint
echo "Test 5: User login API"
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:8080/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d "{
        \"email\": \"test${TIMESTAMP}@example.com\",
        \"password\": \"TestPassword123!\"
    }")

if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
    echo "✅ PASS: Login endpoint works"
    ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
    echo "   Got access token: ${ACCESS_TOKEN:0:20}..."
else
    echo "❌ FAIL: Login failed"
    echo "   Response: $LOGIN_RESPONSE"
fi
echo ""

# Test 6: Frontend routes
echo "Test 6: Frontend routes"
ROUTES=("/" "/login" "/register" "/competitions")
for route in "${ROUTES[@]}"; do
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:3000${route}")
    if [ "$STATUS" = "200" ]; then
        echo "✅ PASS: Route $route is accessible"
    else
        echo "❌ FAIL: Route $route returned HTTP $STATUS"
    fi
done
echo ""

# Test 7: Check frontend JavaScript loads
echo "Test 7: Frontend JavaScript"
HTML=$(curl -s http://localhost:3000)
if echo "$HTML" | grep -q "assets.*\.js"; then
    echo "✅ PASS: Frontend includes JavaScript files"
else
    echo "❌ FAIL: No JavaScript files found in HTML"
fi
echo ""

# Test 8: Check frontend CSS loads
echo "Test 8: Frontend CSS"
if echo "$HTML" | grep -q "assets.*\.css"; then
    echo "✅ PASS: Frontend includes CSS files"
else
    echo "❌ FAIL: No CSS files found in HTML"
fi
echo ""

echo "=== Testing Complete ==="

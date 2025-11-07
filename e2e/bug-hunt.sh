#!/bin/bash

echo "=== A.V.A.R. Bug Hunting Script ==="
echo ""

BUGS_FOUND=0

# Bug Test 1: Test for SQL injection vulnerabilities
echo "Bug Test 1: SQL Injection Protection"
MALICIOUS_INPUT="test' OR '1'='1"
RESPONSE=$(curl -s -X POST http://localhost:8080/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d "{\"email\": \"$MALICIOUS_INPUT\", \"password\": \"test\"}")

if echo "$RESPONSE" | grep -q "detail.*Invalid"; then
    echo "✅ PASS: SQL injection protected"
else
    echo "⚠️  WARNING: Unexpected response to SQL injection test"
    BUGS_FOUND=$((BUGS_FOUND + 1))
fi
echo ""

# Bug Test 2: Test for XSS vulnerabilities
echo "Bug Test 2: XSS Protection"
TIMESTAMP=$(date +%s)
XSS_INPUT="<script>alert('xss')</script>"
RESPONSE=$(curl -s -X POST http://localhost:8080/api/v1/auth/register \
    -H "Content-Type: application/json" \
    -d "{
        \"email\": \"xss${TIMESTAMP}@test.com\",
        \"username\": \"$XSS_INPUT\",
        \"password\": \"test123\"
    }")

if echo "$RESPONSE" | grep -q "<script>"; then
    echo "❌ BUG FOUND: XSS not escaped in response"
    BUGS_FOUND=$((BUGS_FOUND + 1))
else
    echo "✅ PASS: XSS protection working"
fi
echo ""

# Bug Test 3: Test password validation
echo "Bug Test 3: Password Validation"
RESPONSE=$(curl -s -X POST http://localhost:8080/api/v1/auth/register \
    -H "Content-Type: application/json" \
    -d "{
        \"email\": \"weak${TIMESTAMP}@test.com\",
        \"username\": \"weakuser\",
        \"password\": \"123\"
    }")

if echo "$RESPONSE" | grep -q "id"; then
    echo "⚠️  BUG FOUND: Weak passwords accepted"
    BUGS_FOUND=$((BUGS_FOUND + 1))
else
    echo "✅ PASS: Weak passwords rejected"
fi
echo ""

# Bug Test 4: Test duplicate registration
echo "Bug Test 4: Duplicate Registration Prevention"
EMAIL="duplicate${TIMESTAMP}@test.com"
curl -s -X POST http://localhost:8080/api/v1/auth/register \
    -H "Content-Type: application/json" \
    -d "{\"email\": \"$EMAIL\", \"username\": \"user1\", \"password\": \"Test123!\"}" > /dev/null

RESPONSE=$(curl -s -X POST http://localhost:8080/api/v1/auth/register \
    -H "Content-Type: application/json" \
    -d "{\"email\": \"$EMAIL\", \"username\": \"user2\", \"password\": \"Test123!\"}")

if echo "$RESPONSE" | grep -q "detail\|error\|already"; then
    echo "✅ PASS: Duplicate emails rejected"
else
    echo "❌ BUG FOUND: Duplicate registrations allowed"
    BUGS_FOUND=$((BUGS_FOUND + 1))
fi
echo ""

# Bug Test 5: Test unauthorized access
echo "Bug Test 5: Unauthorized Access Protection"
RESPONSE=$(curl -s http://localhost:8080/api/v1/submissions)
STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/api/v1/submissions)

if [ "$STATUS" = "401" ] || [ "$STATUS" = "403" ]; then
    echo "✅ PASS: Protected endpoints require authentication"
else
    echo "⚠️  WARNING: Protected endpoint returned HTTP $STATUS"
    if [ "$STATUS" = "200" ]; then
        echo "❌ BUG FOUND: Submissions accessible without authentication"
        BUGS_FOUND=$((BUGS_FOUND + 1))
    fi
fi
echo ""

# Bug Test 6: Test invalid JSON handling
echo "Bug Test 6: Invalid JSON Handling"
RESPONSE=$(curl -s -X POST http://localhost:8080/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d "invalid json{")
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8080/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d "invalid json{")

if [ "$STATUS" = "422" ] || [ "$STATUS" = "400" ]; then
    echo "✅ PASS: Invalid JSON handled properly (HTTP $STATUS)"
else
    echo "⚠️  WARNING: Invalid JSON returned HTTP $STATUS"
fi
echo ""

# Bug Test 7: Test CORS headers
echo "Bug Test 7: CORS Headers"
CORS_HEADERS=$(curl -s -I -X OPTIONS http://localhost:8080/api/v1/competitions | grep -i "access-control")

if [ -n "$CORS_HEADERS" ]; then
    echo "✅ PASS: CORS headers present"
    echo "   $CORS_HEADERS"
else
    echo "⚠️  WARNING: No CORS headers found"
fi
echo ""

# Bug Test 8: Test rate limiting (if implemented)
echo "Bug Test 8: Rate Limiting Check"
echo "Making 10 rapid requests..."
for i in {1..10}; do
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/health)
    if [ "$STATUS" = "429" ]; then
        echo "✅ PASS: Rate limiting active"
        break
    fi
done
echo "Note: Rate limiting may not be implemented yet"
echo ""

# Bug Test 9: Test empty/null inputs
echo "Bug Test 9: Empty Input Handling"
RESPONSE=$(curl -s -X POST http://localhost:8080/api/v1/auth/register \
    -H "Content-Type: application/json" \
    -d "{\"email\": \"\", \"username\": \"\", \"password\": \"\"}")

if echo "$RESPONSE" | grep -q "detail\|error\|required"; then
    echo "✅ PASS: Empty inputs rejected"
else
    echo "⚠️  WARNING: Empty inputs may be accepted"
fi
echo ""

# Bug Test 10: Test very long inputs
echo "Bug Test 10: Input Length Validation"
LONG_STRING=$(python3 -c "print('A' * 10000)")
RESPONSE=$(curl -s -X POST http://localhost:8080/api/v1/auth/register \
    -H "Content-Type: application/json" \
    -d "{\"email\": \"test@test.com\", \"username\": \"$LONG_STRING\", \"password\": \"test\"}")

if echo "$RESPONSE" | grep -q "detail\|error\|too long\|invalid"; then
    echo "✅ PASS: Long inputs validated"
else
    echo "⚠️  WARNING: Very long inputs accepted"
fi
echo ""

# Bug Test 11: Check for information disclosure
echo "Bug Test 11: Information Disclosure Check"
RESPONSE=$(curl -s http://localhost:8080/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d "{\"email\": \"nonexistent@test.com\", \"password\": \"wrong\"}")

if echo "$RESPONSE" | grep -qi "user not found\|email not found"; then
    echo "⚠️  SECURITY ISSUE: Error messages reveal if user exists"
    BUGS_FOUND=$((BUGS_FOUND + 1))
else
    echo "✅ PASS: Generic error messages used"
fi
echo ""

# Bug Test 12: Test special characters
echo "Bug Test 12: Special Character Handling"
SPECIAL_CHARS="!@#$%^&*()_+-=[]{}|;':,.<>?"
RESPONSE=$(curl -s -X POST http://localhost:8080/api/v1/auth/register \
    -H "Content-Type: application/json" \
    -d "{
        \"email\": \"special${TIMESTAMP}@test.com\",
        \"username\": \"user_$TIMESTAMP\",
        \"password\": \"$SPECIAL_CHARS\"
    }")

if echo "$RESPONSE" | grep -q "id\|error\|detail"; then
    echo "✅ PASS: Special characters handled"
else
    echo "⚠️  WARNING: Unexpected response to special characters"
fi
echo ""

echo "=== Bug Hunt Summary ==="
echo "Total bugs/issues found: $BUGS_FOUND"
echo ""

if [ $BUGS_FOUND -eq 0 ]; then
    echo "🎉 Great! No critical bugs found in basic testing."
else
    echo "⚠️  Please review the issues found above."
fi

#!/bin/bash

# Quick Test Script - Run this for fast testing during development

echo "⚡ Quick Authentication Test"
echo "=========================="

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

print_test() {
    echo -e "${BLUE}🧪${NC} $1"
}

print_pass() {
    echo -e "${GREEN}✅${NC} $1"
}

print_fail() {
    echo -e "${RED}❌${NC} $1"
}

# Quick connectivity test
print_test "Testing API connectivity..."
if curl -s http://localhost:8000/api/auth/verify-token/ > /dev/null; then
    print_pass "API responding"
else
    print_fail "API not responding - is the server running?"
    echo "Start with: docker-compose -f docker-compose.local.yml up -d"
    exit 1
fi

# Test new endpoints
print_test "Testing PIN endpoints..."
PIN_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/auth/pin/status/)
if [ "$PIN_STATUS" = "401" ]; then
    print_pass "PIN endpoints working"
else
    print_fail "PIN endpoints issue (got $PIN_STATUS)"
fi

# Test database
print_test "Testing database..."
if docker-compose -f docker-compose.local.yml exec -T web python manage.py check > /dev/null 2>&1; then
    print_pass "Database OK"
else
    print_fail "Database issues"
fi

echo ""
echo "⚡ Quick test completed! Ready to code 🚀"
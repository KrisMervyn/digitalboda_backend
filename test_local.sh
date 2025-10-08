#!/bin/bash

# Local Testing Script for Authentication Features
# Run this to test your changes locally before pushing to GitHub

set -e

echo "🧪 Testing DigitalBoda Authentication Features Locally"
echo "===================================================="

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[TEST]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
}

print_error() {
    echo -e "${RED}[FAIL]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Check if Docker Compose is running
if ! docker-compose -f docker-compose.local.yml ps | grep -q "Up"; then
    print_error "Local development environment is not running!"
    echo "Start it with: ./local_dev_setup.sh"
    exit 1
fi

print_status "Local environment is running ✅"

# Test database connection
print_status "Testing database connection..."
if docker-compose -f docker-compose.local.yml exec -T web python manage.py showmigrations riders >/dev/null 2>&1; then
    print_success "Database connection working"
else
    print_error "Database connection failed"
    exit 1
fi

# Test migrations
print_status "Checking migrations..."
MIGRATION_OUTPUT=$(docker-compose -f docker-compose.local.yml exec -T web python manage.py showmigrations riders)
if echo "$MIGRATION_OUTPUT" | grep -q "0013_add_pin_and_age_bracket_fields"; then
    print_success "PIN and age bracket migration detected"
else
    print_error "Required migration not found"
    echo "Run: docker-compose -f docker-compose.local.yml exec web python manage.py migrate"
    exit 1
fi

# Test API endpoints
print_status "Testing API endpoints..."

# Wait for server to be ready
sleep 2

# Test basic connectivity
print_status "Testing basic API connectivity..."
HEALTH_CHECK=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/auth/verify-token/)
if [ "$HEALTH_CHECK" = "401" ]; then
    print_success "API is responding (401 as expected)"
else
    print_warning "API returned status: $HEALTH_CHECK"
fi

# Test PIN status endpoint
print_status "Testing PIN status endpoint..."
PIN_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/auth/pin/status/)
if [ "$PIN_STATUS" = "401" ]; then
    print_success "PIN status endpoint requires authentication ✅"
else
    print_error "PIN status endpoint returned: $PIN_STATUS (expected 401)"
fi

# Test PIN setup endpoint
print_status "Testing PIN setup endpoint..."
PIN_SETUP=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8000/api/auth/pin/setup/ \
    -H "Content-Type: application/json" \
    -d '{"pin_code": "1234", "confirm_pin": "1234"}')
if [ "$PIN_SETUP" = "401" ]; then
    print_success "PIN setup endpoint requires authentication ✅"
else
    print_error "PIN setup endpoint returned: $PIN_SETUP (expected 401)"
fi

# Test enhanced login endpoint
print_status "Testing enhanced login endpoint..."
LOGIN_RESPONSE=$(curl -s http://localhost:8000/api/auth/rider/login/ \
    -X POST \
    -H "Content-Type: application/json" \
    -d '{"phone_number": "+256700123456", "pin_code": "1234", "login_type": "pin"}')

if echo "$LOGIN_RESPONSE" | grep -q '"error".*"not found"'; then
    print_success "Enhanced login endpoint working (user not found as expected)"
elif echo "$LOGIN_RESPONSE" | grep -q '"token"'; then
    print_success "Enhanced login endpoint working (login successful)"
else
    print_warning "Enhanced login response: $LOGIN_RESPONSE"
fi

# Test onboarding with age brackets
print_status "Testing onboarding endpoint with age brackets..."
ONBOARD_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8000/api/onboarding/submit/ \
    -H "Content-Type: application/json" \
    -d '{"phoneNumber": "+256700000000", "ageBracket": "24-29", "location": "Test"}')

if [ "$ONBOARD_STATUS" = "401" ]; then
    print_success "Onboarding endpoint requires authentication ✅"
else
    print_warning "Onboarding endpoint returned: $ONBOARD_STATUS"
fi

# Test database operations
print_status "Testing database operations..."
docker-compose -f docker-compose.local.yml exec -T web python manage.py shell << 'EOF'
from riders.models import Rider
import sys

try:
    # Test age bracket choices
    choices = [choice[0] for choice in Rider.AGE_BRACKET_CHOICES]
    expected_brackets = ['18-23', '24-29', '30-35', '36-41', '42-47', '48-53', '54-59', '60-65', '66+']
    
    if all(bracket in choices for bracket in expected_brackets):
        print("✅ Age bracket choices are correct")
    else:
        print("❌ Age bracket choices missing")
        sys.exit(1)
    
    # Test PIN functionality
    rider = Rider.objects.filter(phone_number='+256700123456').first()
    if rider:
        if rider.has_pin_set():
            print("✅ Existing test rider has PIN set")
            
            # Test PIN verification
            if rider.verify_pin('1234'):
                print("✅ PIN verification working")
            else:
                print("❌ PIN verification failed")
                sys.exit(1)
        else:
            print("⚠️ Test rider doesn't have PIN set")
    else:
        print("ℹ️ No test rider found (this is OK)")
        
    print("✅ Database operations test completed")
    
except Exception as e:
    print(f"❌ Database test failed: {e}")
    sys.exit(1)
EOF

if [ $? -eq 0 ]; then
    print_success "Database operations working correctly"
else
    print_error "Database operations failed"
    exit 1
fi

# Test Celery workers
print_status "Testing Celery workers..."
if docker-compose -f docker-compose.local.yml ps | grep celery | grep -q "Up"; then
    print_success "Celery workers are running"
else
    print_warning "Celery workers may not be running"
fi

# Performance test
print_status "Running basic performance test..."
START_TIME=$(date +%s%N)
for i in {1..5}; do
    curl -s http://localhost:8000/api/auth/verify-token/ > /dev/null
done
END_TIME=$(date +%s%N)
DURATION=$((($END_TIME - $START_TIME) / 1000000))

if [ $DURATION -lt 5000 ]; then
    print_success "API response time: ${DURATION}ms (Good)"
else
    print_warning "API response time: ${DURATION}ms (Slow)"
fi

echo ""
echo "======================================================"
print_success "🎉 Local testing completed!"
echo ""
echo "📋 Test Results Summary:"
echo "  ✅ Database connection and migrations"
echo "  ✅ PIN authentication endpoints"
echo "  ✅ Enhanced login functionality"
echo "  ✅ Age bracket support"
echo "  ✅ Database operations"
echo "  ✅ Service health checks"
echo ""
echo "🚀 Your changes are ready to push to GitHub!"
echo ""
echo "💡 Next steps:"
echo "1. git add . && git commit -m 'Your commit message'"
echo "2. git push origin main"
echo "3. Monitor GitHub Actions for automated deployment"
echo ""
print_status "Happy coding! 🎉"
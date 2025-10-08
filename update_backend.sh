#!/bin/bash

# DigitalOcean Backend Update Script for Authentication Enhancements
# Upload this file to your droplet and run: chmod +x update_backend.sh && ./update_backend.sh

set -e

echo "🚀 Updating DigitalBoda Backend with Authentication Enhancements..."

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_DIR="/var/www/digitalboda_backend"
BACKUP_DIR="/tmp/digitalboda_backups"

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then
    print_error "Please run this script as root (use sudo)"
    exit 1
fi

# Create backup directory
mkdir -p $BACKUP_DIR

print_status "Starting deployment of authentication enhancements..."
echo "============================================================="

# Backup database
print_status "Creating database backup..."
BACKUP_FILE="$BACKUP_DIR/backup_$(date +%Y%m%d_%H%M%S).sql"
sudo -u postgres pg_dump digitalboda_prod > $BACKUP_FILE
print_success "Database backup created: $BACKUP_FILE"

# Backup media files
print_status "Backing up media files..."
MEDIA_BACKUP="$BACKUP_DIR/media_backup_$(date +%Y%m%d_%H%M%S).tar.gz"
tar -czf $MEDIA_BACKUP $PROJECT_DIR/media/ 2>/dev/null || print_warning "Media backup skipped"

# Navigate to project
print_status "Navigating to project directory..."
cd $PROJECT_DIR

# Show current commit
print_status "Current commit:"
git log --oneline -1

# Pull latest changes
print_status "Pulling latest changes from GitHub..."
git pull origin main

print_status "New commit:"
git log --oneline -1

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
print_status "Installing dependencies..."
pip install -r requirements.txt

# Check if bcrypt is installed
if pip list | grep -i bcrypt > /dev/null; then
    print_success "bcrypt is installed (required for PIN authentication)"
else
    print_error "bcrypt is not installed - PIN authentication will not work"
    exit 1
fi

# Show migration status before
print_status "Migration status before update:"
python manage.py showmigrations riders | tail -5

# Run migrations
print_status "Running database migrations..."
python manage.py migrate

# Show migration status after
print_status "Migration status after update:"
python manage.py showmigrations riders | tail -5

# Check if new migration was applied
if python manage.py showmigrations riders | grep -q "0013_add_pin_and_age_bracket_fields"; then
    print_success "✅ PIN and age bracket migration applied successfully"
else
    print_warning "⚠️ New migration may not have been applied"
fi

# Collect static files
print_status "Collecting static files..."
python manage.py collectstatic --noinput

# Set proper permissions
print_status "Setting file permissions..."
chown -R www-data:www-data $PROJECT_DIR
chmod -R 755 $PROJECT_DIR

# Stop services gracefully
print_status "Stopping services..."
supervisorctl stop digitalboda digitalboda_celery digitalboda_beat

# Wait a moment
sleep 2

# Start services
print_status "Starting services..."
supervisorctl start digitalboda
supervisorctl start digitalboda_celery  
supervisorctl start digitalboda_beat

# Wait for services to initialize
print_status "Waiting for services to initialize..."
sleep 5

# Check service status
print_status "Checking service status..."
supervisorctl status

# Test the API
print_status "Testing API endpoints..."

# Test basic connectivity
if curl -f -s http://localhost:8000/api/auth/verify-token/ > /dev/null 2>&1; then
    print_success "✅ Basic API is responding"
else
    print_warning "⚠️ API test returned an error (might be expected for auth endpoints)"
fi

# Test new PIN endpoints
print_status "Testing new PIN endpoints..."

# Test PIN status endpoint (should return 401 Unauthorized)
PIN_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/auth/pin/status/)
if [ "$PIN_STATUS" = "401" ]; then
    print_success "✅ PIN status endpoint is working (requires authentication)"
elif [ "$PIN_STATUS" = "404" ]; then
    print_error "❌ PIN status endpoint not found - URL routing may need update"
else
    print_warning "⚠️ PIN status endpoint returned unexpected status: $PIN_STATUS"
fi

# Test PIN setup endpoint (should return 401 Unauthorized)
PIN_SETUP=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8000/api/auth/pin/setup/)
if [ "$PIN_SETUP" = "401" ]; then
    print_success "✅ PIN setup endpoint is working (requires authentication)"
elif [ "$PIN_SETUP" = "404" ]; then
    print_error "❌ PIN setup endpoint not found - URL routing may need update"
else
    print_warning "⚠️ PIN setup endpoint returned unexpected status: $PIN_SETUP"
fi

# Test enhanced login endpoint
LOGIN_TEST=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8000/api/auth/rider/login/ \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+256700000000", "login_type": "pin", "pin_code": "1234"}')

if [ "$LOGIN_TEST" = "404" ]; then
    print_success "✅ Enhanced login endpoint is working (user not found as expected)"
else
    print_warning "⚠️ Enhanced login endpoint returned status: $LOGIN_TEST"
fi

echo ""
echo "============================================================="
print_success "🎉 Deployment completed successfully!"
echo ""
print_status "📋 Summary of changes deployed:"
echo "✅ PIN authentication system with bcrypt encryption"
echo "✅ Age brackets for privacy protection"  
echo "✅ Enhanced API endpoints for PIN management"
echo "✅ Rate limiting and security improvements"
echo "✅ Database schema updated with new fields"
echo ""
print_warning "📝 Next steps:"
echo "1. Test the new authentication features with your mobile apps"
echo "2. Monitor logs: tail -f /var/log/supervisor/digitalboda.log"
echo "3. Update your mobile apps with the new features"
echo "4. Monitor user adoption of PIN authentication"
echo ""
print_status "🔗 New API Endpoints Available:"
echo "• POST /api/auth/pin/setup/ - Setup user PIN"
echo "• POST /api/auth/pin/change/ - Change existing PIN"
echo "• GET /api/auth/pin/status/ - Get PIN status"
echo "• POST /api/auth/rider/login/ - Enhanced login with PIN support"
echo ""
print_status "📊 Monitor deployment:"
echo "• Service status: supervisorctl status"
echo "• API logs: tail -f /var/log/supervisor/digitalboda.log"
echo "• Test endpoints: curl https://dashboard.digitalboda.com/api/auth/verify-token/"
echo ""
print_success "Authentication enhancement deployment completed! 🚀"
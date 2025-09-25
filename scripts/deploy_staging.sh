#!/bin/bash

# DigitalBoda Staging Deployment Script
# This script deploys the application to the staging environment

set -e

echo "🚀 Starting DigitalBoda Staging Deployment..."

# Configuration
STAGING_USER="root"
STAGING_HOST=""  # Will be set during Digital Ocean setup
PROJECT_DIR="/var/www/digitalboda_staging"
SERVICE_NAME="digitalboda_staging"
BRANCH="chris"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Check if staging host is configured
if [ -z "$STAGING_HOST" ]; then
    print_error "STAGING_HOST is not configured. Please update this script with your staging server IP."
    exit 1
fi

print_status "Deploying to staging server: $STAGING_HOST"

# SSH command wrapper
ssh_exec() {
    ssh -o StrictHostKeyChecking=no $STAGING_USER@$STAGING_HOST "$1"
}

# Check if we can connect to the staging server
print_info "Testing connection to staging server..."
if ! ssh_exec "echo 'Connection successful'"; then
    print_error "Cannot connect to staging server. Please check your SSH configuration."
    exit 1
fi

print_status "Connected to staging server successfully!"

# Deploy to staging
print_status "Deploying application to staging..."

ssh_exec "
    set -e
    
    # Navigate to project directory
    cd $PROJECT_DIR
    
    # Pull latest changes from chris branch
    git fetch origin
    git checkout $BRANCH
    git pull origin $BRANCH
    
    # Create backup of current containers
    docker-compose -f docker-compose.staging.yml down
    
    # Pull latest Docker images
    docker-compose -f docker-compose.staging.yml pull
    
    # Build and start containers
    docker-compose -f docker-compose.staging.yml up --build -d
    
    # Wait for services to be ready
    sleep 30
    
    # Run database migrations
    docker-compose -f docker-compose.staging.yml exec -T web python manage.py migrate
    
    # Collect static files
    docker-compose -f docker-compose.staging.yml exec -T web python manage.py collectstatic --noinput
    
    # Check container status
    docker-compose -f docker-compose.staging.yml ps
    
    # Test the deployment
    if curl -f http://localhost:8001/admin/ > /dev/null 2>&1; then
        echo '✅ Staging deployment successful!'
    else
        echo '❌ Staging deployment failed - service not responding'
        exit 1
    fi
"

print_status "Staging deployment completed successfully!"
print_info "You can access the staging environment at: http://$STAGING_HOST:8001"
print_warning "Remember to test all functionality before promoting to production!"

echo ""
echo "🎉 Staging deployment finished!"

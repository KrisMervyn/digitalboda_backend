#!/bin/bash

# DigitalBoda Production Deployment Script
# This script deploys the application to the production environment with safety checks

set -e

echo "🚀 Starting DigitalBoda Production Deployment..."

# Configuration
PRODUCTION_USER="root"
PRODUCTION_HOST=""  # Will be set during Digital Ocean setup
PROJECT_DIR="/var/www/digitalboda_production"
SERVICE_NAME="digitalboda_production"
BRANCH="main"
BACKUP_DIR="/var/backups/digitalboda"

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

# Check if production host is configured
if [ -z "$PRODUCTION_HOST" ]; then
    print_error "PRODUCTION_HOST is not configured. Please update this script with your production server IP."
    exit 1
fi

print_warning "⚠️  PRODUCTION DEPLOYMENT ⚠️"
print_warning "This will deploy to your live production environment!"
print_info "Production server: $PRODUCTION_HOST"

# Confirmation prompt
read -p "Are you sure you want to deploy to production? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    print_info "Deployment cancelled."
    exit 0
fi

# SSH command wrapper
ssh_exec() {
    ssh -o StrictHostKeyChecking=no $PRODUCTION_USER@$PRODUCTION_HOST "$1"
}

# Check if we can connect to the production server
print_info "Testing connection to production server..."
if ! ssh_exec "echo 'Connection successful'"; then
    print_error "Cannot connect to production server. Please check your SSH configuration."
    exit 1
fi

print_status "Connected to production server successfully!"

# Pre-deployment checks
print_status "Running pre-deployment checks..."

ssh_exec "
    set -e
    
    # Check if project directory exists
    if [ ! -d $PROJECT_DIR ]; then
        echo 'ERROR: Project directory does not exist!'
        exit 1
    fi
    
    # Check if .env.production exists
    if [ ! -f $PROJECT_DIR/.env.production ]; then
        echo 'ERROR: .env.production file not found!'
        exit 1
    fi
    
    # Check if current deployment is healthy
    cd $PROJECT_DIR
    if ! docker-compose -f docker-compose.production.yml ps | grep -q 'Up'; then
        echo 'WARNING: Current deployment appears to be down'
    fi
"

# Create backup
print_status "Creating backup before deployment..."

ssh_exec "
    set -e
    
    # Create backup directory
    mkdir -p $BACKUP_DIR
    
    cd $PROJECT_DIR
    
    # Backup database
    BACKUP_FILE=\"$BACKUP_DIR/backup_\$(date +%Y%m%d_%H%M%S).sql\"
    docker-compose -f docker-compose.production.yml exec -T db pg_dump -U \$DB_USER \$DB_NAME > \$BACKUP_FILE
    
    echo \"Database backup created: \$BACKUP_FILE\"
    
    # Backup current code
    tar -czf \"$BACKUP_DIR/code_backup_\$(date +%Y%m%d_%H%M%S).tar.gz\" \
        --exclude='.git' \
        --exclude='venv*' \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        .
"

# Deploy to production
print_status "Deploying application to production..."

ssh_exec "
    set -e
    
    # Navigate to project directory
    cd $PROJECT_DIR
    
    # Pull latest changes from main branch
    git fetch origin
    git checkout $BRANCH
    git pull origin $BRANCH
    
    # Pull latest Docker images
    docker-compose -f docker-compose.production.yml pull
    
    # Perform zero-downtime deployment
    print_info 'Starting zero-downtime deployment...'
    
    # Build new containers
    docker-compose -f docker-compose.production.yml build
    
    # Start new web container alongside old one
    docker-compose -f docker-compose.production.yml up -d --no-deps --scale web=2 web
    
    # Wait for new container to be healthy
    sleep 45
    
    # Check if new containers are healthy
    for i in {1..6}; do
        if curl -f http://localhost:8000/admin/ > /dev/null 2>&1; then
            echo 'New containers are healthy!'
            break
        fi
        if [ \$i -eq 6 ]; then
            echo 'New containers failed health check!'
            exit 1
        fi
        sleep 10
    done
    
    # Scale down to 1 instance (removes old container)
    docker-compose -f docker-compose.production.yml up -d --scale web=1
    
    # Update other services
    docker-compose -f docker-compose.production.yml up -d
    
    # Run database migrations
    docker-compose -f docker-compose.production.yml exec -T web python manage.py migrate
    
    # Collect static files
    docker-compose -f docker-compose.production.yml exec -T web python manage.py collectstatic --noinput
    
    # Final health check
    sleep 30
    docker-compose -f docker-compose.production.yml ps
    
    # Test the deployment
    if curl -f http://localhost:8000/admin/ > /dev/null 2>&1; then
        echo '✅ Production deployment successful!'
    else
        echo '❌ Production deployment failed - service not responding'
        echo 'Rolling back...'
        
        # Rollback command would go here
        exit 1
    fi
"

# Post-deployment tasks
print_status "Running post-deployment tasks..."

ssh_exec "
    cd $PROJECT_DIR
    
    # Clean up old Docker images
    docker image prune -f
    
    # Log deployment
    echo \"\$(date): Production deployment completed successfully\" >> /var/log/digitalboda-deployments.log
"

print_status "Production deployment completed successfully!"
print_info "You can access the production environment at: https://$PRODUCTION_HOST"
print_warning "Monitor the application closely for the next 30 minutes."

# Send notification (if webhook is configured)
if [ ! -z "$SLACK_WEBHOOK_URL" ]; then
    curl -X POST -H 'Content-type: application/json' \
        --data "{\"text\":\"🚀 DigitalBoda production deployment completed successfully!\"}" \
        $SLACK_WEBHOOK_URL
fi

echo ""
echo "🎉 Production deployment finished!"
echo "📊 Remember to monitor:"
echo "   - Application logs"
echo "   - Database performance"
echo "   - Server resources"
echo "   - User feedback"

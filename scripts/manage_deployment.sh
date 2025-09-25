#!/bin/bash

# DigitalBoda Deployment Management Script
# This script provides common deployment management tasks

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

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

# Help function
show_help() {
    echo "DigitalBoda Deployment Management"
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  local-staging     - Start local staging environment"
    echo "  local-production  - Start local production environment"
    echo "  deploy-staging    - Deploy to staging server"
    echo "  deploy-production - Deploy to production server"
    echo "  status            - Check deployment status"
    echo "  logs              - View application logs"
    echo "  backup            - Create database backup"
    echo "  rollback          - Rollback to previous version"
    echo "  ssh-staging       - SSH into staging server"
    echo "  ssh-production    - SSH into production server"
    echo ""
    echo "Options:"
    echo "  -h, --help        - Show this help message"
    echo "  -v, --verbose     - Verbose output"
}

# Local staging environment
start_local_staging() {
    print_status "Starting local staging environment..."
    cd "$PROJECT_ROOT"
    
    if [ ! -f .env.staging ]; then
        print_warning "Creating .env.staging from example..."
        cp .env.example .env.staging
        print_warning "Please update .env.staging with appropriate values"
    fi
    
    docker-compose -f docker-compose.staging.yml down
    docker-compose -f docker-compose.staging.yml up --build -d
    
    print_status "Waiting for services to start..."
    sleep 20
    
    print_status "Running migrations..."
    docker-compose -f docker-compose.staging.yml exec web python manage.py migrate
    
    print_status "Collecting static files..."
    docker-compose -f docker-compose.staging.yml exec web python manage.py collectstatic --noinput
    
    print_status "Local staging environment is running!"
    print_info "Access at: http://localhost:8001"
}

# Local production environment
start_local_production() {
    print_status "Starting local production environment..."
    cd "$PROJECT_ROOT"
    
    if [ ! -f .env.production ]; then
        print_warning "Creating .env.production from example..."
        cp .env.example .env.production
        print_warning "Please update .env.production with appropriate values"
    fi
    
    docker-compose -f docker-compose.production.yml down
    docker-compose -f docker-compose.production.yml up --build -d
    
    print_status "Waiting for services to start..."
    sleep 20
    
    print_status "Running migrations..."
    docker-compose -f docker-compose.production.yml exec web python manage.py migrate
    
    print_status "Collecting static files..."
    docker-compose -f docker-compose.production.yml exec web python manage.py collectstatic --noinput
    
    print_status "Local production environment is running!"
    print_info "Access at: http://localhost:8000"
}

# Deploy to staging
deploy_staging() {
    print_status "Deploying to staging..."
    bash "$SCRIPT_DIR/deploy_staging.sh"
}

# Deploy to production
deploy_production() {
    print_status "Deploying to production..."
    bash "$SCRIPT_DIR/deploy_production.sh"
}

# Check deployment status
check_status() {
    echo "Which environment status would you like to check?"
    echo "1) Local staging"
    echo "2) Local production"
    echo "3) Remote staging"
    echo "4) Remote production"
    read -p "Enter choice (1-4): " status_choice
    
    case $status_choice in
        1)
            print_info "Local staging status:"
            docker-compose -f docker-compose.staging.yml ps
            ;;
        2)
            print_info "Local production status:"
            docker-compose -f docker-compose.production.yml ps
            ;;
        3)
            print_info "Remote staging status:"
            # Add SSH command to check remote staging
            print_warning "Remote status check not yet configured"
            ;;
        4)
            print_info "Remote production status:"
            # Add SSH command to check remote production
            print_warning "Remote status check not yet configured"
            ;;
        *)
            print_error "Invalid choice"
            ;;
    esac
}

# View logs
view_logs() {
    echo "Which logs would you like to view?"
    echo "1) Local staging"
    echo "2) Local production"
    read -p "Enter choice (1-2): " log_choice
    
    case $log_choice in
        1)
            docker-compose -f docker-compose.staging.yml logs -f
            ;;
        2)
            docker-compose -f docker-compose.production.yml logs -f
            ;;
        *)
            print_error "Invalid choice"
            ;;
    esac
}

# Create backup
create_backup() {
    echo "Which environment backup?"
    echo "1) Local staging"
    echo "2) Local production"
    read -p "Enter choice (1-2): " backup_choice
    
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    
    case $backup_choice in
        1)
            print_status "Creating staging backup..."
            docker-compose -f docker-compose.staging.yml exec db pg_dump -U $DB_USER $DB_NAME > "backup_staging_$TIMESTAMP.sql"
            print_status "Backup created: backup_staging_$TIMESTAMP.sql"
            ;;
        2)
            print_status "Creating production backup..."
            docker-compose -f docker-compose.production.yml exec db pg_dump -U $DB_USER $DB_NAME > "backup_production_$TIMESTAMP.sql"
            print_status "Backup created: backup_production_$TIMESTAMP.sql"
            ;;
        *)
            print_error "Invalid choice"
            ;;
    esac
}

# Make scripts executable
chmod +x "$SCRIPT_DIR"/*.sh

# Main command handler
case "${1:-help}" in
    "local-staging")
        start_local_staging
        ;;
    "local-production")
        start_local_production
        ;;
    "deploy-staging")
        deploy_staging
        ;;
    "deploy-production")
        deploy_production
        ;;
    "status")
        check_status
        ;;
    "logs")
        view_logs
        ;;
    "backup")
        create_backup
        ;;
    "rollback")
        print_warning "Rollback functionality not yet implemented"
        ;;
    "ssh-staging")
        print_warning "SSH staging functionality not yet implemented"
        ;;
    "ssh-production")
        print_warning "SSH production functionality not yet implemented"
        ;;
    "-h"|"--help"|"help")
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac

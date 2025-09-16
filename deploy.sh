#!/bin/bash

# Digital Ocean Deployment Script for Django DigitalBoda Backend
# Run this script on your Digital Ocean droplet

set -e

echo "🚀 Starting DigitalBoda Backend Deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="digitalboda_backend"
PROJECT_DIR="/var/www/$PROJECT_NAME"
SERVICE_NAME="digitalboda"
USER="www-data"

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

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "Please run this script as root (use sudo)"
    exit 1
fi

# Update system
print_status "Updating system packages..."
apt update && apt upgrade -y

# Install required packages
print_status "Installing system dependencies..."
apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    postgresql \
    postgresql-contrib \
    nginx \
    redis-server \
    supervisor \
    git \
    build-essential \
    libpq-dev \
    libssl-dev \
    libffi-dev \
    libjpeg-dev \
    libpng-dev \
    libopencv-dev \
    python3-opencv \
    tesseract-ocr \
    tesseract-ocr-eng \
    pkg-config \
    cmake \
    certbot \
    python3-certbot-nginx

# Create project directory
print_status "Creating project directory..."
mkdir -p $PROJECT_DIR
chown $USER:$USER $PROJECT_DIR

# Create virtual environment
print_status "Setting up Python virtual environment..."
cd $PROJECT_DIR
python3 -m venv venv
source venv/bin/activate

# Install Python packages
print_status "Installing Python dependencies..."
pip install --upgrade pip
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    print_warning "requirements.txt not found. Please upload your project files first."
fi

# Setup PostgreSQL
print_status "Configuring PostgreSQL..."
sudo -u postgres createdb digitalboda_prod 2>/dev/null || print_warning "Database already exists"
sudo -u postgres createuser digitalboda_user 2>/dev/null || print_warning "User already exists"
sudo -u postgres psql -c "ALTER USER digitalboda_user CREATEDB;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE digitalboda_prod TO digitalboda_user;"

# Configure Redis
print_status "Starting Redis..."
systemctl enable redis-server
systemctl start redis-server

# Setup Nginx
print_status "Configuring Nginx..."
if [ -f "nginx.conf" ]; then
    cp nginx.conf /etc/nginx/sites-available/$SERVICE_NAME
    ln -sf /etc/nginx/sites-available/$SERVICE_NAME /etc/nginx/sites-enabled/
    rm -f /etc/nginx/sites-enabled/default
    nginx -t && systemctl reload nginx
fi

# Setup Supervisor for Gunicorn
print_status "Setting up Supervisor..."
cat > /etc/supervisor/conf.d/$SERVICE_NAME.conf << EOF
[program:$SERVICE_NAME]
command=$PROJECT_DIR/venv/bin/gunicorn --config $PROJECT_DIR/gunicorn.conf.py digitalboda_backend.wsgi:application
directory=$PROJECT_DIR
user=$USER
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/supervisor/$SERVICE_NAME.log
environment=DJANGO_ENV="production"
EOF

# Setup Supervisor for Celery Worker
cat > /etc/supervisor/conf.d/${SERVICE_NAME}_celery.conf << EOF
[program:${SERVICE_NAME}_celery]
command=$PROJECT_DIR/venv/bin/celery -A digitalboda_backend worker --loglevel=info
directory=$PROJECT_DIR
user=$USER
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/supervisor/${SERVICE_NAME}_celery.log
environment=DJANGO_ENV="production"
EOF

# Setup Supervisor for Celery Beat
cat > /etc/supervisor/conf.d/${SERVICE_NAME}_beat.conf << EOF
[program:${SERVICE_NAME}_beat]
command=$PROJECT_DIR/venv/bin/celery -A digitalboda_backend beat --loglevel=info
directory=$PROJECT_DIR
user=$USER
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/supervisor/${SERVICE_NAME}_beat.log
environment=DJANGO_ENV="production"
EOF

# Create log directory
mkdir -p /var/log/supervisor

# Update supervisor configuration
supervisorctl reread
supervisorctl update

# Set up proper permissions
chown -R $USER:$USER $PROJECT_DIR
chmod -R 755 $PROJECT_DIR

print_status "Deployment configuration completed!"
print_warning "Next steps:"
echo "1. Upload your project files to $PROJECT_DIR"
echo "2. Update .env.production with your actual database credentials and domain"
echo "3. Update nginx.conf with your actual domain name"
echo "4. Run 'python manage.py migrate' to set up the database"
echo "5. Run 'python manage.py collectstatic' to collect static files"
echo "6. Run 'supervisorctl start all' to start the services"
echo "7. Get SSL certificate: certbot --nginx -d yourdomain.com"
echo ""
print_status "Deployment script finished!"
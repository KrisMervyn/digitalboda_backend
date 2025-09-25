#!/bin/bash

# DigitalBoda Server Setup Script for Digital Ocean
# This script sets up both staging and production servers

set -e

echo "🚀 Starting DigitalBoda Server Setup..."

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

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "Please run this script as root (use sudo)"
    exit 1
fi

# Get environment type
echo "Which environment are you setting up?"
echo "1) Staging"
echo "2) Production"
read -p "Enter choice (1 or 2): " env_choice

case $env_choice in
    1)
        ENVIRONMENT="staging"
        PROJECT_DIR="/var/www/digitalboda_staging"
        SERVICE_NAME="digitalboda_staging"
        BRANCH="chris"
        ;;
    2)
        ENVIRONMENT="production"
        PROJECT_DIR="/var/www/digitalboda_production"
        SERVICE_NAME="digitalboda_production"
        BRANCH="main"
        ;;
    *)
        print_error "Invalid choice. Please run the script again."
        exit 1
        ;;
esac

print_status "Setting up $ENVIRONMENT environment..."

# Update system packages
print_status "Updating system packages..."
apt update && apt upgrade -y

# Install Docker
print_status "Installing Docker..."
if ! command -v docker &> /dev/null; then
    apt install -y apt-transport-https ca-certificates curl software-properties-common
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add -
    add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
    apt update
    apt install -y docker-ce docker-ce-cli containerd.io
    systemctl enable docker
    systemctl start docker
else
    print_info "Docker is already installed"
fi

# Install Docker Compose
print_status "Installing Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
else
    print_info "Docker Compose is already installed"
fi

# Install additional tools
print_status "Installing additional tools..."
apt install -y git nginx certbot python3-certbot-nginx ufw fail2ban htop curl wget

# Setup firewall
print_status "Configuring firewall..."
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80
ufw allow 443

if [ "$ENVIRONMENT" = "staging" ]; then
    ufw allow 8001
else
    ufw allow 8000
fi

ufw --force enable

# Setup fail2ban
print_status "Configuring fail2ban..."
cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local
systemctl enable fail2ban
systemctl start fail2ban

# Create project directory
print_status "Creating project directory..."
mkdir -p $PROJECT_DIR
cd $PROJECT_DIR

# Clone repository (you'll need to update this with your actual repository URL)
print_warning "You need to clone your repository here:"
print_info "git clone <your-repository-url> ."
print_info "Then checkout the $BRANCH branch"

# Create environment file template
print_status "Creating environment file template..."
cat > .env.$ENVIRONMENT << EOF
# Django Configuration
SECRET_KEY=change-this-secret-key-in-production
DEBUG=False
DJANGO_ENV=$ENVIRONMENT

# Database Configuration
DB_NAME=digitalboda_$ENVIRONMENT
DB_USER=digitalboda_${ENVIRONMENT}_user
DB_PASSWORD=change-this-password
DB_HOST=db
DB_PORT=5432

# Server Configuration
ALLOWED_HOSTS=your-domain.com,www.your-domain.com,localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=https://your-domain.com,https://www.your-domain.com

# Security Settings
SECURE_SSL_REDIRECT=True
ID_ENCRYPTION_KEY=generate-a-32-byte-key-here
ID_HASH_SALT=generate-unique-salt-here

# Firebase Configuration
FIREBASE_CREDENTIALS_PATH=/app/firebase-credentials.json

# Redis Configuration
REDIS_URL=redis://redis:6379/0
EOF

print_warning "Please update the .env.$ENVIRONMENT file with your actual configuration!"

# Setup Nginx configuration
print_status "Setting up Nginx configuration..."
if [ "$ENVIRONMENT" = "production" ]; then
    cat > /etc/nginx/sites-available/digitalboda << EOF
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    # Redirect HTTP to HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    # SSL configuration (will be updated by certbot)
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Serve static files
    location /static/ {
        alias $PROJECT_DIR/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Serve media files
    location /media/ {
        alias $PROJECT_DIR/media/;
        expires 1y;
        add_header Cache-Control "public";
    }

    # Proxy to Django
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_redirect off;
    }
}
EOF

    ln -sf /etc/nginx/sites-available/digitalboda /etc/nginx/sites-enabled/
    rm -f /etc/nginx/sites-enabled/default
    
else
    # Staging configuration
    cat > /etc/nginx/sites-available/digitalboda-staging << EOF
server {
    listen 80;
    server_name staging.your-domain.com;

    # Serve static files
    location /static/ {
        alias $PROJECT_DIR/staticfiles/;
    }

    # Serve media files
    location /media/ {
        alias $PROJECT_DIR/media/;
    }

    # Proxy to Django
    location / {
        proxy_pass http://localhost:8001;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_redirect off;
    }
}
EOF

    ln -sf /etc/nginx/sites-available/digitalboda-staging /etc/nginx/sites-enabled/
fi

# Test and reload Nginx
nginx -t && systemctl reload nginx

# Create backup directory
print_status "Creating backup directory..."
mkdir -p /var/backups/digitalboda
chmod 755 /var/backups/digitalboda

# Create deployment logs directory
mkdir -p /var/log/digitalboda
chmod 755 /var/log/digitalboda

# Setup log rotation
cat > /etc/logrotate.d/digitalboda << EOF
/var/log/digitalboda/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    sharedscripts
}
EOF

# Create cron job for log cleanup
echo "0 2 * * 0 find /var/log/digitalboda -name '*.log' -mtime +30 -delete" | crontab -

# Setup monitoring script
cat > /usr/local/bin/digitalboda-health-check.sh << EOF
#!/bin/bash
cd $PROJECT_DIR
if ! docker-compose -f docker-compose.$ENVIRONMENT.yml ps | grep -q "Up"; then
    echo "\$(date): DigitalBoda $ENVIRONMENT containers are not running!" >> /var/log/digitalboda/health.log
    # Add notification logic here (email, Slack, etc.)
fi
EOF

chmod +x /usr/local/bin/digitalboda-health-check.sh

# Add health check to cron
echo "*/5 * * * * /usr/local/bin/digitalboda-health-check.sh" | crontab -

print_status "Server setup completed!"
print_warning "Next steps:"
echo "1. Clone your repository to $PROJECT_DIR"
echo "2. Update .env.$ENVIRONMENT with your actual configuration"
echo "3. Update Nginx configuration with your actual domain"
echo "4. Run: docker-compose -f docker-compose.$ENVIRONMENT.yml up -d"
echo "5. For production: Get SSL certificate with: certbot --nginx -d your-domain.com"

if [ "$ENVIRONMENT" = "production" ]; then
    print_warning "For production, also:"
    echo "6. Setup regular database backups"
    echo "7. Configure monitoring and alerting"
    echo "8. Setup log aggregation"
fi

print_status "Server setup finished!"

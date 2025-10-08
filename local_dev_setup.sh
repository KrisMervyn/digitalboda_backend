#!/bin/bash

# Local Development Setup Script
# Run this to set up your local development environment

set -e

echo "🚀 Setting up DigitalBoda Local Development Environment"
echo "======================================================"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    echo "Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    echo "Visit: https://docs.docker.com/compose/install/"
    exit 1
fi

print_status "Docker and Docker Compose are installed ✅"

# Create local environment file if it doesn't exist
if [ ! -f ".env.local" ]; then
    print_warning ".env.local file not found. Please create it with your local settings."
    exit 1
fi

print_status "Setting up local development environment..."

# Stop any running containers
print_status "Stopping any existing containers..."
docker-compose -f docker-compose.local.yml down --remove-orphans || true

# Build the containers
print_status "Building Docker containers..."
docker-compose -f docker-compose.local.yml build

# Start the services
print_status "Starting services..."
docker-compose -f docker-compose.local.yml up -d

# Wait for services to be ready
print_status "Waiting for services to be ready..."
sleep 10

# Check if services are running
print_status "Checking service health..."
if docker-compose -f docker-compose.local.yml ps | grep -q "Up"; then
    print_success "Services are running!"
else
    print_error "Some services failed to start. Check logs with: docker-compose -f docker-compose.local.yml logs"
    exit 1
fi

# Run initial migrations
print_status "Running database migrations..."
docker-compose -f docker-compose.local.yml exec web python manage.py migrate

# Create superuser (optional)
print_status "Creating test data..."
docker-compose -f docker-compose.local.yml exec web python manage.py shell << 'EOF'
from django.contrib.auth.models import User
from riders.models import Rider

# Create superuser if it doesn't exist
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@digitalboda.com', 'admin123')
    print("✅ Superuser created: admin/admin123")

# Create test rider if it doesn't exist
if not Rider.objects.filter(phone_number='+256700123456').exists():
    rider = Rider.objects.create(
        phone_number='+256700123456',
        first_name='Test',
        last_name='Rider',
        age_bracket='24-29',
        location='Kampala',
        status='APPROVED'
    )
    rider.set_pin('1234')
    print("✅ Test rider created: +256700123456 with PIN: 1234")
EOF

print_success "✅ Local development environment is ready!"
echo ""
echo "🔗 Access your application:"
echo "   • Django Admin: http://localhost:8000/admin/"
echo "   • API Base: http://localhost:8000/api/"
echo "   • Login: admin / admin123"
echo ""
echo "🧪 Test the new authentication features:"
echo "   • PIN Status: curl http://localhost:8000/api/auth/pin/status/"
echo "   • PIN Login: curl -X POST http://localhost:8000/api/auth/rider/login/ \\"
echo "              -H 'Content-Type: application/json' \\"
echo "              -d '{\"phone_number\":\"+256700123456\",\"pin_code\":\"1234\",\"login_type\":\"pin\"}'"
echo ""
echo "📊 Monitor your services:"
echo "   • View logs: docker-compose -f docker-compose.local.yml logs -f"
echo "   • Stop services: docker-compose -f docker-compose.local.yml down"
echo "   • Restart: docker-compose -f docker-compose.local.yml restart web"
echo ""
print_success "Happy coding! 🎉"
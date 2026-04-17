#!/bin/bash

# Secure Deployment Script for Lost and Found Application
# This script sets up the application with DDoS protection and security hardening

set -e

echo "🚀 Starting Secure Deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# Check if running as root for system operations
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root for security reasons"
   exit 1
fi

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p logs ssl nginx

# Install system dependencies if needed
print_status "Checking system dependencies..."

# Check if nginx is installed
if ! command -v nginx &> /dev/null; then
    print_warning "Nginx not found. Installing nginx..."
    sudo apt update
    sudo apt install -y nginx
fi

# Check if certbot is installed (for SSL certificates)
if ! command -v certbot &> /dev/null; then
    print_warning "Certbot not found. Installing certbot..."
    sudo apt install -y certbot python3-certbot-nginx
fi

# Generate SSL certificates (self-signed for development, Let's Encrypt for production)
print_status "Setting up SSL certificates..."

if [ ! -f ssl/cert.pem ]; then
    print_warning "Generating self-signed SSL certificate (for development)..."
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout ssl/key.pem \
        -out ssl/cert.pem \
        -subj "/C=HK/ST=Hong Kong/L=Hong Kong/O=EIE3117/OU=IT/CN=localhost"
    
    print_status "SSL certificates generated successfully"
else
    print_status "SSL certificates already exist"
fi

# Set up secure environment file
print_status "Setting up secure environment configuration..."

if [ ! -f .env ]; then
    cat > .env << EOF
# Production Security Configuration
DJANGO_SECRET_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(50))')
DJANGO_DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,\$(hostname -I | cut -d' ' -f1)

# Database Configuration (keep existing MongoDB connection)
MONGODB_URI=mongodb+srv://25015946d:aA386696135@cluster0.zjg38gj.mongodb.net/lost_found_db?retryWrites=true&w=majority

# Security Settings
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
SECURE_CONTENT_TYPE_NOSNIFF=True
SECURE_BROWSER_XSS_FILTER=True
SECURE_REFERRER_POLICY=strict-origin-when-cross-origin

# Rate Limiting
RATE_LIMIT_REQUESTS_PER_MINUTE=60
RATE_LIMIT_REQUESTS_PER_HOUR=1000
RATE_LIMIT_REQUESTS_PER_DAY=10000

# Logging
LOG_LEVEL=INFO
EOF
    print_status "Environment configuration created"
else
    print_status "Environment configuration already exists"
fi

# Install Python dependencies
print_status "Installing Python dependencies..."
cd backend
pip install -r requirement.txt

# Install security dependencies
print_status "Installing additional security packages..."
pip install django-ratelimit django-axes django-security bleach django-defender gunicorn

# Run Django migrations
print_status "Running Django migrations..."
python manage.py migrate

# Collect static files
print_status "Collecting static files..."
python manage.py collectstatic --noinput

# Create superuser if doesn't exist
print_status "Setting up admin user..."
python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'secure_admin_password_123!')
    print("Admin user created")
else:
    print("Admin user already exists")
EOF

cd ..

# Install Node.js dependencies
print_status "Installing frontend dependencies..."
cd frontend
npm install

# Build frontend for production
print_status "Building frontend for production..."
npm run build

cd ..

# Configure nginx
print_status "Configuring nginx reverse proxy..."
sudo cp nginx/nginx.conf /etc/nginx/sites-available/lost-found
sudo ln -sf /etc/nginx/sites-available/lost-found /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
sudo nginx -t

# Set up log rotation
print_status "Setting up log rotation..."
sudo tee /etc/logrotate.d/lost-found << EOF
/home/udon/Downloads/EIE3117_project/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 udon udon
    postrotate
        systemctl reload nginx
    endscript
}
EOF

# Create systemd service for Django
print_status "Creating systemd service for Django application..."
sudo tee /etc/systemd/system/lost-found-backend.service << EOF
[Unit]
Description=Lost and Found Backend
After=network.target

[Service]
Type=exec
User=udon
Group=udon
WorkingDirectory=/home/udon/Downloads/EIE3117_project/backend
Environment=PATH=/home/udon/Downloads/EIE3117_project/backend/venv/bin
ExecStart=/home/udon/Downloads/EIE3117_project/backend/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:8000 lost_found.wsgi:application
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Create systemd service for monitoring
print_status "Creating monitoring service..."
sudo tee /etc/systemd/system/lost-found-monitor.service << EOF
[Unit]
Description=Lost and Found Security Monitor
After=network.target

[Service]
Type=oneshot
User=udon
WorkingDirectory=/home/udon/Downloads/EIE3117_project
ExecStart=/bin/bash -c 'tail -f logs/security.log | grep -i "attack\|injection\|blocked" | logger -t security-monitor'
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and enable services
print_status "Enabling and starting services..."
sudo systemctl daemon-reload
sudo systemctl enable lost-found-backend
sudo systemctl enable lost-found-monitor

# Start services
print_status "Starting application services..."
sudo systemctl start lost-found-backend
sudo systemctl start lost-found-monitor
sudo systemctl restart nginx

# Set up firewall rules
print_status "Configuring firewall rules..."
if command -v ufw &> /dev/null; then
    sudo ufw --force enable
    sudo ufw allow ssh
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    sudo ufw deny 8000/tcp  # Block direct access to Django
    sudo ufw deny 8081/tcp  # Block direct access to Vue dev server
    print_status "Firewall rules configured"
else
    print_warning "UFW not found. Please configure firewall manually"
fi

# Create monitoring script
print_status "Creating security monitoring script..."
cat > monitor-attacks.sh << 'EOF'
#!/bin/bash

# Security Monitoring Script
LOG_FILE="logs/security.log"
ALERT_THRESHOLD=10

# Check for recent attacks
check_attacks() {
    local attack_count=$(tail -100 "$LOG_FILE" | grep -i "attack\|injection\|blocked" | wc -l)
    
    if [ "$attack_count" -gt "$ALERT_THRESHOLD" ]; then
        echo "🚨 HIGH ATTACK VOLUME DETECTED: $attack_count attacks in last 100 log entries"
        echo "Check $LOG_FILE for details"
        
        # Optional: Send email notification
        # echo "Attack detected on $(hostname)" | mail -s "Security Alert" admin@example.com
    fi
}

# Check for blocked IPs
check_blocked_ips() {
    local blocked_count=$(tail -100 "$LOG_FILE" | grep "blocked" | wc -l)
    echo "📊 Blocked IPs in recent logs: $blocked_count"
}

# Check rate limiting
check_rate_limits() {
    local rate_limit_count=$(tail -100 "$LOG_FILE" | grep "Rate limit" | wc -l)
    echo "📈 Rate limit violations: $rate_limit_count"
}

echo "🔍 Security Monitor Report - $(date)"
echo "=================================="
check_attacks
check_blocked_ips
check_rate_limits
echo "=================================="
EOF

chmod +x monitor-attacks.sh

# Final status check
print_status "Performing final security checks..."

# Check if services are running
if systemctl is-active --quiet nginx; then
    print_status "✅ Nginx is running"
else
    print_error "❌ Nginx is not running"
fi

if systemctl is-active --quiet lost-found-backend; then
    print_status "✅ Django backend is running"
else
    print_error "❌ Django backend is not running"
fi

# Test SSL certificate
if [ -f ssl/cert.pem ]; then
    print_status "✅ SSL certificate is available"
else
    print_error "❌ SSL certificate not found"
fi

# Test application endpoints
print_status "Testing application endpoints..."

# Test health endpoint
if curl -k -s https://localhost/health > /dev/null; then
    print_status "✅ Health endpoint is accessible"
else
    print_warning "⚠️  Health endpoint not accessible (application may still be starting)"
fi

echo ""
echo "🎉 Secure Deployment Complete!"
echo "=================================="
echo "📱 Application URL: https://localhost"
echo "🔒 SSL Certificate: Self-signed (accept browser warning)"
echo "📊 Security Monitor: ./monitor-attacks.sh"
echo "📋 Logs: logs/security.log, logs/django.log"
echo ""
echo "🔐 Security Features Enabled:"
echo "  - DDoS Protection Middleware"
echo "  - Rate Limiting (60 req/min, 1000 req/hr)"
echo "  - SQL/NoSQL Injection Protection"
echo "  - XSS Protection"
echo "  - SSL/TLS Encryption"
echo "  - Security Headers"
echo "  - Input Validation & Sanitization"
echo "  - Attack Monitoring & Logging"
echo ""
echo "⚠️  Important Notes:"
echo "  - Change default admin password"
echo "  - Update ALLOWED_HOSTS for production"
echo "  - Use Let's Encrypt certificates for production"
echo "  - Monitor logs regularly for attacks"
echo ""
echo "🚀 Your application is now ready for penetration testing!"

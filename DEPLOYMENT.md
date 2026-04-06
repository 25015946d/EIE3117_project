# Deployment Guide for Lost and Found Application

This guide explains how to deploy the Lost and Found application on different hosting environments and operating systems.

## Quick Start

### For New Environments

1. **Run the setup script** (one-time setup):
   ```bash
   ./setup-environment.sh
   ```

2. **Start the application**:
   ```bash
   ./start-app.sh
   ```

3. **Stop the application**:
   ```bash
   ./stop-app.sh
   ```

## Supported Environments

### Operating Systems
- ✅ Linux (Ubuntu, Debian, CentOS, RHEL, Fedora, Arch)
- ✅ macOS (with Homebrew)
- ✅ Windows (with Git Bash or WSL)

### Hosting Providers
- ✅ Local development
- ✅ VPS providers (DigitalOcean, Linode, Vultr)
- ✅ Cloud providers (AWS EC2, Google Cloud, Azure)
- ✅ Docker containers
- ✅ Shared hosting (with SSH access)

## Detailed Setup Instructions

### 1. Ubuntu/Debian

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Clone the repository
git clone <your-repo-url>
cd EIE3117_project

# Run setup script
./setup-environment.sh

# Start application
./start-app.sh
```

### 2. CentOS/RHEL/Fedora

```bash
# For RHEL/CentOS, enable EPEL repository first
sudo yum install -y epel-release

# Clone and setup
git clone <your-repo-url>
cd EIE3117_project
./setup-environment.sh
./start-app.sh
```

### 3. macOS

```bash
# Install Xcode Command Line Tools if not installed
xcode-select --install

# Clone and setup
git clone <your-repo-url>
cd EIE3117_project
./setup-environment.sh
./start-app.sh
```

### 4. Windows

#### Option A: Using WSL (Recommended)

```bash
# Install WSL and Ubuntu from Microsoft Store
# Then in WSL terminal:

sudo apt update && sudo apt upgrade -y
git clone <your-repo-url>
cd EIE3117_project
./setup-environment.sh
./start-app.sh
```

#### Option B: Using Git Bash

1. Install Python 3 from https://python.org
2. Install Node.js from https://nodejs.org
3. Install Git from https://git-scm.com
4. Use Git Bash to run:
   ```bash
   git clone <your-repo-url>
   cd EIE3117_project
   ./setup-environment.sh
   ./start-app.sh
   ```

## Environment Configuration

### Backend Environment Variables

Create/update `backend/.env`:

```env
# Database Configuration
MONGODB_URI=mongodb://localhost:27017/lost_found_db
# or for MongoDB Atlas: mongodb+srv://username:password@cluster.mongodb.net/dbname

# Django Configuration
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com

# CORS Configuration
CORS_ALLOWED_ORIGINS=http://localhost:8081,http://your-domain.com
```

### Frontend Environment Variables

Create/update `frontend/.env`:

```env
VUE_APP_API_BASE_URL=http://localhost:8080
VUE_APP_ENVIRONMENT=development
```

## Production Deployment

### 1. Using PM2 (Recommended for Node.js)

```bash
# Install PM2
npm install -g pm2

# Create PM2 ecosystem file
cat > ecosystem.config.js << EOF
module.exports = {
  apps: [
    {
      name: 'lost-found-backend',
      script: './backend/manage.py',
      args: 'runserver 0.0.0.0:8080',
      interpreter: './backend/venv/bin/python',
      cwd: './backend'
    },
    {
      name: 'lost-found-frontend',
      script: 'npm',
      args: 'run serve',
      cwd: './frontend'
    }
  ]
};
EOF

# Start with PM2
pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

### 2. Using Docker

Create `Dockerfile`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Copy and setup backend
COPY backend/ ./backend/
WORKDIR /app/backend
RUN python3 -m venv venv
RUN . venv/bin/activate && pip install -r requirement.txt

# Copy and setup frontend
COPY frontend/ ./frontend/
WORKDIR /app/frontend
RUN npm install

# Expose ports
EXPOSE 8080 8081

# Start script
COPY start-app.sh ./
RUN chmod +x start-app.sh
CMD ["./start-app.sh"]
```

### 3. Using Systemd Services

Create backend service:

```ini
# /etc/systemd/system/lost-found-backend.service
[Unit]
Description=Lost and Found Backend
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/EIE3117_project/backend
Environment=PATH=/path/to/EIE3117_project/backend/venv/bin
ExecStart=/path/to/EIE3117_project/backend/venv/bin/python manage.py runserver 0.0.0.0:8080
Restart=always

[Install]
WantedBy=multi-user.target
```

Create frontend service:

```ini
# /etc/systemd/system/lost-found-frontend.service
[Unit]
Description=Lost and Found Frontend
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/EIE3117_project/frontend
ExecStart=/usr/bin/npm run serve
Restart=always

[Install]
WantedBy=multi-user.target
```

Start services:

```bash
sudo systemctl daemon-reload
sudo systemctl enable lost-found-backend lost-found-frontend
sudo systemctl start lost-found-backend lost-found-frontend
```

## Security Considerations

### 1. Environment Security
- Use strong, random SECRET_KEY
- Set DEBUG=False in production
- Use HTTPS with valid SSL certificates
- Configure proper CORS origins

### 2. Database Security
- Use MongoDB Atlas with authentication
- Enable IP whitelisting
- Use strong database passwords
- Enable encryption at rest

### 3. Server Security
- Configure firewall rules
- Use fail2ban for intrusion prevention
- Keep system packages updated
- Use non-root user for application

## Monitoring and Logging

### Application Logs
- Backend logs: `backend.log`
- Frontend logs: `frontend.log`
- Startup logs: `startup.log`

### System Monitoring
```bash
# Monitor application status
pm2 status
# or
systemctl status lost-found-backend lost-found-frontend

# Monitor logs
tail -f backend.log frontend.log

# Monitor system resources
htop
iostat
```

## Troubleshooting

### Common Issues

1. **Port already in use**
   ```bash
   # Find process using port
   sudo lsof -i :8080
   # Kill process
   sudo kill -9 <PID>
   ```

2. **Python dependencies not found**
   ```bash
   cd backend
   source venv/bin/activate
   pip install -r requirement.txt
   ```

3. **Node.js dependencies not found**
   ```bash
   cd frontend
   npm install
   ```

4. **Database connection failed**
   - Check MongoDB URI in `.env` file
   - Verify MongoDB service is running
   - Check network connectivity

5. **Permission denied errors**
   ```bash
   # Fix file permissions
   chmod +x start-app.sh stop-app.sh setup-environment.sh
   ```

### Getting Help

1. Check logs for error messages
2. Verify all dependencies are installed
3. Ensure environment variables are correctly set
4. Check network connectivity and firewall settings

## Automation Scripts

### Automated Deployment Script

```bash
#!/bin/bash
# deploy.sh

# Pull latest changes
git pull origin main

# Install/update dependencies
./setup-environment.sh

# Restart application
./stop-app.sh
sleep 5
./start-app.sh

echo "Deployment completed!"
```

### Backup Script

```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/path/to/backups"

# Backup database
mongodump --uri="mongodb://localhost:27017/lost_found_db" --out="$BACKUP_DIR/db_$DATE"

# Backup application files
tar -czf "$BACKUP_DIR/app_$DATE.tar.gz" /path/to/EIE3117_project

echo "Backup completed: $DATE"
```

This comprehensive deployment guide should help you deploy the application on any hosting environment with minimal issues.

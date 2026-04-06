#!/bin/bash

# Lost and Found Application Startup Script - Enhanced Version
# Features: Adaptive IP detection, port conflict resolution, health checks, logging

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DEFAULT_BACKEND_PORT=8080
DEFAULT_FRONTEND_PORT=8081
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
LOG_FILE="$PROJECT_ROOT/startup.log"
MAX_PORT_ATTEMPTS=10
HEALTH_CHECK_TIMEOUT=30
STARTUP_TIMEOUT=60

# Logging function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}ERROR: $1${NC}" | tee -a "$LOG_FILE"
    exit 1
}

success() {
    echo -e "${GREEN}✅ $1${NC}" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}" | tee -a "$LOG_FILE"
}

info() {
    echo -e "${BLUE}ℹ️  $1${NC}" | tee -a "$LOG_FILE"
}

# Function to detect the primary IP address
detect_ip() {
    local ip
    # Try multiple methods to get the IP
    ip=$(ip route get 1.1.1.1 2>/dev/null | awk '{print $7}' | head -1) ||
    ip=$(hostname -I | awk '{print $1}') ||
    ip=$(ifconfig | grep -E "inet.*broadcast" | awk '{print $2}' | head -1) ||
    ip="localhost"
    
    echo "$ip"
}

# Function to check if port is available
is_port_available() {
    local port=$1
    if lsof -i :"$port" >/dev/null 2>&1; then
        return 1
    else
        return 0
    fi
}

# Function to find available port
find_available_port() {
    local base_port=$1
    local port=$base_port
    
    for ((i=0; i<MAX_PORT_ATTEMPTS; i++)); do
        if is_port_available "$port"; then
            echo "$port"
            return 0
        fi
        port=$((port + 1))
        warning "Port $((port - 1)) is in use, trying port $port..." >&2
    done
    
    error "Could not find an available port starting from $base_port after $MAX_PORT_ATTEMPTS attempts"
}

# Function to kill existing processes gracefully
kill_existing_processes() {
    info "Stopping existing processes..."
    
    # Kill backend processes
    local backend_pids=$(pgrep -f "python.*manage.py.*runserver" 2>/dev/null || true)
    if [[ -n "$backend_pids" ]]; then
        info "Terminating backend processes: $backend_pids"
        echo "$backend_pids" | xargs kill -TERM 2>/dev/null || true
        sleep 2
        # Force kill if still running
        echo "$backend_pids" | xargs kill -KILL 2>/dev/null || true
    fi
    
    # Kill frontend processes
    local frontend_pids=$(pgrep -f "npm.*serve\|vue-cli-service.*serve" 2>/dev/null || true)
    if [[ -n "$frontend_pids" ]]; then
        info "Terminating frontend processes: $frontend_pids"
        echo "$frontend_pids" | xargs kill -TERM 2>/dev/null || true
        sleep 2
        # Force kill if still running
        echo "$frontend_pids" | xargs kill -KILL 2>/dev/null || true
    fi
    
    sleep 2
}

# Function to detect operating system
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    elif [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
        echo "windows"
    else
        echo "unknown"
    fi
}

# Function to detect Linux distribution
detect_linux_distro() {
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        echo "$ID"
    elif command -v lsb_release &> /dev/null; then
        lsb_release -si | tr '[:upper:]' '[:lower:]'
    else
        echo "unknown"
    fi
}

# Function to install system dependencies
install_system_deps() {
    local os=$(detect_os)
    local distro=""
    
    if [[ "$os" == "linux" ]]; then
        distro=$(detect_linux_distro)
    fi
    
    info "Detected OS: $os${distro:+ ($distro)}"
    
    case "$os" in
        "linux")
            case "$distro" in
                "ubuntu"|"debian")
                    info "Installing system dependencies for Ubuntu/Debian..."
                    sudo apt-get update -qq || warning "Failed to update package list"
                    sudo apt-get install -y python3 python3-pip python3-venv nodejs npm curl lsof || warning "Some system packages failed to install"
                    ;;
                "centos"|"rhel"|"fedora")
                    info "Installing system dependencies for CentOS/RHEL/Fedora..."
                    if command -v dnf &> /dev/null; then
                        sudo dnf install -y python3 python3-pip nodejs npm curl lsof || warning "Some system packages failed to install"
                    elif command -v yum &> /dev/null; then
                        sudo yum install -y python3 python3-pip nodejs npm curl lsof || warning "Some system packages failed to install"
                    fi
                    ;;
                "arch")
                    info "Installing system dependencies for Arch Linux..."
                    sudo pacman -S --noconfirm python python-pip nodejs npm curl lsof || warning "Some system packages failed to install"
                    ;;
                *)
                    warning "Unsupported Linux distribution: $distro"
                    info "Please manually install: python3, python3-pip, python3-venv, nodejs, npm, curl, lsof"
                    ;;
            esac
            ;;
        "macos")
            info "Checking system dependencies for macOS..."
            if ! command -v brew &> /dev/null; then
                warning "Homebrew not found. Installing Homebrew..."
                /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" || warning "Failed to install Homebrew"
            fi
            
            if command -v brew &> /dev/null; then
                brew update || warning "Failed to update Homebrew"
                brew install python@3 node curl || warning "Some packages failed to install"
            fi
            ;;
        "windows")
            warning "Windows detected. Please ensure:"
            info "1. Python 3 is installed from https://python.org"
            info "2. Node.js is installed from https://nodejs.org"
            info "3. Git Bash or WSL is being used to run this script"
            ;;
        *)
            warning "Unsupported operating system: $os"
            info "Please manually install: Python 3, Node.js, npm, curl"
            ;;
    esac
}

# Function to check and install Python
ensure_python() {
    if ! command -v python3 &> /dev/null; then
        warning "Python 3 not found. Attempting to install..."
        install_system_deps
        
        if ! command -v python3 &> /dev/null; then
            error "Python 3 installation failed. Please install manually."
        fi
    fi
    
    local python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
    success "Python 3 found: $python_version"
}

# Function to check and install Node.js
ensure_nodejs() {
    if ! command -v node &> /dev/null; then
        warning "Node.js not found. Attempting to install..."
        install_system_deps
        
        if ! command -v node &> /dev/null; then
            # Try installing Node.js via Node Version Manager (NVM)
            info "Trying to install Node.js via NVM..."
            curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
            export NVM_DIR="$HOME/.nvm"
            [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
            [ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"
            
            if command -v nvm &> /dev/null; then
                nvm install node
                nvm use node
            else
                error "Node.js installation failed. Please install manually from https://nodejs.org"
            fi
        fi
    fi
    
    local node_version=$(node --version 2>&1)
    success "Node.js found: $node_version"
}

# Function to ensure pip is available
ensure_pip() {
    if ! python3 -m pip --version &> /dev/null; then
        warning "pip not found. Installing..."
        python3 -m ensurepip --default-pip || {
            # Fallback for older systems
            curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
            python3 get-pip.py
            rm get-pip.py
        }
    fi
    
    local pip_version=$(python3 -m pip --version 2>&1)
    success "pip found: $pip_version"
}

# Function to check and install npm
ensure_npm() {
    if ! command -v npm &> /dev/null; then
        warning "npm not found. This should have been installed with Node.js."
        install_system_deps
        
        if ! command -v npm &> /dev/null; then
            error "npm installation failed. Please install manually."
        fi
    fi
    
    local npm_version=$(npm --version 2>&1)
    success "npm found: $npm_version"
}

# Function to check dependencies
check_dependencies() {
    info "Checking and installing dependencies..."
    
    # Ensure basic tools are available
    ensure_python
    ensure_pip
    ensure_nodejs
    ensure_npm
    
    # Check virtual environment
    if [[ ! -d "$BACKEND_DIR/venv" ]]; then
        warning "Virtual environment not found. Creating one..."
        cd "$BACKEND_DIR"
        python3 -m venv venv || error "Failed to create virtual environment"
    fi
    
    # Check if requirements are installed
    source "$BACKEND_DIR/venv/bin/activate"
    if python3 -c "import django" 2>/dev/null; then
        info "Python dependencies are already installed"
    else
        warning "Installing Python dependencies..."
        if [[ -f "$BACKEND_DIR/requirement.txt" ]]; then
            pip install -r requirement.txt || error "Failed to install Python dependencies"
        elif [[ -f "$BACKEND_DIR/requirements.txt" ]]; then
            pip install -r requirements.txt || error "Failed to install Python dependencies"
        else
            error "No requirements file found"
        fi
    fi
    
    # Check node_modules
    if [[ ! -d "$FRONTEND_DIR/node_modules" ]]; then
        warning "Installing Node.js dependencies..."
        cd "$FRONTEND_DIR"
        npm install || error "Failed to install Node.js dependencies"
    fi
    
    success "All dependencies are available"
}

# Function to perform health check
health_check() {
    local url=$1
    local timeout=$2
    local service_name=$3
    
    info "Performing health check for $service_name..."
    
    local start_time=$(date +%s)
    local end_time=$((start_time + timeout))
    
    while [[ $(date +%s) -lt $end_time ]]; do
        if curl -s -f -o /dev/null "$url" 2>/dev/null; then
            success "$service_name is healthy"
            return 0
        fi
        sleep 2
    done
    
    error "$service_name health check failed after ${timeout}s"
}

# Function to start backend
start_backend() {
    local backend_port=$1
    info "Starting backend on port $backend_port..."
    
    cd "$BACKEND_DIR"
    source venv/bin/activate
    
    # Check database connection
    info "Checking database connection..."
    if ! python3 manage.py check --deploy 2>/dev/null; then
        warning "Database check failed, but continuing..."
    fi
    
    # Start backend
    python3 manage.py runserver 0.0.0.0:"$backend_port" > "$PROJECT_ROOT/backend.log" 2>&1 &
    BACKEND_PID=$!
    echo "$BACKEND_PID" > "$PROJECT_ROOT/backend.pid"
    
    info "Backend PID: $BACKEND_PID"
    
    # Wait for backend to start
    sleep 5
    
    # Health check
    health_check "http://localhost:$backend_port/notices/" "$HEALTH_CHECK_TIMEOUT" "Backend"
}

# Function to configure frontend for client access
configure_frontend() {
    local backend_port=$1
    local frontend_port=$2
    
    info "Configuring frontend for client access..."
    
    # Create/update frontend .env file with correct backend URL
    local frontend_env="$FRONTEND_DIR/.env"
    local backend_url="http://$PRIMARY_IP:$backend_port"
    
    info "Setting backend URL to: $backend_url"
    
    cat > "$frontend_env" << EOF
VUE_APP_API_BASE_URL=/
VUE_APP_BACKEND_URL=$backend_url
EOF
    
    success "Frontend configured for client access"
}

# Function to start frontend
start_frontend() {
    local frontend_port=$1
    info "Starting frontend on port $frontend_port..."
    
    cd "$FRONTEND_DIR"
    
    # Clear cache
    rm -rf node_modules/.cache 2>/dev/null || true
    
    # Start frontend
    npm run serve > "$PROJECT_ROOT/frontend.log" 2>&1 &
    FRONTEND_PID=$!
    echo "$FRONTEND_PID" > "$PROJECT_ROOT/frontend.pid"
    
    info "Frontend PID: $FRONTEND_PID"
    
    # Wait for frontend to start
    sleep 8
    
    # Health check
    health_check "http://localhost:$frontend_port/" "$HEALTH_CHECK_TIMEOUT" "Frontend"
}

# Function to test communication
test_communication() {
    local backend_port=$1
    local frontend_port=$2
    info "Testing frontend-backend communication..."
    
    if curl -s -f -o /dev/null "http://localhost:$frontend_port/notices/" 2>/dev/null; then
        success "Frontend-backend communication is working"
    else
        error "Frontend-backend communication failed"
    fi
}

# Function to cleanup on exit
cleanup() {
    info "Cleaning up..."
    if [[ -f "$PROJECT_ROOT/backend.pid" ]]; then
        local pid=$(cat "$PROJECT_ROOT/backend.pid")
        if kill -0 "$pid" 2>/dev/null; then
            kill -TERM "$pid" 2>/dev/null || true
        fi
        rm -f "$PROJECT_ROOT/backend.pid"
    fi
    
    if [[ -f "$PROJECT_ROOT/frontend.pid" ]]; then
        local pid=$(cat "$PROJECT_ROOT/frontend.pid")
        if kill -0 "$pid" 2>/dev/null; then
            kill -TERM "$pid" 2>/dev/null || true
        fi
        rm -f "$PROJECT_ROOT/frontend.pid"
    fi
}

# Set up signal handlers
trap cleanup EXIT INT TERM

# Main execution
main() {
    log "=== Starting Lost and Found Application (Enhanced) ==="
    
    # Detect IP address
    PRIMARY_IP=$(detect_ip)
    info "Detected primary IP: $PRIMARY_IP"
    
    # Kill existing processes
    kill_existing_processes
    
    # Check dependencies
    check_dependencies
    
    # Find available ports
    BACKEND_PORT=$(find_available_port "$DEFAULT_BACKEND_PORT")
    FRONTEND_PORT=$(find_available_port "$DEFAULT_FRONTEND_PORT")
    
    if [[ "$BACKEND_PORT" != "$DEFAULT_BACKEND_PORT" ]]; then
        warning "Using alternative backend port: $BACKEND_PORT"
    fi
    
    if [[ "$FRONTEND_PORT" != "$DEFAULT_FRONTEND_PORT" ]]; then
        warning "Using alternative frontend port: $FRONTEND_PORT"
    fi
    
    # Start services
    start_backend "$BACKEND_PORT"
    configure_frontend "$BACKEND_PORT" "$FRONTEND_PORT"
    start_frontend "$FRONTEND_PORT"
    
    # Test communication
    test_communication "$BACKEND_PORT" "$FRONTEND_PORT"
    
    # Display success message
    echo
    success "=== Application Started Successfully ==="
    info "Primary IP: $PRIMARY_IP"
    info "Backend URL: http://$PRIMARY_IP:$BACKEND_PORT"
    info "Frontend URL: http://$PRIMARY_IP:$FRONTEND_PORT"
    info "Local Backend: http://localhost:$BACKEND_PORT"
    info "Local Frontend: http://localhost:$FRONTEND_PORT"
    info "Logs: Backend: $PROJECT_ROOT/backend.log, Frontend: $PROJECT_ROOT/frontend.log"
    info "Startup Log: $LOG_FILE"
    echo
    
    # Client access information
    info "=== Client Access Information ==="
    info "For other devices on the same network:"
    info "  • Frontend: http://$PRIMARY_IP:$FRONTEND_PORT"
    info "  • Backend API: http://$PRIMARY_IP:$BACKEND_PORT"
    info "  • Ensure devices can reach this IP address"
    info "  • Check firewall settings if needed"
    echo
    
    # Display stop commands
    info "To stop the application:"
    echo "  • Stop script: Press Ctrl+C or run: kill $BACKEND_PID $FRONTEND_PID"
    echo "  • Clean stop: ./stop-app.sh (if available)"
    echo "  • Force stop: pkill -f 'python.*manage.py.*runserver' && pkill -f 'npm.*serve'"
    echo
    
    # Keep script running
    info "Application is running. Press Ctrl+C to stop."
    info "Monitoring logs (Ctrl+C to stop monitoring)..."
    
    # Monitor logs
    tail -f "$PROJECT_ROOT/backend.log" "$PROJECT_ROOT/frontend.log" 2>/dev/null || true
}

# Run main function
main "$@"

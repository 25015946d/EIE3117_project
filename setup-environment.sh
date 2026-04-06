#!/bin/bash

# Environment Setup Script for Lost and Found Application
# This script prepares a new environment for the application

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

# Logging function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1"
}

error() {
    echo -e "${RED}ERROR: $1${NC}"
    exit 1
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
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
install_system_dependencies() {
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
                    sudo apt-get install -y python3 python3-pip python3-venv nodejs npm git curl wget build-essential || warning "Some system packages failed to install"
                    ;;
                "centos"|"rhel"|"fedora")
                    info "Installing system dependencies for CentOS/RHEL/Fedora..."
                    if command -v dnf &> /dev/null; then
                        sudo dnf install -y python3 python3-pip nodejs npm git curl wget gcc || warning "Some system packages failed to install"
                    elif command -v yum &> /dev/null; then
                        sudo yum install -y python3 python3-pip nodejs npm git curl wget gcc || warning "Some system packages failed to install"
                    fi
                    ;;
                "arch")
                    info "Installing system dependencies for Arch Linux..."
                    sudo pacman -S --noconfirm python python-pip nodejs npm git curl wget base-devel || warning "Some system packages failed to install"
                    ;;
                *)
                    warning "Unsupported Linux distribution: $distro"
                    info "Please manually install: python3, python3-pip, python3-venv, nodejs, npm, git, curl, wget, build-essential"
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
                brew install python@3 node git curl wget || warning "Some packages failed to install"
            fi
            ;;
        "windows")
            warning "Windows detected. Please ensure:"
            info "1. Python 3 is installed from https://python.org"
            info "2. Node.js is installed from https://nodejs.org"
            info "3. Git is installed from https://git-scm.com"
            info "4. Git Bash or WSL is being used to run this script"
            ;;
        *)
            warning "Unsupported operating system: $os"
            info "Please manually install: Python 3, Node.js, npm, Git, curl, wget"
            ;;
    esac
}

# Function to setup Python environment
setup_python_env() {
    info "Setting up Python environment..."
    
    cd "$BACKEND_DIR"
    
    # Create virtual environment if it doesn't exist
    if [[ ! -d "venv" ]]; then
        info "Creating Python virtual environment..."
        python3 -m venv venv || error "Failed to create virtual environment"
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    info "Upgrading pip..."
    pip install --upgrade pip || warning "Failed to upgrade pip"
    
    # Install Python dependencies
    info "Installing Python dependencies..."
    if [[ -f "requirement.txt" ]]; then
        pip install -r requirement.txt || error "Failed to install Python dependencies"
    elif [[ -f "requirements.txt" ]]; then
        pip install -r requirements.txt || error "Failed to install Python dependencies"
    else
        error "No requirements file found in backend directory"
    fi
    
    success "Python environment setup completed"
}

# Function to setup Node.js environment
setup_nodejs_env() {
    info "Setting up Node.js environment..."
    
    cd "$FRONTEND_DIR"
    
    # Install Node.js dependencies
    info "Installing Node.js dependencies..."
    npm install || error "Failed to install Node.js dependencies"
    
    success "Node.js environment setup completed"
}

# Function to setup environment files
setup_env_files() {
    info "Setting up environment files..."
    
    # Backend environment file
    if [[ ! -f "$BACKEND_DIR/.env" ]] && [[ -f "$BACKEND_DIR/.env.example" ]]; then
        info "Creating backend .env file from example..."
        cp "$BACKEND_DIR/.env.example" "$BACKEND_DIR/.env"
        warning "Please update $BACKEND_DIR/.env with your actual configuration"
    fi
    
    # Frontend environment file
    if [[ ! -f "$FRONTEND_DIR/.env" ]] && [[ -f "$FRONTEND_DIR/.env.example" ]]; then
        info "Creating frontend .env file from example..."
        cp "$FRONTEND_DIR/.env.example" "$FRONTEND_DIR/.env"
        warning "Please update $FRONTEND_DIR/.env with your actual configuration"
    fi
    
    success "Environment files setup completed"
}

# Function to run database migrations
setup_database() {
    info "Setting up database..."
    
    cd "$BACKEND_DIR"
    source venv/bin/activate
    
    # Run migrations
    info "Running database migrations..."
    python3 manage.py migrate || warning "Database migrations failed or already applied"
    
    # Create superuser (optional)
    info "You can create a superuser with: cd $BACKEND_DIR && source venv/bin/activate && python3 manage.py createsuperuser"
    
    success "Database setup completed"
}

# Function to verify installation
verify_installation() {
    info "Verifying installation..."
    
    # Check Python
    if command -v python3 &> /dev/null; then
        local python_version=$(python3 --version 2>&1)
        success "Python: $python_version"
    else
        error "Python 3 not found"
    fi
    
    # Check Node.js
    if command -v node &> /dev/null; then
        local node_version=$(node --version 2>&1)
        success "Node.js: $node_version"
    else
        error "Node.js not found"
    fi
    
    # Check npm
    if command -v npm &> /dev/null; then
        local npm_version=$(npm --version 2>&1)
        success "npm: $npm_version"
    else
        error "npm not found"
    fi
    
    # Check virtual environment
    if [[ -d "$BACKEND_DIR/venv" ]]; then
        success "Python virtual environment exists"
    else
        error "Python virtual environment not found"
    fi
    
    # Check node_modules
    if [[ -d "$FRONTEND_DIR/node_modules" ]]; then
        success "Node.js dependencies installed"
    else
        error "Node.js dependencies not found"
    fi
    
    # Test Django import
    cd "$BACKEND_DIR"
    source venv/bin/activate
    if python3 -c "import django" 2>/dev/null; then
        local django_version=$(python3 -c "import django; print(django.get_version())" 2>/dev/null)
        success "Django: $django_version"
    else
        error "Django not installed"
    fi
    
    success "Installation verification completed"
}

# Main execution
main() {
    log "=== Environment Setup for Lost and Found Application ==="
    
    info "This script will set up the complete development environment"
    info "including system dependencies, Python virtual environment, and Node.js dependencies"
    echo
    
    read -p "Do you want to continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        info "Setup cancelled"
        exit 0
    fi
    
    # Install system dependencies
    install_system_dependencies
    
    # Setup Python environment
    setup_python_env
    
    # Setup Node.js environment
    setup_nodejs_env
    
    # Setup environment files
    setup_env_files
    
    # Setup database
    setup_database
    
    # Verify installation
    verify_installation
    
    echo
    success "=== Environment Setup Completed Successfully ==="
    info "You can now start the application with: ./start-app.sh"
    info "Or stop it with: ./stop-app.sh"
    echo
    
    info "Next steps:"
    echo "1. Update environment files with your configuration"
    echo "2. Run: ./start-app.sh"
    echo "3. Open your browser to the displayed URLs"
}

# Run main function
main "$@"

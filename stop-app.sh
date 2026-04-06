#!/bin/bash

# Lost and Found Application Stop Script
# Cleanly stops all application processes

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

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

# Function to stop processes using PID files
stop_using_pid_files() {
    local stopped=false
    
    # Stop backend
    if [[ -f "$PROJECT_ROOT/backend.pid" ]]; then
        local backend_pid=$(cat "$PROJECT_ROOT/backend.pid")
        if kill -0 "$backend_pid" 2>/dev/null; then
            info "Stopping backend (PID: $backend_pid)..."
            kill -TERM "$backend_pid" 2>/dev/null || true
            
            # Wait for graceful shutdown
            local count=0
            while kill -0 "$backend_pid" 2>/dev/null && [[ $count -lt 10 ]]; do
                sleep 1
                count=$((count + 1))
            done
            
            # Force kill if still running
            if kill -0 "$backend_pid" 2>/dev/null; then
                warning "Backend did not stop gracefully, force killing..."
                kill -KILL "$backend_pid" 2>/dev/null || true
            fi
            
            success "Backend stopped"
            stopped=true
        else
            warning "Backend PID file exists but process is not running"
        fi
        rm -f "$PROJECT_ROOT/backend.pid"
    fi
    
    # Stop frontend
    if [[ -f "$PROJECT_ROOT/frontend.pid" ]]; then
        local frontend_pid=$(cat "$PROJECT_ROOT/frontend.pid")
        if kill -0 "$frontend_pid" 2>/dev/null; then
            info "Stopping frontend (PID: $frontend_pid)..."
            kill -TERM "$frontend_pid" 2>/dev/null || true
            
            # Wait for graceful shutdown
            local count=0
            while kill -0 "$frontend_pid" 2>/dev/null && [[ $count -lt 10 ]]; do
                sleep 1
                count=$((count + 1))
            done
            
            # Force kill if still running
            if kill -0 "$frontend_pid" 2>/dev/null; then
                warning "Frontend did not stop gracefully, force killing..."
                kill -KILL "$frontend_pid" 2>/dev/null || true
            fi
            
            success "Frontend stopped"
            stopped=true
        else
            warning "Frontend PID file exists but process is not running"
        fi
        rm -f "$PROJECT_ROOT/frontend.pid"
    fi
    
    if $stopped; then
        return 0
    else
        return 1
    fi
}

# Function to stop processes by pattern matching
stop_by_pattern() {
    local stopped=false
    
    # Stop backend processes
    local backend_pids=$(pgrep -f "python.*manage.py.*runserver" 2>/dev/null || true)
    if [[ -n "$backend_pids" ]]; then
        info "Stopping backend processes: $backend_pids"
        echo "$backend_pids" | xargs kill -TERM 2>/dev/null || true
        sleep 2
        echo "$backend_pids" | xargs kill -KILL 2>/dev/null || true
        success "Backend processes stopped"
        stopped=true
    fi
    
    # Stop frontend processes
    local frontend_pids=$(pgrep -f "npm.*serve\|vue-cli-service.*serve" 2>/dev/null || true)
    if [[ -n "$frontend_pids" ]]; then
        info "Stopping frontend processes: $frontend_pids"
        echo "$frontend_pids" | xargs kill -TERM 2>/dev/null || true
        sleep 2
        echo "$frontend_pids" | xargs kill -KILL 2>/dev/null || true
        success "Frontend processes stopped"
        stopped=true
    fi
    
    if $stopped; then
        return 0
    else
        return 1
    fi
}

# Function to clean up resources
cleanup() {
    info "Cleaning up resources..."
    
    # Remove PID files
    rm -f "$PROJECT_ROOT/backend.pid" "$PROJECT_ROOT/frontend.pid"
    
    # Clean up log files if requested
    if [[ "${1:-}" == "--clean-logs" ]]; then
        info "Cleaning up log files..."
        rm -f "$PROJECT_ROOT/backend.log" "$PROJECT_ROOT/frontend.log" "$PROJECT_ROOT/startup.log"
        success "Log files cleaned up"
    fi
    
    success "Cleanup completed"
}

# Main execution
main() {
    log "=== Stopping Lost and Found Application ==="
    
    local stopped=false
    
    # Try to stop using PID files first
    if stop_using_pid_files; then
        stopped=true
    fi
    
    # Fallback to pattern matching
    if ! $stopped; then
        if stop_by_pattern; then
            stopped=true
        fi
    fi
    
    if ! $stopped; then
        warning "No running application processes found"
    fi
    
    # Clean up
    cleanup "${1:-}"
    
    success "=== Application Stopped Successfully ==="
    
    if ! $stopped; then
        info "No processes were stopped (none were running)"
    fi
}

# Run main function
main "$@"

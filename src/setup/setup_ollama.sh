#!/usr/bin/env bash
set -e

# ============================================================================
# Ollama Setup Script for SkillCorner AI Analyst
# ============================================================================
# This script will:
# 1. Detect your operating system
# 2. Install Ollama if not present
# 3. Start the Ollama service
# 4. Pull the required Llama 3.1 model
# ============================================================================

# Configuration
MODEL_NAME="llama3.1:latest"
LOG_FILE="ollama_setup.log"
OLLAMA_URL="http://127.0.0.1:11434"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_header() {
    echo ""
    echo -e "${GREEN}================================${NC}"
    echo -e "${GREEN}$1${NC}"
    echo -e "${GREEN}================================${NC}"
    echo ""
}

# Detect OS
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
        print_info "Detected OS: Linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
        print_info "Detected OS: macOS"
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        OS="windows"
        print_info "Detected OS: Windows (WSL/Cygwin)"
    else
        print_error "Unsupported OS: $OSTYPE"
        exit 1
    fi
}

# Check if Ollama is installed
check_installed() {
    print_header "Step 1: Checking Ollama Installation"
    
    if command -v ollama >/dev/null 2>&1; then
        OLLAMA_VERSION=$(ollama --version 2>/dev/null || echo "unknown")
        print_success "Ollama is already installed (${OLLAMA_VERSION})"
        return 0
    else
        print_warning "Ollama is not installed"
        return 1
    fi
}

# Install Ollama
install_ollama() {
    print_header "Step 2: Installing Ollama"
    
    if [[ "$OS" == "linux" ]]; then
        print_info "Installing Ollama for Linux..."
        curl -fsSL https://ollama.com/install.sh | sh
        
    elif [[ "$OS" == "macos" ]]; then
        print_info "Installing Ollama for macOS..."
        
        # Check if Homebrew is available
        if command -v brew >/dev/null 2>&1; then
            print_info "Using Homebrew to install Ollama..."
            brew install ollama
        else
            print_info "Downloading Ollama installer..."
            curl -fsSL https://ollama.com/install.sh | sh
        fi
        
    elif [[ "$OS" == "windows" ]]; then
        print_error "For Windows, please download Ollama from: https://ollama.com/download"
        print_info "After installation, run this script again."
        exit 1
    fi
    
    # Verify installation
    if command -v ollama >/dev/null 2>&1; then
        print_success "Ollama installed successfully!"
    else
        print_error "Installation failed. Please install manually from https://ollama.com"
        exit 1
    fi
}

# Start Ollama service
start_ollama() {
    print_header "Step 3: Starting Ollama Service"
    
    # Check if already running
    if pgrep -x "ollama" >/dev/null; then
        print_success "Ollama is already running (PID: $(pgrep -x ollama))"
        return 0
    fi
    
    # Try systemd first (Linux)
    if command -v systemctl >/dev/null 2>&1; then
        if systemctl list-units --type=service 2>/dev/null | grep -q "ollama.service"; then
            print_info "Starting Ollama via systemd..."
            sudo systemctl start ollama || {
                print_warning "Systemd start failed, trying manual start..."
                start_ollama_manual
            }
        else
            start_ollama_manual
        fi
    else
        start_ollama_manual
    fi
}

# Manual start for Ollama
start_ollama_manual() {
    print_info "Starting Ollama manually..."
    
    # Create log file
    touch "$LOG_FILE"
    
    # Start in background
    nohup ollama serve >"$LOG_FILE" 2>&1 &
    OLLAMA_PID=$!
    
    print_info "Ollama started with PID: $OLLAMA_PID"
    print_info "Logs available at: $LOG_FILE"
    
    # Give it a moment to start
    sleep 2
}

# Wait for Ollama API to be ready
wait_for_ollama() {
    print_header "Step 4: Waiting for Ollama API"
    
    local max_attempts=15
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        print_info "Attempt $attempt/$max_attempts - Checking API..."
        
        if curl -s --max-time 2 "$OLLAMA_URL/api/tags" >/dev/null 2>&1; then
            print_success "Ollama API is responding!"
            return 0
        fi
        
        sleep 2
        attempt=$((attempt + 1))
    done
    
    print_error "Ollama API did not respond in time."
    print_info "Check logs at: $LOG_FILE"
    print_info "Try manually running: ollama serve"
    exit 1
}

# Pull the model
pull_model() {
    print_header "Step 5: Pulling Model ($MODEL_NAME)"
    
    # Check if model exists
    print_info "Checking if model is already available..."
    if ollama list 2>/dev/null | grep -q "$MODEL_NAME"; then
        print_success "Model '$MODEL_NAME' is already available!"
        
        # Show model info
        print_info "Model details:"
        ollama list | grep "$MODEL_NAME" || true
        return 0
    fi
    
    print_warning "Model '$MODEL_NAME' not found locally"
    print_info "Pulling model (this may take several minutes)..."
    print_info "Download size: ~4.7GB for llama3.1:latest"
    
    # Pull with progress
    if ollama pull "$MODEL_NAME"; then
        print_success "Model '$MODEL_NAME' downloaded successfully!"
    else
        print_error "Failed to pull model '$MODEL_NAME'"
        print_info "You can try manually: ollama pull $MODEL_NAME"
        exit 1
    fi
}

# Verify setup
verify_setup() {
    print_header "Step 6: Verifying Setup"
    
    # Test API
    print_info "Testing Ollama API..."
    if curl -s "$OLLAMA_URL/api/tags" >/dev/null; then
        print_success "API is accessible"
    else
        print_error "API is not accessible"
        return 1
    fi
    
    # Test model
    print_info "Testing model inference..."
    local test_response=$(ollama run "$MODEL_NAME" "Say 'OK' if you can read this" --verbose 2>&1 | head -n 1)
    
    if [ -n "$test_response" ]; then
        print_success "Model is responding correctly"
        print_info "Model response: $test_response"
    else
        print_warning "Model test inconclusive"
    fi
    
    # Show available models
    print_info "Available models:"
    ollama list
}

# Show next steps
show_next_steps() {
    print_header "Setup Complete! 🎉"
    
    cat << EOF
${GREEN}Ollama is now ready to use!${NC}

${BLUE}Model Information:${NC}
  - Model: ${MODEL_NAME}
  - API URL: ${OLLAMA_URL}
  - Service Status: Running

${BLUE}Next Steps:${NC}
  1. Install Python dependencies:
     ${YELLOW}pip install -r requirements.txt${NC}

  2. Start the SkillCorner AI Analyst:
     ${YELLOW}./run_app.sh${NC}
     or
     ${YELLOW}streamlit run app.py${NC}

${BLUE}Useful Commands:${NC}
  - Check service: ${YELLOW}ollama list${NC}
  - Stop service: ${YELLOW}pkill ollama${NC}
  - View logs: ${YELLOW}tail -f $LOG_FILE${NC}
  - Test model: ${YELLOW}ollama run $MODEL_NAME "Hello"${NC}

${BLUE}Troubleshooting:${NC}
  - If the service stops, restart with: ${YELLOW}ollama serve${NC}
  - Check logs at: ${YELLOW}$LOG_FILE${NC}
  - For issues, visit: ${YELLOW}https://github.com/ollama/ollama${NC}

EOF
}

# Cleanup function
cleanup() {
    if [ $? -ne 0 ]; then
        print_error "Setup failed. Check $LOG_FILE for details."
    fi
}

trap cleanup EXIT

# Main execution
main() {
    clear
    echo -e "${GREEN}"
    cat << "EOF"
   ___  _ _                          ___      _               
  / _ \| | |                        / __| ___| |_ _  _ _ __  
 | (_) | | |__ _ _ __  __ _  _____ \__ \/ -_)  _| || | '_ \ 
  \___/|_|_|\_\ '_/ _` (_-< |_____|___/\___|\__|\_,_| .__/ 
            |_| \__,_/__/                           |_|    
                                                             
EOF
    echo -e "${NC}"
    
    print_info "SkillCorner AI Analyst - Ollama Setup"
    print_info "This script will set up Ollama and Llama 3.1"
    echo ""
    
    # Detect OS
    detect_os
    
    # Check and install
    if ! check_installed; then
        read -p "Would you like to install Ollama now? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            install_ollama
        else
            print_info "Installation cancelled. Please install Ollama manually:"
            print_info "Visit: https://ollama.com/download"
            exit 0
        fi
    fi
    
    # Start service
    start_ollama
    
    # Wait for API
    wait_for_ollama
    
    # Pull model
    pull_model
    
    # Verify everything works
    verify_setup
    
    # Show completion message
    show_next_steps
}

# Run main function
main "$@"
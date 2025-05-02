#!/bin/bash

# Production-Grade Bot Launcher
set -e  # Exit on error

# Configuration
VENV_DIR="venv"
REQUIREMENTS_DIR="requirements"
PYTHON_CMD="python3"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

header() {
    echo -e "${GREEN}\n=== $1 ===${NC}"
}

setup_venv() {
    header "Setting Up Virtual Environment"
    [ ! -d "$VENV_DIR" ] && $PYTHON_CMD -m venv "$VENV_DIR"
    source "$VENV_DIR/bin/activate"
    pip install --upgrade pip wheel
}

install_deps() {
    header "Installing Dependencies"
    pip install -r "$REQUIREMENTS_DIR/base.txt"
    pip install -r "$REQUIREMENTS_DIR/bot.txt"
}

load_env() {
    [ -f ".env" ] && source ".env" || {
        echo -e "${YELLOW}⚠ .env file not found${NC}"
    }
}

start_services() {
    header "Starting Services"
    pm2 start ecosystem.config.js
}

# Main Execution
main() {
    setup_venv
    install_deps
    load_env
    start_services
    echo -e "${GREEN}\n✅ Setup Completed Successfully${NC}"
}

main "$@"
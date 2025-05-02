#!/bin/bash

# Sentiment Analysis Bot Launcher
# Version 2.2 - Dependency Management

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check MongoDB
if ! pgrep -x "mongod" >/dev/null; then
    echo -e "${YELLOW}⚠ Starting MongoDB...${NC}"
    if command -v systemctl >/dev/null; then
        sudo systemctl start mongod
    elif command -v brew >/dev/null; then
        brew services start mongodb-community
    else
        echo -e "${RED}✗ Could not start MongoDB${NC}"
        exit 1
    fi
    sleep 3
fi

# Check Redis
if ! redis-cli ping >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠ Starting Redis...${NC}"
    if command -v systemctl >/dev/null; then
        sudo systemctl start redis
    elif command -v brew >/dev/null; then
        brew services start redis
    else
        echo -e "${RED}✗ Could not start Redis${NC}"
        exit 1
    fi
    sleep 2
fi

# Setup Virtual Environment
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠ Creating virtual environment...${NC}"
    python3 -m venv venv || {
        echo -e "${RED}✗ Failed to create venv${NC}"
        exit 1
    }
fi

echo -e "${YELLOW}⚠ Activating virtual environment...${NC}"
source venv/bin/activate || {
    echo -e "${RED}✗ Failed to activate venv${NC}"
    exit 1
}

# Install Dependencies
echo -e "${YELLOW}⚠ Installing dependencies...${NC}"
pip install --upgrade pip
pip install -r requirements.txt
pip install python-telegram-bot[job-queue]
pip install huggingface_hub[hf_xet]
pip install --upgrade transformers torch
# Add this before starting services
echo -e "${YELLOW}⚠ Checking Telegram API connectivity...${NC}"
if ! curl -s --connect-timeout 10 https://api.telegram.org >/dev/null; then
    echo -e "${RED}✗ Cannot connect to Telegram API${NC}"
    echo -e "${YELLOW}ℹ Try these troubleshooting steps:${NC}"
    echo "1. Check your internet connection"
    echo "2. Verify Telegram isn't blocked in your region"
    echo "3. Try using a VPN if needed"
    exit 1
fi
echo -e "${GREEN}✓ Telegram API is reachable${NC}"

# Start Services
echo -e "${GREEN}✓ Starting services...${NC}"
uvicorn main:app --host 0.0.0.0 --port 8000
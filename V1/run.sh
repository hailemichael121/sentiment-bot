#!/bin/bash

# Enhanced Sentiment Analysis Bot Runner
# Version 1.4 - Comprehensive Network Handling
# Features:
# - DNS troubleshooting
# - IPv4/IPv6 handling
# - Proxy awareness
# - Comprehensive error checking

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print section headers
section() {
    echo -e "${BLUE}=== $1 ===${NC}"
}

# Function to check command availability
check_command() {
    if ! command -v "$1" &> /dev/null; then
        echo -e "${RED}Error: $1 could not be found${NC}"
        echo -e "${YELLOW}Please install $1 first${NC}"
        exit 1
    fi
}

# Function to check DNS resolution
check_dns() {
    echo -e "${YELLOW}Testing DNS resolution...${NC}"
    local success=0
    
    # Try system DNS first
    if nslookup api.telegram.org >/dev/null 2>&1; then
        echo -e "${GREEN}✓ System DNS working${NC}"
        success=1
    else
        echo -e "${YELLOW}⚠ System DNS failed${NC}"
    fi
    
    # Try Google DNS if system DNS failed
    if [ $success -eq 0 ]; then
        if nslookup api.telegram.org 8.8.8.8 >/dev/null 2>&1; then
            echo -e "${GREEN}✓ Google DNS working${NC}"
            echo -e "${YELLOW}Recommendation: Update your system DNS to use 8.8.8.8${NC}"
            success=1
        else
            echo -e "${RED}✗ All DNS tests failed${NC}"
            return 1
        fi
    fi
    
    return 0
}

# Function to test network connectivity
test_network() {
    echo -e "${YELLOW}Testing network connectivity...${NC}"
    
    # Check basic internet access
    if ! ping -c 1 8.8.8.8 &> /dev/null; then
        echo -e "${RED}✗ No network connectivity${NC}"
        return 1
    fi
    echo -e "${GREEN}✓ Basic connectivity OK${NC}"
    
    # Check Telegram API access
    local curl_output
    curl_output=$(curl -sSI https://api.telegram.org 2>&1)
    
    if [[ $curl_output == *"HTTP/2 302"* ]]; then
        echo -e "${GREEN}✓ Telegram API reachable${NC}"
    else
        echo -e "${YELLOW}⚠ Could not verify Telegram API${NC}"
        echo -e "${YELLOW}Curl output:\n$curl_output${NC}"
        return 1
    fi
    
    return 0
}

# Function to test Python connectivity
test_python_connectivity() {
    echo -e "${YELLOW}Testing Python connectivity to Telegram API...${NC}"
    
    python3 -c "
import socket
import requests
from urllib3.util.connection import allowed_gai_family

# Force IPv4 for testing
def _create_connection(address, *args, **kwargs):
    family = allowed_gai_family()
    try:
        host, port = address
        return socket.create_connection(
            (host, port), 
            timeout=5, 
            family=socket.AF_INET
        )
    except Exception as e:
        print(f'\033[91m✗ Connection failed: {e}\033[0m')
        raise

# Test both IPv4 and IPv6
for family in (socket.AF_INET, socket.AF_INET6):
    try:
        socket.create_connection = lambda *args, **kwargs: _create_connection(*args, **kwargs)
        response = requests.get('https://api.telegram.org', timeout=5)
        print(f'\033[92m✓ Connected via {"IPv4" if family == socket.AF_INET else "IPv6"}\033[0m')
        print(f'Status code: {response.status_code}')
        break
    except Exception as e:
        continue
else:
    print('\033[91m✗ Could not establish connection\033[0m')
    exit(1)
" || return 1

    return 0
}

# Function to setup virtual environment
setup_venv() {
    section "Setting up Python environment"
    
    # Check Python version
    echo -e "${YELLOW}Checking Python version...${NC}"
    if ! python3 -c "import sys; assert sys.version_info >= (3, 8)" 2>/dev/null; then
        echo -e "${RED}Python 3.8 or higher is required${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Python version OK${NC}"
    
    # Create virtual environment
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    if [ ! -d "venv" ]; then
        python3 -m venv venv || {
            echo -e "${RED}Failed to create virtual environment${NC}"
            exit 1
        }
    fi
    
    # Activate virtual environment
    echo -e "${YELLOW}Activating virtual environment...${NC}"
    source venv/bin/activate || {
        echo -e "${RED}Failed to activate virtual environment${NC}"
        exit 1
    }
    
    # Upgrade pip
    echo -e "${YELLOW}Upgrading pip...${NC}"
    pip install --upgrade pip || {
        echo -e "${YELLOW}⚠ Failed to upgrade pip (continuing anyway)${NC}"
    }
}

# In the install_dependencies() function:
install_dependencies() {
    section "Installing dependencies"
    
    # Core requirements
    pip install urllib3 requests || {
        echo -e "${RED}Failed to install core networking packages${NC}"
        exit 1
    }

    # Other requirements
    pip install -r requirements.txt || {
        echo -e "${RED}Failed to install dependencies${NC}"
        exit 1
    }
}

# Function to start the bot
start_bot() {
    section "Starting Bot"
    
    # Add forced IPv4 to bot.py if not present
    if ! grep -q "urllib3.util.connection" bot.py; then
        echo -e "${YELLOW}Adding network optimizations to bot.py...${NC}"
        sed -i '1i import socket\nimport urllib3\nfrom urllib3.util.connection import allowed_gai_family\n\n# Force IPv4 for all connections\ndef _create_connection(address, *args, **kwargs):\n    family = allowed_gai_family()\n    host, port = address\n    return socket.create_connection(\n        (host, port),\n        timeout=5,\n        family=socket.AF_INET\n    )\n\nurllib3.util.connection.create_connection = _create_connection' bot.py
    fi
    
    # Start the bot with retries
    local max_retries=3
    local retry_delay=5
    
    for ((i=1; i<=max_retries; i++)); do
        echo -e "${YELLOW}Starting bot (attempt $i of $max_retries)...${NC}"
        python3 bot.py && break || {
            if [ $i -eq $max_retries ]; then
                echo -e "${RED}Failed to start bot after $max_retries attempts${NC}"
                echo -e "${YELLOW}Possible issues:"
                echo -e "1. Invalid bot token in .env file"
                echo -e "2. Network connectivity problems"
                echo -e "3. Server-side Telegram API issues${NC}"
                exit 1
            fi
            echo -e "${YELLOW}Retrying in $retry_delay seconds...${NC}"
            sleep $retry_delay
        }
    done
}

# Main execution flow
main() {
    section "Sentiment Analysis Bot Setup"
    
    # Check prerequisites
    check_command python3
    check_command pip3
    
    # Network checks
    check_dns
    test_network
    test_python_connectivity
    
    # Environment setup
    setup_venv
    # install_dependencies
    
    # Start the bot
    start_bot
}

# Run main function
main
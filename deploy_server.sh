#!/bin/bash
# Server Deployment Script
# Automated deployment for Ubuntu/Debian VPS

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_USER="budtender"
APP_DIR="/opt/budtender"
DOMAIN="joyyfeedback.com"

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}Budtender Feedback System Deployment${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Please run as root (sudo)${NC}"
    exit 1
fi

# Step 1: System Update
echo -e "${GREEN}Step 1: Updating system...${NC}"
apt update
apt upgrade -y
apt install -y curl git ufw nano htop

# Step 2: Install Docker
echo -e "${GREEN}Step 2: Installing Docker...${NC}"
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com | sh
    echo -e "${GREEN}✓ Docker installed${NC}"
else
    echo -e "${YELLOW}Docker already installed${NC}"
fi

# Step 3: Install Docker Compose
echo -e "${GREEN}Step 3: Installing Docker Compose...${NC}"
if ! docker compose version &> /dev/null; then
    apt install -y docker-compose-plugin
    echo -e "${GREEN}✓ Docker Compose installed${NC}"
else
    echo -e "${YELLOW}Docker Compose already installed${NC}"
fi

# Step 4: Create application user
echo -e "${GREEN}Step 4: Creating application user...${NC}"
if ! id "$APP_USER" &>/dev/null; then
    useradd -m -s /bin/bash $APP_USER
    usermod -aG docker $APP_USER
    echo -e "${GREEN}✓ User $APP_USER created${NC}"
else
    echo -e "${YELLOW}User $APP_USER already exists${NC}"
fi

# Step 5: Create application directory
echo -e "${GREEN}Step 5: Creating application directory...${NC}"
mkdir -p $APP_DIR
chown $APP_USER:$APP_USER $APP_DIR
echo -e "${GREEN}✓ Directory $APP_DIR created${NC}"

# Step 6: Configure firewall
echo -e "${GREEN}Step 6: Configuring firewall...${NC}"
ufw --force enable
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
echo -e "${GREEN}✓ Firewall configured${NC}"
ufw status

# Step 7: Install Nginx
echo -e "${GREEN}Step 7: Installing Nginx...${NC}"
if ! command -v nginx &> /dev/null; then
    apt install -y nginx
    echo -e "${GREEN}✓ Nginx installed${NC}"
else
    echo -e "${YELLOW}Nginx already installed${NC}"
fi

# Step 8: Install Certbot
echo -e "${GREEN}Step 8: Installing Certbot...${NC}"
if ! command -v certbot &> /dev/null; then
    apt install -y certbot python3-certbot-nginx
    echo -e "${GREEN}✓ Certbot installed${NC}"
else
    echo -e "${YELLOW}Certbot already installed${NC}"
fi

echo ""
echo -e "${BLUE}======================================${NC}"
echo -e "${GREEN}✓ Server preparation complete!${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Clone repository to $APP_DIR"
echo "2. Configure .env file"
echo "3. Run: ./deploy_app.sh"
echo ""
echo -e "${YELLOW}Switch to app user:${NC}"
echo "   su - $APP_USER"
echo ""

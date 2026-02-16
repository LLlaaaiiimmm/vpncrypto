#!/bin/bash
# Application Deployment Script
# Run as budtender user in /opt/budtender

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}Application Deployment${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""

# Check if in correct directory
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}Error: docker-compose.yml not found${NC}"
    echo "Please run this script from the application directory"
    exit 1
fi

# Step 1: Check .env file
echo -e "${GREEN}Step 1: Checking .env configuration...${NC}"
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}.env file not found${NC}"
    echo "Would you like to run the setup wizard? (y/n)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        python3 setup_production_env.py
    else
        echo -e "${RED}Please create .env file before continuing${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✓ .env file exists${NC}"
fi

# Step 2: Test environment configuration
echo -e "${GREEN}Step 2: Testing environment configuration...${NC}"
if python3 test_environment.py; then
    echo -e "${GREEN}✓ Environment configuration valid${NC}"
else
    echo -e "${RED}Environment configuration has errors${NC}"
    exit 1
fi

# Step 3: Build and start containers
echo -e "${GREEN}Step 3: Building and starting Docker containers...${NC}"
docker compose up -d --build

# Step 4: Wait for containers to be healthy
echo -e "${GREEN}Step 4: Waiting for containers to be healthy...${NC}"
sleep 10

# Check container status
if docker compose ps | grep -q "healthy"; then
    echo -e "${GREEN}✓ Containers are healthy${NC}"
else
    echo -e "${YELLOW}Waiting for healthcheck...${NC}"
    sleep 20
fi

# Step 5: Check logs
echo -e "${GREEN}Step 5: Checking application logs...${NC}"
docker compose logs --tail=20

# Step 6: Test application
echo -e "${GREEN}Step 6: Testing application...${NC}"
if curl -f http://localhost:8000 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Application is responding${NC}"
else
    echo -e "${RED}Application is not responding${NC}"
    echo "Check logs: docker compose logs"
    exit 1
fi

# Step 7: Setup backups
echo -e "${GREEN}Step 7: Setting up automatic backups...${NC}"
if [ -f "setup_backup_cron.sh" ]; then
    echo "Would you like to setup automatic backups? (y/n)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        ./setup_backup_cron.sh
    fi
fi

echo ""
echo -e "${BLUE}======================================${NC}"
echo -e "${GREEN}✓ Application deployment complete!${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""
echo -e "${YELLOW}Application is running at:${NC}"
echo "   http://localhost:8000"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Configure Nginx (run as root): ./deploy_nginx.sh"
echo "2. Setup SSL: ./deploy_ssl.sh"
echo "3. Change default passwords"
echo ""
echo -e "${YELLOW}Useful commands:${NC}"
echo "   docker compose ps          - Check status"
echo "   docker compose logs -f     - View logs"
echo "   docker compose restart     - Restart"
echo "   docker compose down        - Stop"
echo ""

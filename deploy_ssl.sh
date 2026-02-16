#!/bin/bash
# SSL Certificate Setup Script
# Run as root

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Please run as root (sudo)${NC}"
    exit 1
fi

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}SSL Certificate Setup${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""

# Get domain name
echo -e "${YELLOW}Enter your domain name (e.g., joyyfeedback.com):${NC}"
read -r DOMAIN

if [ -z "$DOMAIN" ]; then
    echo -e "${RED}Domain name is required${NC}"
    exit 1
fi

# Get email
echo -e "${YELLOW}Enter your email for SSL notifications:${NC}"
read -r EMAIL

if [ -z "$EMAIL" ]; then
    echo -e "${RED}Email is required${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}Setting up SSL for: $DOMAIN${NC}"
echo -e "${GREEN}Email: $EMAIL${NC}"
echo ""

# Check if certbot is installed
if ! command -v certbot &> /dev/null; then
    echo -e "${YELLOW}Installing Certbot...${NC}"
    apt install -y certbot python3-certbot-nginx
fi

# Check DNS before proceeding
echo -e "${YELLOW}Checking DNS configuration...${NC}"
if host "$DOMAIN" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ DNS is configured for $DOMAIN${NC}"
else
    echo -e "${RED}DNS is not configured for $DOMAIN${NC}"
    echo "Please configure DNS before continuing:"
    echo "   A    $DOMAIN        → [Your Server IP]"
    echo "   A    www.$DOMAIN    → [Your Server IP]"
    exit 1
fi

# Obtain SSL certificate
echo ""
echo -e "${GREEN}Obtaining SSL certificate...${NC}"
echo -e "${YELLOW}This will:${NC}"
echo "  1. Obtain SSL certificate from Let's Encrypt"
echo "  2. Configure Nginx to use HTTPS"
echo "  3. Redirect HTTP to HTTPS"
echo ""

certbot --nginx \
    -d "$DOMAIN" \
    -d "www.$DOMAIN" \
    --email "$EMAIL" \
    --agree-tos \
    --no-eff-email \
    --redirect

echo ""
echo -e "${GREEN}✓ SSL certificate obtained${NC}"

# Test auto-renewal
echo ""
echo -e "${GREEN}Testing certificate auto-renewal...${NC}"
if certbot renew --dry-run; then
    echo -e "${GREEN}✓ Auto-renewal is configured${NC}"
else
    echo -e "${RED}Auto-renewal test failed${NC}"
    exit 1
fi

# Check certbot timer
echo ""
echo -e "${GREEN}Checking certbot timer...${NC}"
systemctl status certbot.timer --no-pager

echo ""
echo -e "${BLUE}======================================${NC}"
echo -e "${GREEN}✓ SSL setup complete!${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""
echo -e "${YELLOW}Your site is now available at:${NC}"
echo "   https://$DOMAIN"
echo "   https://www.$DOMAIN"
echo ""
echo -e "${GREEN}✓ HTTP automatically redirects to HTTPS${NC}"
echo -e "${GREEN}✓ Certificate will auto-renew${NC}"
echo ""
echo -e "${YELLOW}Test your site:${NC}"
echo "   curl -I https://$DOMAIN"
echo ""
echo -e "${YELLOW}Check SSL rating:${NC}"
echo "   https://www.ssllabs.com/ssltest/analyze.html?d=$DOMAIN"
echo ""

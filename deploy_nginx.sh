#!/bin/bash
# Nginx Configuration Script
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
echo -e "${BLUE}Nginx Configuration${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""

# Get domain name
echo -e "${YELLOW}Enter your domain name (e.g., joyyfeedback.com):${NC}"
read -r DOMAIN

if [ -z "$DOMAIN" ]; then
    echo -e "${RED}Domain name is required${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}Configuring Nginx for: $DOMAIN${NC}"
echo ""

# Create Nginx configuration
NGINX_CONFIG="/etc/nginx/sites-available/$DOMAIN"

cat > "$NGINX_CONFIG" << EOF
server {
    listen 80;
    listen [::]:80;
    server_name $DOMAIN www.$DOMAIN;

    # Максимальный размер загружаемых файлов (6MB для запаса)
    client_max_body_size 6M;

    # Логи
    access_log /var/log/nginx/${DOMAIN}_access.log;
    error_log /var/log/nginx/${DOMAIN}_error.log;

    # Proxy к приложению
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Таймауты
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Статические файлы (кэширование)
    location /static/ {
        proxy_pass http://localhost:8000/static/;
        proxy_cache_valid 200 1d;
        add_header Cache-Control "public, immutable";
    }

    # Загруженные файлы
    location /uploads/ {
        proxy_pass http://localhost:8000/uploads/;
    }
}
EOF

echo -e "${GREEN}✓ Nginx configuration created${NC}"

# Create symbolic link
if [ -f "/etc/nginx/sites-enabled/$DOMAIN" ]; then
    rm "/etc/nginx/sites-enabled/$DOMAIN"
fi
ln -s "$NGINX_CONFIG" "/etc/nginx/sites-enabled/$DOMAIN"
echo -e "${GREEN}✓ Symbolic link created${NC}"

# Remove default site
if [ -f "/etc/nginx/sites-enabled/default" ]; then
    rm "/etc/nginx/sites-enabled/default"
    echo -e "${GREEN}✓ Default site removed${NC}"
fi

# Test Nginx configuration
echo ""
echo -e "${GREEN}Testing Nginx configuration...${NC}"
if nginx -t; then
    echo -e "${GREEN}✓ Nginx configuration is valid${NC}"
else
    echo -e "${RED}Nginx configuration has errors${NC}"
    exit 1
fi

# Restart Nginx
echo ""
echo -e "${GREEN}Restarting Nginx...${NC}"
systemctl restart nginx
systemctl status nginx --no-pager

echo ""
echo -e "${BLUE}======================================${NC}"
echo -e "${GREEN}✓ Nginx configuration complete!${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""
echo -e "${YELLOW}Your site is now available at:${NC}"
echo "   http://$DOMAIN"
echo "   http://www.$DOMAIN"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Make sure DNS is configured:"
echo "   A    $DOMAIN        → [Your Server IP]"
echo "   A    www.$DOMAIN    → [Your Server IP]"
echo ""
echo "2. Setup SSL certificate:"
echo "   ./deploy_ssl.sh"
echo ""
echo -e "${YELLOW}Test your site:${NC}"
echo "   curl -I http://$DOMAIN"
echo ""

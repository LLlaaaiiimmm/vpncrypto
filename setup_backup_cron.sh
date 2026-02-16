#!/bin/bash
# Setup automatic database backups via cron
# Run this script on your production server

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "========================================"
echo "Database Backup Cron Setup"
echo "========================================"
echo ""

# Get the absolute path to the project directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_SCRIPT="$PROJECT_DIR/backup_database.py"
PYTHON_PATH=$(which python3)

echo "Project directory: $PROJECT_DIR"
echo "Backup script: $BACKUP_SCRIPT"
echo "Python path: $PYTHON_PATH"
echo ""

# Check if backup script exists
if [ ! -f "$BACKUP_SCRIPT" ]; then
    echo -e "${RED}Error: backup_database.py not found!${NC}"
    exit 1
fi

# Make backup script executable
chmod +x "$BACKUP_SCRIPT"

# Create log directory
LOG_DIR="$PROJECT_DIR/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/backup.log"

echo -e "${GREEN}✓ Backup script is ready${NC}"
echo ""

# Cron job options
echo "Select backup frequency:"
echo "1) Daily at 2:00 AM"
echo "2) Daily at 3:00 AM"
echo "3) Every 12 hours (2:00 AM and 2:00 PM)"
echo "4) Every 6 hours"
echo "5) Custom (manual entry)"
echo "6) Show current cron jobs and exit"
echo ""

read -p "Enter choice [1-6]: " choice

case $choice in
    1)
        CRON_SCHEDULE="0 2 * * *"
        DESCRIPTION="Daily at 2:00 AM"
        ;;
    2)
        CRON_SCHEDULE="0 3 * * *"
        DESCRIPTION="Daily at 3:00 AM"
        ;;
    3)
        CRON_SCHEDULE="0 2,14 * * *"
        DESCRIPTION="Every 12 hours (2:00 AM and 2:00 PM)"
        ;;
    4)
        CRON_SCHEDULE="0 */6 * * *"
        DESCRIPTION="Every 6 hours"
        ;;
    5)
        echo ""
        echo "Enter cron schedule (e.g., '0 2 * * *' for daily at 2 AM):"
        read -p "Schedule: " CRON_SCHEDULE
        DESCRIPTION="Custom schedule"
        ;;
    6)
        echo ""
        echo "Current cron jobs:"
        crontab -l 2>/dev/null || echo "No cron jobs found"
        exit 0
        ;;
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

# Create cron job command
CRON_COMMAND="cd $PROJECT_DIR && $PYTHON_PATH $BACKUP_SCRIPT >> $LOG_FILE 2>&1"
CRON_JOB="$CRON_SCHEDULE $CRON_COMMAND"

echo ""
echo "Cron job to be added:"
echo "  Schedule: $DESCRIPTION ($CRON_SCHEDULE)"
echo "  Command: $CRON_COMMAND"
echo "  Log file: $LOG_FILE"
echo ""

read -p "Add this cron job? [y/N]: " confirm

if [[ $confirm != [yY] ]]; then
    echo "Cancelled"
    exit 0
fi

# Add cron job
(crontab -l 2>/dev/null | grep -v "$BACKUP_SCRIPT"; echo "$CRON_JOB") | crontab -

echo ""
echo -e "${GREEN}✓ Cron job added successfully!${NC}"
echo ""
echo "Backup schedule: $DESCRIPTION"
echo "Logs will be written to: $LOG_FILE"
echo ""
echo "To view current cron jobs:"
echo "  crontab -l"
echo ""
echo "To remove this cron job:"
echo "  crontab -e"
echo "  (then delete the line containing 'backup_database.py')"
echo ""
echo "To test the backup manually:"
echo "  python3 backup_database.py"
echo ""
echo -e "${YELLOW}Note: Make sure the application is running when backups execute${NC}"
echo ""
echo "========================================"
echo -e "${GREEN}Setup complete!${NC}"
echo "========================================"

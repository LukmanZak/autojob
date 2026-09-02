#!/usr/bin/env bash
# Setup Linux cron - daily 07:00 WIB
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CRON_CMD="0 7 * * * cd $PROJECT_ROOT && python3 main.py --headless >> logs/daily_\$(date +\%Y-\%m-\%d).log 2>&1"
(crontab -l 2>/dev/null | grep -v "main.py --headless"; echo "$CRON_CMD") | crontab -
echo "Cron terpasang: $CRON_CMD"
crontab -l | grep main.py

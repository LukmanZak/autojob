#!/usr/bin/env bash
# Daily job scrape - Linux/Mac cron: 0 7 * * * /path/to/autojob/scripts/run_daily.sh
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"
mkdir -p logs
LOG_DATE=$(date +%Y-%m-%d)
echo "[$(date)] Starting daily scrape" >> "logs/daily_${LOG_DATE}.log"
python3 main.py --headless >> "logs/daily_${LOG_DATE}.log" 2>&1
echo "Done at $(date)" >> "logs/daily_${LOG_DATE}.log"

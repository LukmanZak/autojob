#!/usr/bin/env bash
# Daily quote content agent. Example cron: 0 6 * * * /path/to/project/scripts/run_quote_agent.sh
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"
mkdir -p logs
LOG_DATE="$(date +%F)"
python3 quote_agent.py --visible --send >> "logs/quote_agent_${LOG_DATE}.log" 2>&1

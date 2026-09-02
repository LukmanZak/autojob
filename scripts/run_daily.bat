@echo off
REM Daily job scrape - run via Windows Task Scheduler daily 07:00
cd /d F:\alpha
python main.py --headless >> logs\daily_%date:~10,4%-%date:~4,2%-%date:~7,2%.log 2>&1
echo Done at %time% >> logs\daily_%date:~10,4%-%date:~4,2%-%date:~7,2%.log

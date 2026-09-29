@echo off
REM Daily quote content agent - Windows Task Scheduler daily 06:00
setlocal
cd /d "%~dp0.."
if not exist logs mkdir logs
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set dt=%%I
set LOG_DATE=%dt:~0,4%-%dt:~4,2%-%dt:~6,2%
if "%LOG_DATE%"=="--" set LOG_DATE=%date:~10,4%-%date:~4,2%-%date:~7,2%
echo [%date% %time%] Starting quote agent >> logs\quote_agent_%LOG_DATE%.log
python quote_agent.py --visible --send >> logs\quote_agent_%LOG_DATE%.log 2>&1
set EXIT_CODE=%ERRORLEVEL%
echo [%date% %time%] Finished with code %EXIT_CODE% >> logs\quote_agent_%LOG_DATE%.log
endlocal & exit /b %EXIT_CODE%

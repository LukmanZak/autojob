@echo off
REM Daily job scrape - Windows Task Scheduler daily 07:00
REM Relatif terhadap lokasi script, tidak hardcode F:/alpha
setlocal
cd /d "%~dp0.."
if not exist logs mkdir logs
REM tanggal format YYYY-MM-DD
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set dt=%%I
set LOG_DATE=%dt:~0,4%-%dt:~4,2%-%dt:~6,2%
if "%LOG_DATE%"=="--" set LOG_DATE=%date:~10,4%-%date:~4,2%-%date:~7,2%
echo [%date% %time%] Starting daily scrape >> logs\daily_%LOG_DATE%.log
python main.py --headless >> logs\daily_%LOG_DATE%.log 2>&1
echo Done at %time% >> logs\daily_%LOG_DATE%.log
endlocal

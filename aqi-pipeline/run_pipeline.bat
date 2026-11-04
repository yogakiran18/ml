@echo off
REM ============================================================
REM AQI Pipeline - Daily Batch Runner
REM Schedule this file with Windows Task Scheduler to automate.
REM ============================================================
cd /d "%~dp0"
echo [%date% %time%] Starting AQI Pipeline...
python run_pipeline.py
echo [%date% %time%] Pipeline finished with exit code %ERRORLEVEL%.
pause
